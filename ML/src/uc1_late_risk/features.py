"""
Feature engineering for UC1: Late Payment Risk
"""
import pandas as pd
import numpy as np
from typing import Dict


def load_and_parse_dates(data_files: Dict[str, str]) -> Dict[str, pd.DataFrame]:
    """Load all CSVs and parse date columns (single place to parse dates)."""
    dfs = {}

    # Load data
    dfs["users"] = pd.read_csv(data_files["users"])
    dfs["orders"] = pd.read_csv(data_files["orders"])
    dfs["installments"] = pd.read_csv(data_files["installments"])
    dfs["payments"] = pd.read_csv(data_files["payments"])
    dfs["disputes"] = pd.read_csv(data_files["disputes"])
    dfs["refunds"] = pd.read_csv(data_files["refunds"])
    dfs["merchants"] = pd.read_csv(data_files["merchants"])
    dfs["checkout_events"] = pd.read_csv(data_files["checkout_events"])

    # Parse dates
    if "signup_date" in dfs["users"].columns:
        dfs["users"]["signup_date"] = pd.to_datetime(dfs["users"]["signup_date"], errors="coerce")
    if "order_date" in dfs["orders"].columns:
        dfs["orders"]["order_date"] = pd.to_datetime(dfs["orders"]["order_date"], errors="coerce")

    if "due_date" in dfs["installments"].columns:
        dfs["installments"]["due_date"] = pd.to_datetime(dfs["installments"]["due_date"], errors="coerce")
    if "paid_date" in dfs["installments"].columns:
        dfs["installments"]["paid_date"] = pd.to_datetime(dfs["installments"]["paid_date"], errors="coerce")

    if "payment_date" in dfs["payments"].columns:
        dfs["payments"]["payment_date"] = pd.to_datetime(dfs["payments"]["payment_date"], errors="coerce")
    if "dispute_date" in dfs["disputes"].columns:
        dfs["disputes"]["dispute_date"] = pd.to_datetime(dfs["disputes"]["dispute_date"], errors="coerce")
    if "refund_date" in dfs["refunds"].columns:
        dfs["refunds"]["refund_date"] = pd.to_datetime(dfs["refunds"]["refund_date"], errors="coerce")
    if "event_date" in dfs["checkout_events"].columns:
        dfs["checkout_events"]["event_date"] = pd.to_datetime(dfs["checkout_events"]["event_date"], errors="coerce")
    if "created_at" in dfs["merchants"].columns:
        dfs["merchants"]["created_at"] = pd.to_datetime(dfs["merchants"]["created_at"], errors="coerce")

    return dfs


def build_base_table(installments: pd.DataFrame) -> pd.DataFrame:
    """
    Create base table with anchor date + target.
    NOTE:
      - We keep ONLY labeled rows for training: status in ["paid","late"].
      - Unpaid rows still exist in 'installments' table and will be used for history/exposure features.
    """
    gold = installments.copy()

    # Keep only valid due_date
    gold = gold[gold["due_date"].notna()].copy()

    # Keep only labeled outcomes for supervised training
    gold = gold[gold["status"].astype(str).str.lower().isin(["paid", "late"])].copy()

    # Anchor date = decision time (here: due_date)
    gold["anchor_date"] = gold["due_date"]

    # Compute late_days_final + target
    late_days_calc = (gold["paid_date"] - gold["due_date"]).dt.days
    gold["late_days_final"] = gold["late_days"].fillna(late_days_calc)
    gold["is_late"] = (gold["late_days_final"].fillna(0) > 0).astype(int)

    return gold


