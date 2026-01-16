"""
Feature engineering for UC1: Late Payment Risk
"""
import pandas as pd
import numpy as np
from typing import Dict


def load_and_parse_dates(data_files: Dict[str, str]) -> Dict[str, pd.DataFrame]:
    """Load all CSVs and parse date columns"""
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
    dfs["users"]["signup_date"] = pd.to_datetime(dfs["users"]["signup_date"], errors="coerce")
    dfs["orders"]["order_date"] = pd.to_datetime(dfs["orders"]["order_date"], errors="coerce")
    dfs["installments"]["due_date"] = pd.to_datetime(dfs["installments"]["due_date"], errors="coerce")
    dfs["installments"]["paid_date"] = pd.to_datetime(dfs["installments"]["paid_date"], errors="coerce")
    dfs["payments"]["payment_date"] = pd.to_datetime(dfs["payments"]["payment_date"], errors="coerce")
    dfs["disputes"]["dispute_date"] = pd.to_datetime(dfs["disputes"]["dispute_date"], errors="coerce")
    dfs["refunds"]["refund_date"] = pd.to_datetime(dfs["refunds"]["refund_date"], errors="coerce")
    dfs["checkout_events"]["event_date"] = pd.to_datetime(dfs["checkout_events"]["event_date"], errors="coerce")
    dfs["merchants"]["created_at"] = pd.to_datetime(dfs["merchants"]["created_at"], errors="coerce")
    
    return dfs


def build_base_table(installments: pd.DataFrame) -> pd.DataFrame:
    """Create base table with anchor date and target"""
    gold = installments.copy()
    
    # Ensure datetime
    gold["due_date"] = pd.to_datetime(gold["due_date"], errors="coerce")
    gold["paid_date"] = pd.to_datetime(gold["paid_date"], errors="coerce")
    
    # Keep only valid due_date
    gold = gold[gold["due_date"].notna()].copy()
    
    # IMPORTANT: Keep only installments with status = paid or late
    gold = gold[gold["status"].astype(str).str.lower().isin(["paid", "late"])].copy()
    
    gold["anchor_date"] = gold["due_date"]
    
    # Calculate late days and target
    late_days_calc = (gold["paid_date"] - gold["due_date"]).dt.days
    gold["late_days_final"] = gold["late_days"].fillna(late_days_calc)
    gold["is_late"] = (gold["late_days_final"].fillna(0) > 0).astype(int)
    
    return gold


def add_user_features(gold: pd.DataFrame, users: pd.DataFrame) -> pd.DataFrame:
    """Add user-level features"""
    gold = gold.merge(
        users[["user_id", "signup_date", "kyc_level", "city", "account_status"]],
        on="user_id", how="left"
    )
    gold.rename(columns={"city": "user_city"}, inplace=True)
    
    # Ensure signup_date is datetime
    gold["signup_date"] = pd.to_datetime(gold["signup_date"], errors="coerce")
    
    # Account age
    gold["account_age_days"] = (gold["anchor_date"] - gold["signup_date"]).dt.days
    
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
    
    return gold


