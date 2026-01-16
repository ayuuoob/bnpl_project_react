"""
Configuration for UC1: Late Payment Risk Prediction
"""
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]   # .../repo/ML
DATA_DIR = PROJECT_ROOT.parent / "data"              # .../repo/data
SILVER_DIR = DATA_DIR / "silver"
GOLD_DIR = DATA_DIR / "gold"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
MODELS_DIR = ARTIFACTS_DIR / "models"

# Ensure directories exist
SILVER_DIR.mkdir(parents=True, exist_ok=True)
GOLD_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Data files (Silver layer - raw CSVs)
SILVER_FILES = {
    "users": SILVER_DIR / "users.csv",
    "orders": SILVER_DIR / "orders.csv",
    "installments": SILVER_DIR / "installments.csv",
    "payments": SILVER_DIR / "payments.csv",
    "disputes": SILVER_DIR / "disputes.csv",
    "refunds": SILVER_DIR / "refunds.csv",
    "merchants": SILVER_DIR / "merchants.csv",
    "checkout_events": SILVER_DIR / "checkout_events.csv",
}

# Gold file (engineered features)
GOLD_UC1_FILE = GOLD_DIR / "gold_uc1_features.csv"

# Feature definitions
GOLD_UC1_FEATURES = [
    "account_age_days", "kyc_level_num", "account_status_num", "user_trust_score", "user_city",
    "late_payment_rate_90d", "avg_late_days_90d", "max_late_days_90d", "on_time_payment_rate_90d",
    "num_active_plans", "repayment_severity_score", "load_pressure_score",
    "total_orders_30d", "avg_order_amount_30d", "max_order_amount_30d", "sum_order_amount_30d",
    "spend_pressure_score", "currency",
    "dispute_count_90d", "refund_count_90d", "context_friction_score",
    "checkout_start_30d", "checkout_success_30d", "checkout_abandon_30d",
    "checkout_abandon_rate_30d", "checkout_friction_score",
    "merchant_status_num", "merchant_dispute_rate_90d", "merchant_refund_rate_90d", "merchant_risk_score",
    "category", "city_merchant"
]

# (Optional but recommended) Training features (drop constants)
FEATURES_FOR_MODEL = [f for f in GOLD_UC1_FEATURES if f not in ["currency", "merchant_status_num"]]

# ID columns
ID_COLS = ["installment_id", "order_id", "user_id", "merchant_id", "installment_number", "anchor_date"]

# Target
TARGET = "is_late"

# Model hyperparameters
RANDOM_STATE = 42
TEST_SIZE = 0.2
CV_FOLDS = 5

# MLflow
MLFLOW_TRACKING_URI = f"file:{(PROJECT_ROOT / 'mlruns').resolve()}"
MLFLOW_EXPERIMENT_NAME = "uc1_late_payment_risk"