def add_user_features(gold: pd.DataFrame, users: pd.DataFrame) -> pd.DataFrame:
    """Add user-level features."""
    gold = gold.merge(
        users[["user_id", "signup_date", "kyc_level", "city", "account_status"]],
        on="user_id", how="left"
    )
    gold.rename(columns={"city": "user_city"}, inplace=True)

    # Account age
    gold["account_age_days"] = (gold["anchor_date"] - gold["signup_date"]).dt.days
    # Prevent invalid negatives (signup after anchor)
    gold.loc[gold["account_age_days"] < 0, "account_age_days"] = np.nan

    # KYC encoding
    kyc_map = {"basic": 1, "full": 2}
    gold["kyc_level_num"] = gold["kyc_level"].astype(str).str.lower().map(kyc_map).fillna(0)

    # Account status encoding
    status_map = {"active": 1, "suspended": -1, "blocked": -2, "closed": -2}
    gold["account_status_num"] = gold["account_status"].astype(str).str.lower().map(status_map).fillna(0)

    # User trust score (grouped feature)
    gold["user_trust_score"] = (
        1.0 * (gold["kyc_level_num"] >= 1).astype(int) +
        0.5 * (gold["kyc_level_num"] >= 2).astype(int) +
        1.0 * (gold["account_status_num"] > 0).astype(int) +
        -1.0 * (gold["account_status_num"] < 0).astype(int)
    )

    # Ensure categorical dtype stability
    if "user_city" in gold.columns:
        gold["user_city"] = gold["user_city"].astype("string")

    return gold


def add_repayment_features(gold: pd.DataFrame, installments: pd.DataFrame) -> pd.DataFrame:
    """
    Add repayment history features (90d lookback), using the FULL installments table
    (including unpaid rows) to compute realistic exposure history.

    UPDATED num_active_plans:
      - counts ALL obligations that are unpaid at anchor time
      - not restricted to due_date < anchor_dt (captures future due dates too)
    """
    inst = installments.copy()
    inst = inst[inst["due_date"].notna()].copy()

    # late_days_final for history (safe: computed from past due_date/paid_date)
    late_days_calc = (inst["paid_date"] - inst["due_date"]).dt.days
    inst["late_days_final"] = inst["late_days"].fillna(late_days_calc)
    inst["late_days_pos"] = inst["late_days_final"].clip(lower=0)

    # Helper aggregation
    def repayment_agg(uid, anchor_dt, days=90):
        lo = anchor_dt - pd.Timedelta(days=days)

        # past behavior window (strictly before anchor_dt)
        hist = inst[
            (inst["user_id"] == uid) &
            (inst["due_date"] < anchor_dt) &
            (inst["due_date"] >= lo)
        ]

        if len(hist) == 0:
            late_rate = np.nan
            ontime_rate = np.nan
            avg_late = np.nan
            max_late = np.nan
        else:
            ld = hist["late_days_pos"].fillna(0)
            late_flag = (ld > 0)

            late_rate = float(late_flag.mean())
            ontime_rate = float((ld == 0).mean())
            avg_late = float(ld[late_flag].mean()) if late_flag.any() else 0.0
            max_late = float(ld.max())

        # UPDATED: exposure at anchor time (count ALL unpaid obligations)
        # unpaid at anchor_dt => paid_date is null OR paid after anchor_dt
        act = inst[
            (inst["user_id"] == uid) &
            ((inst["paid_date"].isna()) | (inst["paid_date"] > anchor_dt)) &
            (inst["due_date"].notna())
        ]
        num_active = int(act.shape[0])

        return (late_rate, avg_late, max_late, ontime_rate, num_active)

    rep_rows = [repayment_agg(u, d, 90) for u, d in zip(gold["user_id"], gold["anchor_date"])]
    rep_df = pd.DataFrame(
        rep_rows,
        columns=[
            "late_payment_rate_90d", "avg_late_days_90d", "max_late_days_90d",
            "on_time_payment_rate_90d", "num_active_plans"
        ],
        index=gold.index
    )
    gold = pd.concat([gold, rep_df], axis=1)

    # Severity scores
    gold["repayment_severity_score"] = (
        1.5 * gold["late_payment_rate_90d"].fillna(0) +
        0.5 * np.log1p(gold["avg_late_days_90d"].fillna(0)) +
        0.2 * np.log1p(gold["max_late_days_90d"].fillna(0)) +
        0.8 * (1 - gold["on_time_payment_rate_90d"].fillna(0))
    )
    gold["load_pressure_score"] = np.log1p(gold["num_active_plans"].fillna(0))

    return gold