def add_repayment_features(gold: pd.DataFrame, installments: pd.DataFrame) -> pd.DataFrame:
    """Add repayment history features (90d lookback)"""
    inst = installments.copy()
    inst = inst[inst["due_date"].notna()].copy()
    inst["due_date"] = pd.to_datetime(inst["due_date"], errors="coerce")
    inst["paid_date"] = pd.to_datetime(inst["paid_date"], errors="coerce")
    inst["late_days_final"] = inst["late_days"].fillna((inst["paid_date"] - inst["due_date"]).dt.days)
    inst["late_days_pos"] = inst["late_days_final"].clip(lower=0)
    
    def repayment_agg(uid, anchor_dt, days=90):
        lo = anchor_dt - pd.Timedelta(days=days)
        hist = inst[(inst["user_id"] == uid) & 
                    (inst["due_date"] < anchor_dt) & 
                    (inst["due_date"] >= lo)].copy()
        
        if len(hist) == 0:
            return (np.nan, np.nan, np.nan, np.nan, 0)
        
        ld = hist["late_days_pos"].fillna(0)
        late_flag = (ld > 0)
        
        late_rate = float(late_flag.mean())
        ontime_rate = float((ld == 0).mean())
        avg_late = float(ld[late_flag].mean()) if late_flag.any() else 0.0
        max_late = float(ld.max())
        
        # Active plans
        act = inst[(inst["user_id"] == uid) & 
                   (inst["due_date"] < anchor_dt) & 
                   ((inst["paid_date"].isna()) | (inst["paid_date"] > anchor_dt))]
        num_active = int(len(act))
        
        return (late_rate, avg_late, max_late, ontime_rate, num_active)
    
    rep_rows = [repayment_agg(u, d, 90) for u, d in zip(gold["user_id"], gold["anchor_date"])]
    rep_df = pd.DataFrame(rep_rows, columns=[
        "late_payment_rate_90d", "avg_late_days_90d", "max_late_days_90d", 
        "on_time_payment_rate_90d", "num_active_plans"
    ], index=gold.index)
    
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
    """Add order aggregation features (30d lookback)"""
    ordr = orders.copy()
    ordr["order_date"] = pd.to_datetime(ordr["order_date"], errors="coerce")
    ordr = ordr[ordr["order_date"].notna()].copy()
    
    def order_agg(uid, anchor_dt, days=30):
        lo = anchor_dt - pd.Timedelta(days=days)
        w = ordr[(ordr["user_id"] == uid) & 
                 (ordr["order_date"] < anchor_dt) & 
                 (ordr["order_date"] >= lo)]
        if len(w) == 0:
            return (0, np.nan, np.nan, np.nan)
        return (int(len(w)), float(w["amount"].mean()), 
                float(w["amount"].max()), float(w["amount"].sum()))
    
    ord_rows = [order_agg(u, d, 30) for u, d in zip(gold["user_id"], gold["anchor_date"])]
    ord_df = pd.DataFrame(ord_rows, columns=[
        "total_orders_30d", "avg_order_amount_30d", 
        "max_order_amount_30d", "sum_order_amount_30d"
    ], index=gold.index)
    
    gold = pd.concat([gold, ord_df], axis=1)
    
    gold["spend_pressure_score"] = (
        0.4 * np.log1p(gold["total_orders_30d"].fillna(0)) +
        0.6 * np.log1p(gold["max_order_amount_30d"].fillna(0))
    )
    
    # Add currency
    gold = gold.merge(orders[["order_id", "currency"]], on="order_id", how="left")
    
    return gold


def add_friction_features(gold: pd.DataFrame, disputes: pd.DataFrame, 
                          refunds: pd.DataFrame) -> pd.DataFrame:
    """Add dispute and refund features (90d lookback)"""
    def count_user_events(events_df, uid, anchor_dt, date_col, days=90):
        tmp = events_df.copy()
        tmp[date_col] = pd.to_datetime(tmp[date_col], errors="coerce")
        lo = anchor_dt - pd.Timedelta(days=days)
        return int(tmp[(tmp["user_id"] == uid) & 
                       (tmp[date_col] < anchor_dt) & 
                       (tmp[date_col] >= lo)].shape[0])
    
    gold["dispute_count_90d"] = [count_user_events(disputes, u, d, "dispute_date", 90)
                                 for u, d in zip(gold["user_id"], gold["anchor_date"])]
    gold["refund_count_90d"] = [count_user_events(refunds, u, d, "refund_date", 90)
                                for u, d in zip(gold["user_id"], gold["anchor_date"])]
    
    gold["context_friction_score"] = 1.0 * gold["dispute_count_90d"] + 0.5 * gold["refund_count_90d"]
    
    return gold


