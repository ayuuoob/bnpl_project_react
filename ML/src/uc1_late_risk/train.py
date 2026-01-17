"""
UC1 - Train models (MLflow runner)

- Loads gold_uc1_features.csv
- Trains multiple models with CV (ROC-AUC / PR-AUC / F1 / Precision / Recall / Accuracy)
- Picks best model (default: ROC-AUC)
- Tunes threshold on holdout set (default: maximize F1)
- Saves ONE final model bundle as pkl
- Logs everything to MLflow (metrics + artifacts)

"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd
import mlflow
from mlflow.tracking import MlflowClient
import mlflow.pyfunc


from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    accuracy_score,
    confusion_matrix,
    classification_report,
)

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier

# XGBoost
from xgboost import XGBClassifier

from src.config import (
    GOLD_UC1_FILE,
    GOLD_UC1_FEATURES,
    TARGET,
    RANDOM_STATE,
    TEST_SIZE,
    CV_FOLDS,
    MLFLOW_TRACKING_URI,
    MLFLOW_EXPERIMENT_NAME,
    MODELS_DIR,
)


# ------------------------------------------------------------
# Model bundle (what the agent will load)
# ------------------------------------------------------------
@dataclass
class RiskModelBundle:
    """
    Saved object = pipeline + threshold + feature list + model identity.

    Agent loads it with joblib.load() and calls:
      - bundle.predict_proba(df)  -> Nx2 probs
      - bundle.predict(df)        -> binary risky label using bundle.risk_threshold
    """
    model_id: str
    model_name: str
    pipeline: Pipeline
    risk_threshold: float
    feature_names: List[str]

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        return self.pipeline.predict_proba(X)

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        proba = self.predict_proba(X)[:, 1]
        return (proba >= self.risk_threshold).astype(int)


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def _infer_cat_num_columns(X_features_only: pd.DataFrame, feature_cols: List[str]) -> Tuple[List[str], List[str]]:
    """
    X_features_only must be X = df[feature_cols] (no ids/target).
    """
    cat_cols, num_cols = [], []
    for c in feature_cols:
        if pd.api.types.is_numeric_dtype(X_features_only[c]):
            num_cols.append(c)
        else:
            cat_cols.append(c)
    return num_cols, cat_cols


def _build_preprocessor(num_cols: List[str], cat_cols: List[str]) -> ColumnTransformer:
    num_pipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    cat_pipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("num", num_pipe, num_cols),
            ("cat", cat_pipe, cat_cols),
        ],
        remainder="drop",
        sparse_threshold=0.3,
    )


def _make_pipelines(prep: ColumnTransformer, scale_pos_weight: float) -> Dict[str, Pipeline]:
    return {
        "LogReg": Pipeline(
            steps=[
                ("prep", prep),
                ("model", LogisticRegression(
                    max_iter=5000,
                    solver="lbfgs",
                    class_weight="balanced",
                    random_state=RANDOM_STATE
                )),
            ]
        ),
        "RF": Pipeline(
            steps=[
                ("prep", prep),
                ("model", RandomForestClassifier(
                    n_estimators=400,
                    max_depth=None,
                    min_samples_split=2,
                    min_samples_leaf=1,
                    random_state=RANDOM_STATE,
                    n_jobs=-1,
                    class_weight="balanced_subsample",
                )),
            ]
        ),
        "GB": Pipeline(
            steps=[
                ("prep", prep),
                ("model", GradientBoostingClassifier(random_state=RANDOM_STATE)),
            ]
        ),
        "XGB": Pipeline(
            steps=[
                ("prep", prep),
                ("model", XGBClassifier(
                    n_estimators=500,
                    max_depth=4,
                    learning_rate=0.05,
                    subsample=0.9,
                    colsample_bytree=0.9,
                    reg_lambda=1.0,
                    objective="binary:logistic",
                    eval_metric="logloss",
                    random_state=RANDOM_STATE,
                    n_jobs=-1,
                    scale_pos_weight=scale_pos_weight,
                    # Important: we OneHot encode categorical, so keep this False
                    enable_categorical=False,
                )),
            ]
        ),
    }


def _cv_eval(pipe: Pipeline, X: pd.DataFrame, y: pd.Series, n_splits: int) -> Dict[str, float]:
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_STATE)

    roc_list, pr_list, f1_list, prec_list, rec_list, acc_list = [], [], [], [], [], []

    for tr_idx, va_idx in skf.split(X, y):
        X_tr, X_va = X.iloc[tr_idx], X.iloc[va_idx]
        y_tr, y_va = y.iloc[tr_idx], y.iloc[va_idx]

        pipe.fit(X_tr, y_tr)
        proba = pipe.predict_proba(X_va)[:, 1]
        pred = (proba >= 0.5).astype(int)

        roc_list.append(roc_auc_score(y_va, proba))
        pr_list.append(average_precision_score(y_va, proba))
        f1_list.append(f1_score(y_va, pred, zero_division=0))
        prec_list.append(precision_score(y_va, pred, zero_division=0))
        rec_list.append(recall_score(y_va, pred, zero_division=0))
        acc_list.append(accuracy_score(y_va, pred))

    return {
        "cv_roc_auc_mean": float(np.mean(roc_list)),
        "cv_roc_auc_std": float(np.std(roc_list)),
        "cv_pr_auc_mean": float(np.mean(pr_list)),
        "cv_f1_mean": float(np.mean(f1_list)),
        "cv_precision_mean": float(np.mean(prec_list)),
        "cv_recall_mean": float(np.mean(rec_list)),
        "cv_accuracy_mean": float(np.mean(acc_list)),
    }


def _best_threshold_for_f1(y_true: pd.Series, proba: np.ndarray) -> Tuple[float, float]:
    thresholds = np.linspace(0.05, 0.95, 91)
    best_t, best_f1 = 0.5, -1.0
    for t in thresholds:
        pred = (proba >= t).astype(int)
        f1 = f1_score(y_true, pred, zero_division=0)
        if f1 > best_f1:
            best_f1 = f1
            best_t = float(t)
    return best_t, float(best_f1)


def _save_registry_artifacts(best_pipe: Pipeline, meta: dict, out_dir: Path) -> tuple[Path, Path]:
    """
    Save pipeline + meta as standalone artifacts (portable, no RiskModelBundle dependency).
    Returns: (pipeline_path, meta_path)
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    pipeline_path = out_dir / "pipeline.joblib"
    meta_path = out_dir / "meta.json"

    joblib.dump(best_pipe, pipeline_path)
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return pipeline_path, meta_path