def add_order_features(gold: pd.DataFrame, orders: pd.DataFrame) -> pd.DataFrame:
    """Add order aggregation features (30d lookback)."""
    ordr = orders.copy()
    ordr = ordr[ordr["order_date"].notna()].copy()

    def order_agg(uid, anchor_dt, days=30):
        lo = anchor_dt - pd.Timedelta(days=days)
        w = ordr[
            (ordr["user_id"] == uid) &
            (ordr["order_date"] < anchor_dt) &
            (ordr["order_date"] >= lo)
        ]
        if len(w) == 0:
            return (0, np.nan, np.nan, np.nan)
        return (
            int(len(w)),
            float(w["amount"].mean()),
            float(w["amount"].max()),
            float(w["amount"].sum())
        )

    ord_rows = [order_agg(u, d, 30) for u, d in zip(gold["user_id"], gold["anchor_date"])]
    ord_df = pd.DataFrame(
        ord_rows,
        columns=["total_orders_30d", "avg_order_amount_30d", "max_order_amount_30d", "sum_order_amount_30d"],
        index=gold.index
    )
    gold = pd.concat([gold, ord_df], axis=1)

    gold["spend_pressure_score"] = (
        0.4 * np.log1p(gold["total_orders_30d"].fillna(0)) +
        0.6 * np.log1p(gold["max_order_amount_30d"].fillna(0))
    )

    # Add currency
    if "order_id" in gold.columns and "order_id" in orders.columns:
        gold = gold.merge(orders[["order_id", "currency"]], on="order_id", how="left")
        if "currency" in gold.columns:
            gold["currency"] = gold["currency"].astype("string")

    return gold


def add_friction_features(gold: pd.DataFrame, disputes: pd.DataFrame, refunds: pd.DataFrame) -> pd.DataFrame:
    """Add dispute and refund features (90d lookback)."""
    def count_user_events(events_df, uid, anchor_dt, date_col, days=90):
        lo = anchor_dt - pd.Timedelta(days=days)
        w = events_df[
            (events_df["user_id"] == uid) &
            (events_df[date_col].notna()) &
            (events_df[date_col] < anchor_dt) &
            (events_df[date_col] >= lo)
        ]
        return int(w.shape[0])

    gold["dispute_count_90d"] = [
        count_user_events(disputes, u, d, "dispute_date", 90)
        for u, d in zip(gold["user_id"], gold["anchor_date"])
    ]
    gold["refund_count_90d"] = [
        count_user_events(refunds, u, d, "refund_date", 90)
        for u, d in zip(gold["user_id"], gold["anchor_date"])
    ]

    gold["context_friction_score"] = 1.0 * gold["dispute_count_90d"] + 0.5 * gold["refund_count_90d"]

    return gold


def add_checkout_features(gold: pd.DataFrame, checkout_events: pd.DataFrame) -> pd.DataFrame:
    """Add checkout behavior features (30d lookback)."""
    ce = checkout_events.copy()
    ce = ce[ce["event_date"].notna()].copy()

    def checkout_agg(uid, anchor_dt, days=30):
        lo = anchor_dt - pd.Timedelta(days=days)
        w = ce[
            (ce["user_id"] == uid) &
            (ce["event_date"] < anchor_dt) &
            (ce["event_date"] >= lo)
        ]
        if len(w) == 0:
            return (0, 0, 0, 0.0)

        n_start = int((w["event_type"] == "checkout_start").sum())
        n_success = int((w["event_type"] == "checkout_success").sum())
        n_abandon = int((w["event_type"] == "checkout_abandon").sum())
        abandon_rate = float(n_abandon / n_start) if n_start > 0 else 0.0
        return (n_start, n_success, n_abandon, abandon_rate)

    chk_rows = [checkout_agg(u, d, 30) for u, d in zip(gold["user_id"], gold["anchor_date"])]
    chk_df = pd.DataFrame(
        chk_rows,
        columns=["checkout_start_30d", "checkout_success_30d", "checkout_abandon_30d", "checkout_abandon_rate_30d"],
        index=gold.index
    )
    gold = pd.concat([gold, chk_df], axis=1)

    gold["checkout_friction_score"] = (
        1.0 * np.log1p(gold["checkout_abandon_30d"].fillna(0)) +
        2.0 * gold["checkout_abandon_rate_30d"].fillna(0)
    )

    return gold


