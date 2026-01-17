"""
UC1 - Build daily scoring set (before due date)

Goal:
- Predict risk for installments that are:
    status == "unpaid"
    due_date >= scoring_date (today by default)
- anchor_date = scoring_date (today)
- Features use history strictly before anchor_date (your current feature logic does this)

Outputs:
- CSV scoring_set_uc1.csv containing:
    - ID columns (optional)
    - all model features (bundle.feature_names compatible)
    - optional extra: days_to_due (recommended if you add it to features later)

IMPORTANT:
- This does NOT change your training feature logic.
- It just chooses cohort + sets anchor_date.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional, Dict

import numpy as np
import pandas as pd

from src.config import (
    SILVER_FILES,
    GOLD_UC1_FEATURES,
    ID_COLS,
    GOLD_DIR,
)

from src.uc1_late_risk.features import load_and_parse_dates
from src.uc1_late_risk.features import (
    add_user_features,
    add_repayment_features,
    add_order_features,
    add_friction_features,
    add_checkout_features,
    add_merchant_features,
)

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def _normalize_status(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip().str.lower()


def build_scoring_set(
    scoring_date: Optional[str] = None,
    output_csv: Optional[str | Path] = None,
    include_ids: bool = True,
) -> Path:
    """
    Build scoring set for "daily monitoring before due date".

    scoring_date:
      - None => today (local)
      - "YYYY-MM-DD" string => that day

    output_csv:
      - None => data/gold/uc1_scoring_set.csv
    """
    dfs = load_and_parse_dates({k: str(v) for k, v in SILVER_FILES.items()})

    inst = dfs["installments"].copy()
    if "due_date" not in inst.columns:
        raise ValueError("installments must include due_date")
    if "status" not in inst.columns:
        raise ValueError("installments must include status")

    # scoring date
    if scoring_date is None:
        anchor_dt = pd.Timestamp(datetime.now().date())
    else:
        anchor_dt = pd.to_datetime(scoring_date)

    # cohort: unpaid and not yet due
    inst["status_norm"] = _normalize_status(inst["status"])
    cohort = inst[
        (inst["due_date"].notna()) &
        (inst["status_norm"] == "unpaid") &
        (inst["due_date"] >= anchor_dt)
    ].copy()

    if cohort.empty:
        raise ValueError(
            f"No rows in scoring cohort for anchor_date={anchor_dt.date()} "
            f"(unpaid & due_date >= anchor_date)."
        )

    # anchor_date = scoring_date (today)
    cohort["anchor_date"] = anchor_dt

    # OPTIONAL (recommended if you later include in model):
    # cohort["days_to_due"] = (cohort["due_date"] - cohort["anchor_date"]).dt.days.clip(lower=0)

    # Build features using your existing functions
    gold = cohort

    gold = add_user_features(gold, dfs["users"])
    gold = add_repayment_features(gold, dfs["installments"])  # full history incl unpaid
    gold = add_order_features(gold, dfs["orders"])
    gold = add_friction_features(gold, dfs["disputes"], dfs["refunds"])
    gold = add_checkout_features(gold, dfs["checkout_events"])
    gold = add_merchant_features(gold, dfs["merchants"], dfs["disputes"], dfs["refunds"], dfs["orders"])

    # Keep only what the model needs (+ ids if you want)
    feature_cols = [c for c in GOLD_UC1_FEATURES if c in gold.columns]

    cols = []
    if include_ids:
        cols += [c for c in ID_COLS if c in gold.columns]
        # helpful extra context for ops
        for extra in ["due_date", "status"]:
            if extra in gold.columns:
                cols.append(extra)

    cols += feature_cols

    scoring_df = gold.loc[:, cols].copy()

    # Save
    if output_csv is None:
        output_csv = GOLD_DIR / "uc1_scoring_set.csv"

    out_path = Path(output_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    scoring_df.to_csv(out_path, index=False)

    print("anchor_date:", anchor_dt.date())
    print("scoring_set rows:", scoring_df.shape[0])
    print("saved to:", out_path)

    return out_path


# ------------------------------------------------------------
# CLI
# ------------------------------------------------------------
def main():
    import argparse

    parser = argparse.ArgumentParser(description="Build UC1 daily scoring set (unpaid & not due yet)")
    parser.add_argument("--date", type=str, default=None, help="Scoring date YYYY-MM-DD (default: today)")
    parser.add_argument("--output", type=str, default=None, help="Output CSV path")
    parser.add_argument("--no_ids", action="store_true", help="Do not include ID columns in output")
    args = parser.parse_args()

    build_scoring_set(
        scoring_date=args.date,
        output_csv=args.output,
        include_ids=not args.no_ids
    )


if __name__ == "__main__":
    main()
