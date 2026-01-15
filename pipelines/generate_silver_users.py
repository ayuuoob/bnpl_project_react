# scripts/generate_silver_checkout_events.py

import pandas as pd
import random
from datetime import timedelta

# ------------------
# LOAD DATA
# ------------------
orders = pd.read_csv("data/silver/orders.csv", parse_dates=["order_date"])
users = pd.read_csv("data/silver/users.csv")

orders = orders.merge(
    users[["user_id", "kyc_level", "account_status"]],
    on="user_id",
    how="left"
)

rows = []
checkout_counter = 1

for _, o in orders.iterrows():

    if o.account_status in ["blocked", "closed"]:
        continue

    start_time = o.order_date

    rows.append({
        "checkout_event_id": f"chk_{checkout_counter:07d}",
        "order_id": o.order_id,
        "user_id": o.user_id,
        "event_type": "checkout_start",
        "event_date": start_time
    })
    checkout_counter += 1

    abandon_prob = 0.05

    if o.kyc_level == "basic":
        abandon_prob += 0.15
    if o.account_status == "suspended":
        abandon_prob += 0.25
    if o.status == "rejected":
        abandon_prob += 0.40

    if random.random() < abandon_prob:
        rows.append({
            "checkout_event_id": f"chk_{checkout_counter:07d}",
            "order_id": o.order_id,
            "user_id": o.user_id,
            "event_type": "checkout_abandon",
            "event_date": start_time + timedelta(minutes=2)
        })
        checkout_counter += 1
        continue

    rows.append({
        "checkout_event_id": f"chk_{checkout_counter:07d}",
        "order_id": o.order_id,
        "user_id": o.user_id,
        "event_type": "checkout_success",
        "event_date": start_time + timedelta(minutes=3)
    })
    checkout_counter += 1

df_checkout = pd.DataFrame(rows)

df_checkout.to_csv("data/silver/checkout_events.csv", index=False)

print("✅ silver_checkout_events generated:", len(df_checkout))