class UC1RegistryPyFunc(mlflow.pyfunc.PythonModel):
    """
    MLflow Registry model:
    - loads pipeline + meta.json
    - predict() returns DataFrame with proba + is_risky (+ optional margin)
    """

    def load_context(self, context):
        self.pipeline = joblib.load(context.artifacts["pipeline"])
        self.meta = json.loads(Path(context.artifacts["meta"]).read_text(encoding="utf-8"))
        self.feature_names = self.meta["features"]
        self.threshold = float(self.meta["risk_threshold"])

    def predict(self, context, model_input: pd.DataFrame) -> pd.DataFrame:
        X = model_input.loc[:, self.feature_names].copy()
        proba = self.pipeline.predict_proba(X)[:, 1].astype(float)
        pred = (proba >= self.threshold).astype(int)
        out = pd.DataFrame({
            "proba_late_30d": proba,
            "risk_threshold": float(self.threshold),
            "is_risky_late": pred,
            "margin_vs_threshold": (proba - self.threshold).astype(float),
        })
        # traceability
        out["model_id"] = self.meta.get("model_id")
        out["model_name"] = self.meta.get("model_name")
        return out


def safe_register_model(model_uri: str, registered_name: str, *, alias: str = "champion"):
    """
    Safe model registration:
    - Registers a new version
    - Tries to set alias (new MLflow) OR stage (older MLflow)
    - Never breaks your training if registry unsupported
    """
    client = MlflowClient()
    try:
        mv = mlflow.register_model(model_uri=model_uri, name=registered_name)
        # wait not needed; local should register quickly
        try:
            # Preferred modern way: alias
            client.set_registered_model_alias(name=registered_name, alias=alias, version=mv.version)
        except Exception:
            # Fallback older way: stage
            try:
                client.transition_model_version_stage(
                    name=registered_name,
                    version=mv.version,
                    stage="Staging",
                    archive_existing_versions=False
                )
            except Exception:
                pass

        print(f"[registry] Registered model '{registered_name}' version={mv.version} from {model_uri}")
        return mv.version

    except Exception as e:
        print(f"[registry] Skipped registration (registry not available): {e}")
        return None



# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
def main():
    # -----------------------------
    # MLflow setup
    # -----------------------------
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)

    model_id = str(MLFLOW_EXPERIMENT_NAME)  # stable UC identity

    gold_path = Path(GOLD_UC1_FILE)
    if not gold_path.exists():
        raise FileNotFoundError(
            f"Gold file not found: {gold_path}\n"
            f"Run feature build first: python -m src.uc1_late_risk.build_features"
        )

    gold = pd.read_csv(gold_path)

    # -----------------------------
    # Select feature columns (from config) and drop constants
    # -----------------------------
    feature_cols = [c for c in GOLD_UC1_FEATURES if c in gold.columns]
    const_cols = [c for c in feature_cols if gold[c].nunique(dropna=False) <= 1]
    feature_cols = [c for c in feature_cols if c not in const_cols]

    if TARGET not in gold.columns:
        raise ValueError(f"TARGET '{TARGET}' missing in gold.")

    X = gold[feature_cols].copy()
    y = gold[TARGET].astype(int).copy()

    # -----------------------------
    # Train/holdout split
    # -----------------------------
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y
    )

    # For XGB imbalance handling
    pos = float((y_train == 1).sum())
    neg = float((y_train == 0).sum())
    scale_pos_weight = (neg / pos) if pos > 0 else 1.0

    # Infer cat/num from FEATURES ONLY dataframe (X)
    num_cols, cat_cols = _infer_cat_num_columns(X, feature_cols)

    prep = _build_preprocessor(num_cols, cat_cols)
    pipelines = _make_pipelines(prep, scale_pos_weight=scale_pos_weight)

    # -----------------------------
    # MLflow run
    # -----------------------------
    with mlflow.start_run(run_name="uc1_train_models") as run:
        mlflow.log_param("model_id", model_id)
        mlflow.log_param("n_rows_gold", int(gold.shape[0]))
        mlflow.log_param("n_features_used", int(len(feature_cols)))
        mlflow.log_param("dropped_constant_features", json.dumps(const_cols))
        mlflow.log_param("cv_folds", int(CV_FOLDS))
        mlflow.log_param("xgb_scale_pos_weight", float(scale_pos_weight))

        # CV per model (nested runs)
        cv_rows = []
        for name, pipe in pipelines.items():
            with mlflow.start_run(run_name=f"cv_{name}", nested=True):
                cvm = _cv_eval(pipe, X_train, y_train, CV_FOLDS)

                mlflow.log_param("model_name", name)
                for k, v in cvm.items():
                    mlflow.log_metric(k, v)

                cv_rows.append({"model": name, **cvm})

        cv_df = pd.DataFrame(cv_rows).sort_values("cv_roc_auc_mean", ascending=False).reset_index(drop=True)

        # save CV table artifact
        tmp_dir = MODELS_DIR.parent / "tmp"
        tmp_dir.mkdir(parents=True, exist_ok=True)

        cv_path = tmp_dir / "cv_summary.csv"
        cv_df.to_csv(cv_path, index=False)
        mlflow.log_artifact(str(cv_path), artifact_path="reports")

        # pick best model by ROC-AUC
        best_name = str(cv_df.iloc[0]["model"])
        best_pipe = pipelines[best_name]

        mlflow.log_param("best_model_by", "cv_roc_auc_mean")
        mlflow.log_param("best_model_name", best_name)

        # fit best
        best_pipe.fit(X_train, y_train)

        # holdout predictions
        proba = best_pipe.predict_proba(X_test)[:, 1]
        pred_05 = (proba >= 0.5).astype(int)

        # NOTE: metric names must be MLflow-safe (no '@')
        holdout = {
            "holdout_roc_auc": float(roc_auc_score(y_test, proba)),
            "holdout_pr_auc": float(average_precision_score(y_test, proba)),
            "holdout_f1_at_0_5": float(f1_score(y_test, pred_05, zero_division=0)),
            "holdout_precision_at_0_5": float(precision_score(y_test, pred_05, zero_division=0)),
            "holdout_recall_at_0_5": float(recall_score(y_test, pred_05, zero_division=0)),
            "holdout_accuracy_at_0_5": float(accuracy_score(y_test, pred_05)),
        }
        for k, v in holdout.items():
            mlflow.log_metric(k, v)

        # threshold tuning (maximize F1)
        best_t, best_f1 = _best_threshold_for_f1(y_test, proba)
        pred_t = (proba >= best_t).astype(int)

        tuned = {
            "best_threshold_f1": float(best_t),
            "holdout_f1_at_best_t": float(best_f1),
            "holdout_precision_at_best_t": float(precision_score(y_test, pred_t, zero_division=0)),
            "holdout_recall_at_best_t": float(recall_score(y_test, pred_t, zero_division=0)),
            "holdout_accuracy_at_best_t": float(accuracy_score(y_test, pred_t)),
        }
        for k, v in tuned.items():
            mlflow.log_metric(k, v)

        # artifacts: cm + report
        cm = confusion_matrix(y_test, pred_t)
        report = classification_report(y_test, pred_t, zero_division=0, output_dict=True)

        cm_path = tmp_dir / "confusion_matrix_best_t.json"
        rep_path = tmp_dir / "classification_report_best_t.json"

        cm_path.write_text(json.dumps(cm.tolist(), indent=2))
        rep_path.write_text(json.dumps(report, indent=2))

        mlflow.log_artifact(str(cm_path), artifact_path="reports")
        mlflow.log_artifact(str(rep_path), artifact_path="reports")

        # save ONE final model bundle (agent-friendly)
        bundle = RiskModelBundle(
            model_id=model_id,
            model_name=str(best_name),
            pipeline=best_pipe,
            risk_threshold=best_t,
            feature_names=feature_cols,
        )

        MODELS_DIR.mkdir(parents=True, exist_ok=True)

        # Use model_id in file name to avoid ambiguity across containers
        pkl_path = Path(MODELS_DIR) / f"{model_id}.bundle.pkl"
        joblib.dump(bundle, pkl_path)

        mlflow.log_artifact(str(pkl_path), artifact_path="models")

        # contract artifact
        meta = {
            "model_id": model_id,
            "model_name": best_name,
            "risk_threshold": best_t,
            "features": feature_cols,
        }
        meta_path = tmp_dir / "model_contract.json"
        meta_path.write_text(json.dumps(meta, indent=2))
        mlflow.log_artifact(str(meta_path), artifact_path="models")

        # ------------------------------------------------------------
        # Registry-ready MLflow model (pipeline + meta) + SAFE registration
        # Requires helper functions:
        #   - _save_registry_artifacts(...)
        #   - UC1RegistryPyFunc (mlflow.pyfunc.PythonModel)
        #   - safe_register_model(...)
        # ------------------------------------------------------------
        registry_art_dir = tmp_dir / "registry_artifacts"
        pipeline_path, meta2_path = _save_registry_artifacts(best_pipe, meta, registry_art_dir)

        mlflow.pyfunc.log_model(
            artifact_path="registry_model",
            python_model=UC1RegistryPyFunc(),
            artifacts={
                "pipeline": str(pipeline_path),
                "meta": str(meta2_path),
            },
            pip_requirements=[
                "pandas",
                "numpy",
                "scikit-learn",
                "mlflow",
                "joblib",
                "xgboost",
            ],
        )

        REGISTERED_MODEL_NAME = model_id  # simplest: same as experiment/model_id
        model_uri = f"runs:/{run.info.run_id}/registry_model"
        _ = safe_register_model(model_uri=model_uri, registered_name=REGISTERED_MODEL_NAME, alias="champion")

        print("MLflow run_id:", run.info.run_id)
        print("Best model:", best_name)
        print("Holdout ROC-AUC:", round(holdout["holdout_roc_auc"], 4))
        print("Best threshold (F1):", round(best_t, 4), "F1:", round(best_f1, 4))
        print("Saved model bundle to:", pkl_path)
        print("Logged registry model uri:", model_uri)


if __name__ == "__main__":
    main()
