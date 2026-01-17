import json
import pandas as pd
from pathlib import Path
import uuid

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRONZE_PATH = PROJECT_ROOT / "data" / "bronze" / "bnpl_events.json"
SILVER_PATH = PROJECT_ROOT / "data" / "silver"
PAYMENTS_PATH = SILVER_PATH / "payments.csv"

def load_bronze_events():
    events = []
    with open(BRONZE_PATH, "r", encoding="utf-8") as f:
        for line in f:
            events.append(json.loads(line))
    df = pd.DataFrame(events)
    df["ts"] = pd.to_datetime(df["ts"])
    return df

def build_payments(df: pd.DataFrame) -> pd.DataFrame:
    # Filter for payment events
    payments = df[df["event_type"] == "INST_PAID"].copy()
    
    # Extract fields
    payments["installment_id"] = payments["payload_json"].apply(lambda x: x.get("installment_id"))
    payments["amount"] = payments["payload_json"].apply(lambda x: x.get("installment_amount"))
    payments["payment_channel"] = payments["payload_json"].apply(lambda x: x.get("payment_channel"))
    
    # Generate payment_id (using event_id as proxy or generating new unique one)
    # Using event_id is safer for idempotency if one event = one payment
    payments["payment_id"] = payments["event_id"].apply(lambda x: "pay_" + x.split("_")[-1])

    # Status: Assuming "success" for all INST_PAID. If there are failed payments, logic needed.
    # Event implies paid, so status="paid" or "success". Schema has 'status'.
    payments["status"] = "success"

    # Rename ts to payment_date
    payments = payments.rename(columns={"ts": "payment_date"})
    
    # Select columns matching schema
    # payment_id, installment_id, order_id, user_id, merchant_id, payment_date, amount, payment_channel, status
    payments = payments[[
        "payment_id",
        "installment_id",
        "order_id",
        "user_id",
        "merchant_id",
        "payment_date",
        "amount",
        "payment_channel",
        "status"
    ]]
    
    return payments

def main():
    SILVER_PATH.mkdir(parents=True, exist_ok=True)
    df_events = load_bronze_events()
    payments = build_payments(df_events)
    payments.to_csv(PAYMENTS_PATH, index=False)
    print(f"✅ Silver payments table created: {PAYMENTS_PATH}")

if __name__ == "__main__":
    main()
