"""
UC1 - Build Gold Features (MLflow runner)

- Uses src.uc1_late_risk.features.build_gold_features (pure logic)
- Saves gold_uc1_features.csv
- Logs artifacts + basic metrics to MLflow
"""

import json
from pathlib import Path

import mlflow
import pandas as pd

from src.config import (
    SILVER_FILES,
    GOLD_UC1_FILE,
    GOLD_UC1_FEATURES,
    ID_COLS,
    TARGET,
    MLFLOW_TRACKING_URI,
    MLFLOW_EXPERIMENT_NAME,
)

from src.uc1_late_risk.features import build_gold_features


def main():
    # -----------------------------
    # MLflow setup
    # -----------------------------
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)

    with mlflow.start_run(run_name="uc1_build_gold_features") as run:
        # -----------------------------
        # Build gold features (pure logic)
        # -----------------------------
        gold = build_gold_features(SILVER_FILES)

        # -----------------------------
        # Minimal runner checks (safe)
        # -----------------------------
        if TARGET not in gold.columns:
            raise ValueError(f"TARGET '{TARGET}' missing from gold output.")

        if "anchor_date" not in gold.columns:
            raise ValueError("anchor_date missing from gold output.")

        if gold["anchor_date"].isna().any():
            raise ValueError("anchor_date has null values in gold output.")

        # ensure at least some rows
        if gold.shape[0] == 0:
            raise ValueError("Gold output has 0 rows. Check input files or filtering logic.")

        # ensure target is binary
        unique_y = set(pd.Series(gold[TARGET].dropna().unique()).astype(int).tolist())
        if not unique_y.issubset({0, 1}):
            raise ValueError(f"Target {TARGET} not binary. Found: {unique_y}")

        # -----------------------------
        # Save to GOLD_UC1_FILE
        # -----------------------------
        out_path = Path(GOLD_UC1_FILE)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        gold.to_csv(out_path, index=False)

        # -----------------------------
        # Log artifacts
        # -----------------------------
        mlflow.log_artifact(str(out_path), artifact_path="data")

        # Data contract artifact (helps agent + training reproducibility)
        contract = {
            "gold_file": str(out_path),
            "id_cols": ID_COLS,
            "target": TARGET,
            "features_expected": GOLD_UC1_FEATURES,
            "n_rows": int(gold.shape[0]),
            "n_cols": int(gold.shape[1]),
        }
        contract_path = "uc1_data_contract.json"
        with open(contract_path, "w") as f:
            json.dump(contract, f, indent=2)

        mlflow.log_artifact(contract_path, artifact_path="data_contract")

        # -----------------------------
        # Log metrics
        # -----------------------------
        late_rate = float(pd.Series(gold[TARGET]).mean())
        mlflow.log_metric("rows", int(gold.shape[0]))
        mlflow.log_metric("cols", int(gold.shape[1]))
        mlflow.log_metric("late_rate", late_rate)

        # Optional: missingness summary (top 10)
        miss = gold[GOLD_UC1_FEATURES].isna().mean().sort_values(ascending=False)
        miss_top = miss.head(10).to_dict()
        miss_path = "missingness_top10.json"
        with open(miss_path, "w") as f:
            json.dump({k: float(v) for k, v in miss_top.items()}, f, indent=2)
        mlflow.log_artifact(miss_path, artifact_path="data_quality")

        print("MLflow run_id:", run.info.run_id)
        print("Saved gold to:", out_path)
        print("late_rate:", round(late_rate, 4))


if __name__ == "__main__":
    main()
