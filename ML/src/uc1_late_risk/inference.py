"""
UC1 - Inference / Scoring / Explainability

- Loads ONE saved model bundle (RiskModelBundle) produced by train.py (local .pkl bundle)
  OR loads a bundle-like object from MLflow Model Registry (pipeline.joblib + meta.json)
- Predicts probability + binary late-risk using saved threshold
- Optional local explainability (LogReg only): coef * value in log-odds space
- Batch scoring to CSV
- Agent-ready JSONL: one line per row with risk + reason codes + (optional) top factors

Expected LOCAL bundle fields (saved with joblib):
  - bundle.model_id: str
  - bundle.model_name: str
  - bundle.pipeline: sklearn Pipeline (prep + model)
  - bundle.risk_threshold: float
  - bundle.feature_names: list[str]

Registry model expectation (recommended):
  - The registered model contains artifacts:
      - pipeline.joblib  (sklearn Pipeline)
      - meta.json        (dict with model_id, model_name, risk_threshold, features)
  If names differ, this file tries to find reasonable alternatives by searching recursively.
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, Iterable, List, Optional, Tuple

import joblib
import mlflow
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline


# ============================================================
# Bundle loading (local)
# ============================================================
def load_bundle(pkl_path: str | Path):
    """Load the saved RiskModelBundle (joblib/pickle)."""
    return joblib.load(str(pkl_path))


def load_bundle_by_model_id(models_dir: str | Path, model_id: str) -> Tuple[Any, Path]:
    """
    Find and load exactly one bundle in models_dir that matches bundle.model_id == model_id.
    Returns: (bundle, path)
    """
    models_dir = Path(models_dir)
    if not models_dir.exists():
        raise FileNotFoundError(f"models_dir not found: {models_dir}")

    candidates = list(models_dir.glob("*.pkl"))
    if not candidates:
        raise FileNotFoundError(f"No .pkl bundles found in: {models_dir}")

    matches: List[Tuple[Path, Any]] = []
    for p in candidates:
        try:
            b = joblib.load(str(p))
            if getattr(b, "model_id", None) == model_id:
                matches.append((p, b))
        except Exception:
            continue

    if not matches:
        raise ValueError(f"No bundle with model_id='{model_id}' found in {models_dir}")

    if len(matches) > 1:
        raise ValueError(
            f"Multiple bundles with model_id='{model_id}' found:\n"
            + "\n".join(str(m[0]) for m in matches)
        )

    return matches[0][1], matches[0][0]


def validate_model_id(bundle, expected_model_id: Optional[str]):
    """Optional safety check to prevent using the wrong model."""
    if expected_model_id is None:
        return
    got = getattr(bundle, "model_id", None)
    if got != expected_model_id:
        raise ValueError(f"Wrong model loaded: expected model_id='{expected_model_id}', got '{got}'")


# ============================================================
# Bundle loading (MLflow Model Registry)
# ============================================================
def _find_first(root: Path, patterns: List[str]) -> Optional[Path]:
    for pat in patterns:
        hits = list(root.rglob(pat))
        if hits:
            # deterministic-ish
            hits = sorted(hits, key=lambda p: str(p))
            return hits[0]
    return None


def load_bundle_from_registry(
    registered_model_name: str,
    *,
    stage: Optional[str] = None,
    alias: Optional[str] = "champion",
    tracking_uri: Optional[str] = None,
) -> Tuple[Any, str]:
    """
    Loads a model from MLflow Model Registry and returns (bundle_like, model_uri).

    bundle_like fields:
      - model_id, model_name, pipeline, risk_threshold, feature_names

    Use either:
      - alias="champion" (recommended)
      - OR stage="Production"/"Staging"
    """
    if tracking_uri:
        mlflow.set_tracking_uri(tracking_uri)

    if alias:
        model_uri = f"models:/{registered_model_name}@{alias}"
    else:
        if not stage:
            raise ValueError("Provide either alias or stage")
        model_uri = f"models:/{registered_model_name}/{stage}"

    # Download model directory locally (MLflow API differs by version)
    try:
        local_dir_str = mlflow.artifacts.download_artifacts(model_uri=model_uri)
    except TypeError:
        # Older MLflow uses artifact_uri instead of model_uri
        local_dir_str = mlflow.artifacts.download_artifacts(artifact_uri=model_uri)

    local_dir = Path(local_dir_str)

    # Try to find expected artifacts anywhere under downloaded dir
    pipeline_path = _find_first(local_dir, ["pipeline.joblib", "pipeline.pkl", "*.joblib", "*.pkl"])
    meta_path = _find_first(local_dir, ["meta.json", "model_contract.json", "*contract*.json"])

    if pipeline_path is None or meta_path is None:
        raise FileNotFoundError(
            "Registry model is missing expected artifacts.\n"
            f"Downloaded dir: {local_dir}\n"
            f"Found pipeline: {pipeline_path}\n"
            f"Found meta: {meta_path}\n"
            "Recommendation: in train.py registry logging, store artifacts named exactly "
            "'pipeline.joblib' and 'meta.json'."
        )

    pipeline = joblib.load(str(pipeline_path))
    meta = json.loads(meta_path.read_text(encoding="utf-8"))

    # Build bundle-like object to reuse existing inference functions
    bundle = SimpleNamespace(
        model_id=meta.get("model_id"),
        model_name=meta.get("model_name"),
        pipeline=pipeline,
        risk_threshold=float(meta["risk_threshold"]),
        feature_names=list(meta.get("features", meta.get("feature_names", []))),
    )

    if not bundle.feature_names:
        raise ValueError(f"Registry meta file does not include 'features' / 'feature_names': {meta_path}")

    return bundle, model_uri


# ============================================================
# Input validation
# ============================================================
def ensure_features(df: pd.DataFrame, feature_names: List[str]) -> pd.DataFrame:
    """
    Ensure df contains ALL required features.
    - Raises if missing.
    - Returns a copy with columns ordered exactly.
    """
    missing = [c for c in feature_names if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required features: {missing}")

    return df.loc[:, feature_names].copy()


# ============================================================
# Core prediction
# ============================================================
def predict_proba(bundle, X: pd.DataFrame) -> np.ndarray:
    Xc = ensure_features(X, bundle.feature_names)
    return bundle.pipeline.predict_proba(Xc)


def predict_binary(bundle, X: pd.DataFrame) -> np.ndarray:
    proba = predict_proba(bundle, X)[:, 1]
    return (proba >= float(bundle.risk_threshold)).astype(int)


# ============================================================
# EXPLAINABILITY (LogReg-only coef*value)
# ============================================================
def _get_lr_from_pipeline(pipe: Pipeline):
    """Return underlying LogisticRegression if present (supports CalibratedClassifierCV)."""
    model = pipe.named_steps.get("model")
    if model is None:
        return None

    if hasattr(model, "calibrated_classifiers_"):
        try:
            return model.calibrated_classifiers_[0].estimator
        except Exception:
            return None

    return model


def get_transformed_feature_names(pipe: Pipeline) -> np.ndarray:
    prep = pipe.named_steps.get("prep")
    if prep is None or not hasattr(prep, "get_feature_names_out"):
        return np.array([], dtype=object)
    return prep.get_feature_names_out()


def explain_one(pipe: Pipeline, X_row: pd.DataFrame, top_k: int = 8):
    """
    Local explanation for ONE row:
      contribution_j = coef_j * x_j (in transformed/model space)
    Returns:
      p, logit, top_factors(list)
    """
    prep = pipe.named_steps.get("prep")
    lr = _get_lr_from_pipeline(pipe)

    # not compatible => proba only
    if prep is None or lr is None or not hasattr(lr, "coef_"):
        p = float(pipe.predict_proba(X_row)[:, 1][0])
        return p, None, []

    Xt = prep.transform(X_row)
    Xt_dense = Xt.toarray().ravel() if hasattr(Xt, "toarray") else np.array(Xt).ravel()

    coefs = lr.coef_.ravel()
    intercept = float(np.ravel(lr.intercept_)[0])

    contrib = Xt_dense * coefs
    logit = intercept + float(contrib.sum())
    p = float(pipe.predict_proba(X_row)[:, 1][0])

    feat_names = get_transformed_feature_names(pipe)
    if feat_names is None or len(feat_names) == 0:
        feat_names = np.array([f"f_{i}" for i in range(len(contrib))], dtype=object)

    idx = np.argsort(np.abs(contrib))[::-1][:top_k]

    top_factors = []
    for j in idx:
        if Xt_dense[j] == 0:
            continue
        top_factors.append(
            {
                "feature": str(feat_names[j]),
                "direction": "increases_risk" if contrib[j] > 0 else "decreases_risk",
                "contribution_logodds": float(contrib[j]),
                "odds_ratio_per_1std": float(np.exp(coefs[j])),
                "modelspace_value": float(Xt_dense[j]),
            }
        )

    return p, float(logit), top_factors


# ============================================================
# Reason codes (business rules on ORIGINAL feature names)
# ============================================================
REASON_RULES = [
    ("REPEATED_LATE_PAYMENTS", lambda r: r.get("late_payment_rate_90d", 0) >= 0.30),
    ("SEVERE_LATE_BEHAVIOR", lambda r: r.get("max_late_days_90d", 0) >= 15),
    ("POOR_ON_TIME_HISTORY", lambda r: r.get("on_time_payment_rate_90d", 1.0) <= 0.70),
    ("HIGH_LOAD", lambda r: r.get("num_active_plans", 0) >= 2),
    ("HIGH_SPEND_PRESSURE", lambda r: r.get("spend_pressure_score", 0) >= 1.0),
    ("LOW_KYC", lambda r: r.get("kyc_level_num", 0) <= 1),
    ("LOW_TRUST_SCORE", lambda r: r.get("user_trust_score", 999) <= 1),
]


def build_reason_codes(X_row: pd.DataFrame) -> List[str]:
    r = X_row.iloc[0].to_dict()
    codes = [code for code, rule in REASON_RULES if rule(r)]
    return codes if codes else ["MODEL_SIGNAL_ONLY"]


# ============================================================
# Recommendations (optional)
# ============================================================
def limit_recommendation(is_risky: int, base_limit: float):
    if not is_risky:
        return "KEEP", float(base_limit), 1.0
    return "DECREASE", float(round(base_limit * 0.4, 2)), 0.4


# ============================================================
# FINAL PAYLOAD (binary risk + optional explainability)
# ============================================================
def predict_with_explainability_binary(
    bundle,
    X_row: pd.DataFrame,
    base_limit: float = 4000.0,
    top_k: int = 8,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Predict + explain for a single 1-row DataFrame."""
    X_row = ensure_features(X_row, bundle.feature_names)

    pipe = bundle.pipeline
    threshold = float(bundle.risk_threshold)

    p, logit, top_factors = explain_one(pipe, X_row, top_k=top_k)
    is_risky = int(p >= threshold)
    margin = float(p - threshold)

    reason_codes = build_reason_codes(X_row)
    limit_action, suggested_limit, multiplier = limit_recommendation(is_risky, base_limit)

    summary = [f"{f['feature']} {f['direction']}" for f in top_factors[:3]] if top_factors else []

    payload = {
        "request_id": request_id,
        "model": {
            "model_id": getattr(bundle, "model_id", None),
            "model_name": getattr(bundle, "model_name", None),
        },
        "risk": {
            "probability_late_30d": float(p),
            "risk_threshold": float(threshold),
            "is_risky_late": int(is_risky),
            "margin_vs_threshold": float(margin),
        },
        "explainability": {
            "method": "logreg_coef_x_value" if (top_factors or logit is not None) else "not_available_for_model",
            "reason_code": reason_codes,
            "logit": logit,
            "top_factors": top_factors,
            "summary": summary,
        },
        "recommendations": {
            "limit_adjustment": {
                "apply_if_risky": True,
                "recommendation": limit_action,
                "current_limit": float(base_limit),
                "suggested_limit": float(suggested_limit),
                "multiplier": float(multiplier),
                "reason": "Risk-based exposure control",
            }
        },
    }
    return payload


