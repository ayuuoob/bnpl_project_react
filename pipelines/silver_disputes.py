import json
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRONZE_PATH = PROJECT_ROOT / "data" / "bronze" / "bnpl_events.json"
SILVER_PATH = PROJECT_ROOT / "data" / "silver"
DISPUTES_PATH = SILVER_PATH / "disputes.csv"

def load_bronze_events():
    events = []
    with open(BRONZE_PATH, "r", encoding="utf-8") as f:
        for line in f:
            events.append(json.loads(line))
    df = pd.DataFrame(events)
    df["ts"] = pd.to_datetime(df["ts"])
    return df

def build_disputes(df: pd.DataFrame) -> pd.DataFrame:
    # Filter for dispute events
    disputes = df[df["event_type"] == "DISPUTE"].copy()
    
    if disputes.empty:
        print("No DISPUTE events found.")
        return pd.DataFrame(columns=["dispute_id", "order_id", "user_id", "merchant_id", "dispute_date", "reason", "status"])

    # Extract fields
    disputes["reason"] = disputes["payload_json"].apply(lambda x: x.get("dispute_reason"))
    # disputes["status"] = "open" # Default status or derive?
    # Schema has 'status'. The payload doesn't seem to have it.
    # In one example payload: {"dispute_reason": "refund", "dispute_amount": 1691}
    # We can default to "open".
    disputes["status"] = "open"

    disputes["dispute_id"] = disputes["event_id"].apply(lambda x: "disp_" + x.split("_")[-1])
    
    # Rename ts
    disputes = disputes.rename(columns={"ts": "dispute_date"})
    
    # Select columns
    disputes = disputes[[
        "dispute_id",
        "order_id",
        "user_id",
        "merchant_id",
        "dispute_date",
        "reason",
        "status"
    ]]
    
    return disputes

def main():
    SILVER_PATH.mkdir(parents=True, exist_ok=True)
    df_events = load_bronze_events()
    disputes = build_disputes(df_events)
    disputes.to_csv(DISPUTES_PATH, index=False)
    print(f"✅ Silver disputes table created: {DISPUTES_PATH}")

if __name__ == "__main__":
    main()