def add_checkout_features(gold: pd.DataFrame, checkout_events: pd.DataFrame) -> pd.DataFrame:
    """Add checkout behavior features (30d lookback)"""
    checkout_events = checkout_events.copy()
    checkout_events["event_date"] = pd.to_datetime(checkout_events["event_date"], errors="coerce")
    
    def checkout_agg(uid, anchor_dt, days=30):
        lo = anchor_dt - pd.Timedelta(days=days)
        w = checkout_events[(checkout_events["user_id"] == uid) & 
                           (checkout_events["event_date"] < anchor_dt) & 
                           (checkout_events["event_date"] >= lo)].copy()
        if len(w) == 0:
            return (0, 0, 0, 0.0)
        
        n_start = int((w["event_type"] == "checkout_start").sum())
        n_success = int((w["event_type"] == "checkout_success").sum())
        n_abandon = int((w["event_type"] == "checkout_abandon").sum())
        abandon_rate = float(n_abandon / n_start) if n_start > 0 else 0.0
        
        return (n_start, n_success, n_abandon, abandon_rate)
    
    chk_rows = [checkout_agg(u, d, 30) for u, d in zip(gold["user_id"], gold["anchor_date"])]
    chk_df = pd.DataFrame(chk_rows, columns=[
        "checkout_start_30d", "checkout_success_30d", 
        "checkout_abandon_30d", "checkout_abandon_rate_30d"
    ], index=gold.index)
    
    gold = pd.concat([gold, chk_df], axis=1)
    
    gold["checkout_friction_score"] = (
        1.0 * np.log1p(gold["checkout_abandon_30d"].fillna(0)) +
        2.0 * gold["checkout_abandon_rate_30d"].fillna(0)
    )
    
    return gold


def add_merchant_features(gold: pd.DataFrame, merchants: pd.DataFrame, 
                          disputes: pd.DataFrame, refunds: pd.DataFrame, 
                          orders: pd.DataFrame) -> pd.DataFrame:
    """Add merchant-level features"""
    gold = gold.merge(
        merchants[["merchant_id", "merchant_name", "category", "city", "merchant_status"]],
        on="merchant_id", how="left", suffixes=("", "_merchant")
    )
    gold.rename(columns={"city": "city_merchant"}, inplace=True)
    
    # Merchant status encoding
    mstat_map = {"active": 1, "under_review": -1, "blocked": -2, "closed": -2}
    gold["merchant_status_num"] = gold["merchant_status"].astype(str).str.lower().map(mstat_map).fillna(0)
    
    # Ensure orders order_date is datetime
    orders_dt = orders.copy()
    orders_dt["order_date"] = pd.to_datetime(orders_dt["order_date"], errors="coerce")
    
    # Merchant dispute/refund rates
    def merchant_rate(events_df, mid, anchor_dt, date_col, days=90):
        tmp = events_df.copy()
        tmp[date_col] = pd.to_datetime(tmp[date_col], errors="coerce")
        lo = anchor_dt - pd.Timedelta(days=days)
        
        denom = orders_dt[(orders_dt["merchant_id"] == mid) & 
                         (orders_dt["order_date"] < anchor_dt) & 
                         (orders_dt["order_date"] >= lo)].shape[0]
        if denom == 0:
            return 0.0
        num = tmp[(tmp["merchant_id"] == mid) & 
                  (tmp[date_col] < anchor_dt) & 
                  (tmp[date_col] >= lo)].shape[0]
        return float(num / denom)
    
    gold["merchant_dispute_rate_90d"] = [merchant_rate(disputes, mid, d, "dispute_date", 90)
                                         for mid, d in zip(gold["merchant_id"], gold["anchor_date"])]
    gold["merchant_refund_rate_90d"] = [merchant_rate(refunds, mid, d, "refund_date", 90)
                                        for mid, d in zip(gold["merchant_id"], gold["anchor_date"])]
    
    gold["merchant_risk_score"] = (
        1.0 * (gold["merchant_status_num"] < 0).astype(int) +
        2.0 * gold["merchant_dispute_rate_90d"].fillna(0) +
        1.0 * gold["merchant_refund_rate_90d"].fillna(0)
    )
    
    return gold


def build_gold_features(data_files: Dict[str, str]) -> pd.DataFrame:
    """
    Main pipeline: build all features for UC1
    """
    # Load data
    dfs = load_and_parse_dates(data_files)
    
    # Build features step by step
    gold = build_base_table(dfs["installments"])
    gold = add_user_features(gold, dfs["users"])
    gold = add_repayment_features(gold, dfs["installments"])
    gold = add_order_features(gold, dfs["orders"])
    gold = add_friction_features(gold, dfs["disputes"], dfs["refunds"])
    gold = add_checkout_features(gold, dfs["checkout_events"])
    gold = add_merchant_features(gold, dfs["merchants"], dfs["disputes"], 
                                  dfs["refunds"], dfs["orders"])
    
    return gold