# ============================================================
# Batch scoring utilities (CSV)
# ============================================================
def score_dataframe(bundle, df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds:
      - model_id, model_name
      - proba_late_30d, risk_threshold, is_risky_late, margin_vs_threshold
    """
    X = ensure_features(df, bundle.feature_names)
    proba = bundle.pipeline.predict_proba(X)[:, 1].astype(float)
    thr = float(bundle.risk_threshold)
    pred = (proba >= thr).astype(int)
    margin = (proba - thr).astype(float)

    out = df.copy()
    out["model_id"] = getattr(bundle, "model_id", None)
    out["model_name"] = getattr(bundle, "model_name", None)
    out["proba_late_30d"] = proba
    out["risk_threshold"] = thr
    out["is_risky_late"] = pred
    out["margin_vs_threshold"] = margin
    return out


def score_csv(bundle, input_csv: str | Path, output_csv: str | Path) -> Path:
    df = pd.read_csv(str(input_csv))
    scored = score_dataframe(bundle, df)
    out_path = Path(output_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    scored.to_csv(out_path, index=False)
    return out_path


# ============================================================
# Batch payload writing (JSONL) for Agent
# ============================================================
def _safe_json_default(obj):
    """JSON serializer for objects not serializable by default json.dumps()."""
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.ndarray,)):
        return obj.tolist()
    if isinstance(obj, (pd.Timestamp,)):
        return obj.isoformat()
    if isinstance(obj, (_dt.date, _dt.datetime)):
        return obj.isoformat()
    return str(obj)


def iter_payloads(
    bundle,
    df_scoring: pd.DataFrame,
    *,
    id_cols: Optional[List[str]] = None,
    only_risky: bool = True,
    base_limit: float = 4000.0,
    top_k: int = 8,
    request_id_prefix: str = "batch",
) -> Iterable[Dict[str, Any]]:
    """
    Yields explainability payload dicts for each row in df_scoring.

    - only_risky=True: yields only risky rows based on bundle.risk_threshold
    - id_cols: columns copied into payload["context"]["ids"]
    """
    if id_cols is None:
        id_cols = []

    for i in range(len(df_scoring)):
        full_row = df_scoring.iloc[[i]]  # 1-row DF

        # early filter for speed
        if only_risky:
            Xf = ensure_features(full_row, bundle.feature_names)
            p = float(bundle.pipeline.predict_proba(Xf)[:, 1][0])
            if p < float(bundle.risk_threshold):
                continue

        payload = predict_with_explainability_binary(
            bundle=bundle,
            X_row=full_row,
            request_id=f"{request_id_prefix}_{i}",
            base_limit=float(base_limit),
            top_k=int(top_k),
        )

        # Attach ids / context
        ids: Dict[str, Any] = {}
        for c in id_cols:
            if c in full_row.columns:
                v = full_row.iloc[0][c]
                ids[c] = None if pd.isna(v) else v

        payload["context"] = payload.get("context", {})
        payload["context"]["ids"] = ids

        for c in ["due_date", "anchor_date", "status", "installment_number"]:
            if c in full_row.columns:
                v = full_row.iloc[0][c]
                payload["context"][c] = None if pd.isna(v) else v

        yield payload


def write_explanations_jsonl(
    bundle,
    df_scoring: pd.DataFrame,
    out_jsonl: str | Path,
    *,
    id_cols: Optional[List[str]] = None,
    only_risky: bool = True,
    base_limit: float = 4000.0,
    top_k: int = 8,
    request_id_prefix: str = "batch",
) -> Path:
    """Writes JSONL file where each line is one payload dict (agent-ready)."""
    out_path = Path(out_jsonl)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    n_written = 0
    with out_path.open("w", encoding="utf-8") as f:
        for payload in iter_payloads(
            bundle,
            df_scoring,
            id_cols=id_cols,
            only_risky=only_risky,
            base_limit=base_limit,
            top_k=top_k,
            request_id_prefix=request_id_prefix,
        ):
            f.write(json.dumps(payload, ensure_ascii=False, default=_safe_json_default) + "\n")
            n_written += 1

    print(f"[write_explanations_jsonl] wrote {n_written} payloads to {out_path}")
    return out_path


# ============================================================
# CLI
# ============================================================
def main():
    import argparse

    parser = argparse.ArgumentParser(description="UC1 BNPL late-payment risk inference")

    # --- Choose ONE loading mode ---
    # (A) Local bundle path
    parser.add_argument("--model", type=str, default=None, help="Path to *.bundle.pkl")

    # (B) Local folder by model_id
    parser.add_argument("--models_dir", type=str, default=None, help="Folder containing bundles (*.pkl)")
    parser.add_argument("--model_id", type=str, default=None, help="Load local bundle by model_id")

    # (C) MLflow Registry
    parser.add_argument("--registry_name", type=str, default=None, help="MLflow registered model name")
    parser.add_argument("--registry_alias", type=str, default="champion", help="Registry alias (default: champion)")
    parser.add_argument("--registry_stage", type=str, default=None, help="Registry stage (Production/Staging)")
    parser.add_argument("--tracking_uri", type=str, default=None, help="Override MLflow tracking URI")

    # Optional safety check
    parser.add_argument("--expect_model_id", type=str, default=None, help="Fail if loaded model_id != this")

    # Inputs/outputs
    parser.add_argument("--input", type=str, required=True, help="CSV input to score")
    parser.add_argument("--output", type=str, required=True, help="CSV output path")

    # Single-row explain
    parser.add_argument("--explain_row", type=int, default=None, help="Row index to explain (optional)")

    # Recommendations / explainability
    parser.add_argument("--base_limit", type=float, default=4000.0, help="Base credit limit for recommendations")
    parser.add_argument("--top_k", type=int, default=8, help="Top K factors for local explanation (LogReg only)")

    # Agent JSONL
    parser.add_argument("--explanations_jsonl", type=str, default=None, help="If set, write explanations JSONL here")
    parser.add_argument("--only_risky", action="store_true", help="If set, JSONL includes only risky rows")
    parser.add_argument("--id_cols", type=str, default="", help="Comma-separated id cols for payload context.ids")

    args = parser.parse_args()

    # ---- Load bundle ----
    bundle = None

    if args.registry_name:
        # prefer alias unless user forces stage
        alias = args.registry_alias if args.registry_alias else None
        stage = args.registry_stage
        if stage and alias:
            # if both provided, stage wins only if alias is empty; keep it simple:
            pass
        bundle, model_uri = load_bundle_from_registry(
            registered_model_name=args.registry_name,
            alias=alias,
            stage=stage,
            tracking_uri=args.tracking_uri,
        )
        print("Loaded bundle from registry:", model_uri)

    elif args.model_id:
        if not args.models_dir:
            raise ValueError("If you pass --model_id, you must also pass --models_dir")
        bundle, found_path = load_bundle_by_model_id(args.models_dir, args.model_id)
        print("Loaded local bundle:", found_path)

    else:
        if not args.model:
            raise ValueError("Provide --model (path) OR (--model_id + --models_dir) OR --registry_name")
        bundle = load_bundle(args.model)
        print("Loaded local bundle:", args.model)

    validate_model_id(bundle, args.expect_model_id)

    # ---- Score CSV ----
    out_path = score_csv(bundle, args.input, args.output)
    print("Saved scored CSV to:", out_path)

    # ---- Write JSONL for agent ----
    if args.explanations_jsonl:
        df_in = pd.read_csv(args.input)
        id_cols = [c.strip() for c in args.id_cols.split(",") if c.strip()]
        write_explanations_jsonl(
            bundle=bundle,
            df_scoring=df_in,
            out_jsonl=args.explanations_jsonl,
            only_risky=bool(args.only_risky),
            id_cols=id_cols,
            base_limit=float(args.base_limit),
            top_k=int(args.top_k),
            request_id_prefix="cli",
        )

    # ---- Explain one row ----
    if args.explain_row is not None:
        df = pd.read_csv(args.input)
        row = df.iloc[[args.explain_row]]
        payload = predict_with_explainability_binary(
            bundle,
            row,
            request_id=f"row_{args.explain_row}",
            base_limit=float(args.base_limit),
            top_k=int(args.top_k),
        )
        print(json.dumps(payload, indent=2, ensure_ascii=False, default=_safe_json_default))


if __name__ == "__main__":
    main()