def add_merchant_features(
    gold: pd.DataFrame,
    merchants: pd.DataFrame,
    disputes: pd.DataFrame,
    refunds: pd.DataFrame,
    orders: pd.DataFrame
) -> pd.DataFrame:
    """Add merchant-level features."""
    gold = gold.merge(
        merchants[["merchant_id", "merchant_name", "category", "city", "merchant_status"]],
        on="merchant_id", how="left", suffixes=("", "_merchant")
    )
    gold.rename(columns={"city": "city_merchant"}, inplace=True)

    # Merchant status encoding
    mstat_map = {"active": 1, "under_review": -1, "blocked": -2, "closed": -2}
    gold["merchant_status_num"] = gold["merchant_status"].astype(str).str.lower().map(mstat_map).fillna(0)

    # Ensure orders order_date is datetime and non-null
    orders_dt = orders.copy()
    orders_dt = orders_dt[orders_dt["order_date"].notna()].copy()

    def merchant_rate(events_df, mid, anchor_dt, date_col, days=90):
        lo = anchor_dt - pd.Timedelta(days=days)

        denom = orders_dt[
            (orders_dt["merchant_id"] == mid) &
            (orders_dt["order_date"] < anchor_dt) &
            (orders_dt["order_date"] >= lo)
        ].shape[0]

        if denom == 0:
            return 0.0

        tmp = events_df[events_df[date_col].notna()]
        num = tmp[
            (tmp["merchant_id"] == mid) &
            (tmp[date_col] < anchor_dt) &
            (tmp[date_col] >= lo)
        ].shape[0]
        return float(num / denom)

    gold["merchant_dispute_rate_90d"] = [
        merchant_rate(disputes, mid, d, "dispute_date", 90)
        for mid, d in zip(gold["merchant_id"], gold["anchor_date"])
    ]
    gold["merchant_refund_rate_90d"] = [
        merchant_rate(refunds, mid, d, "refund_date", 90)
        for mid, d in zip(gold["merchant_id"], gold["anchor_date"])
    ]

    gold["merchant_risk_score"] = (
        1.0 * (gold["merchant_status_num"] < 0).astype(int) +
        2.0 * gold["merchant_dispute_rate_90d"].fillna(0) +
        1.0 * gold["merchant_refund_rate_90d"].fillna(0)
    )

    # Ensure categorical stability
    for c in ["category", "city_merchant"]:
        if c in gold.columns:
            gold[c] = gold[c].astype("string")

    return gold


def build_gold_features(data_files: Dict[str, str]) -> pd.DataFrame:
    """Main pipeline: build all features for UC1."""
    dfs = load_and_parse_dates(data_files)

    gold = build_base_table(dfs["installments"])
    gold = add_user_features(gold, dfs["users"])
    gold = add_repayment_features(gold, dfs["installments"])  # uses full installments (includes unpaid)
    gold = add_order_features(gold, dfs["orders"])
    gold = add_friction_features(gold, dfs["disputes"], dfs["refunds"])
    gold = add_checkout_features(gold, dfs["checkout_events"])
    gold = add_merchant_features(gold, dfs["merchants"], dfs["disputes"], dfs["refunds"], dfs["orders"])

    return gold
