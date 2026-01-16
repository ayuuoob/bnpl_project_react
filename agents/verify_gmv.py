"""
Quick verification script to validate agent's GMV calculation.
Run this to compare agent output vs direct pandas calculation.
"""

import pandas as pd
from pathlib import Path

# Load orders data
data_path = Path(__file__).parent.parent / "data" / "silver"
orders = pd.read_csv(data_path / "orders.csv")

print("=" * 60)
print("GMV VERIFICATION")
print("=" * 60)

# Total stats
print(f"\nTotal Orders: {len(orders)}")
print(f"Order Statuses: {orders['status'].value_counts().to_dict()}")

# Calculate GMV (approved orders only)
approved = orders[orders['status'] == 'approved']
gmv = approved['amount'].sum()

print(f"\nApproved Orders: {len(approved)}")
print(f"GMV (SUM of approved amounts): ${gmv:,.2f}")

# Additional stats
print(f"\nAverage Order Value: ${approved['amount'].mean():,.2f}")
print(f"Min Order: ${approved['amount'].min():,.2f}")
print(f"Max Order: ${approved['amount'].max():,.2f}")

# Compare with agent's answer
agent_answer = 4_969_356.00
print(f"\n{'=' * 60}")
print(f"Agent's Answer: ${agent_answer:,.2f}")
print(f"Direct Calculation: ${gmv:,.2f}")
print(f"Match: {'✅ YES' if abs(gmv - agent_answer) < 1 else '❌ NO (difference: ${:,.2f})'.format(abs(gmv - agent_answer))}")
print("=" * 60)
