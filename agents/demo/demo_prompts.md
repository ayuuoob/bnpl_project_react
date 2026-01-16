# Demo Prompts - BNPL Analytics Agent

This document contains 5 demo scenarios to showcase the agent's capabilities.

---

## Demo 1: Growth Analytics

**Query:**
```
What was our GMV last month vs previous month?
```

**Expected Intent:** `growth_analytics`

**Expected Output:**
- GMV comparison with both absolute values
- Percentage change (MoM)
- Top contributing merchants/segments
- Recommendation on growth opportunities

---

## Demo 2: Risk Analysis

**Query:**
```
What is our late payment rate by cohort?
```

**Expected Intent:** `risk`

**Expected Output:**
- Overall late rate
- Breakdown by signup cohort
- Identification of underperforming cohorts
- Recommendations for collections strategy

---

## Demo 3: Merchant Performance

**Query:**
```
Which merchants have the highest dispute rates?
```

**Expected Intent:** `merchant_perf`

**Expected Output:**
- Top merchants ranked by dispute rate
- Dispute counts and amounts
- Recommendations for merchant management

---

## Demo 4: Funnel Analysis

**Query:**
```
What is our checkout to approval conversion rate?
```

**Expected Intent:** `funnel`

**Expected Output:**
- Conversion rate at each funnel step
- Drop-off identification
- Recommendations for conversion optimization

---

## Demo 5: Delinquency Buckets

**Query:**
```
How many users are in each delinquency bucket (1-7, 8-30, 30+)?
```

**Expected Intent:** `risk`

**Expected Output:**
- Count per bucket
- Percentage distribution
- Total late amount
- Recommendations for early intervention

---

## Running Demos

```bash
# Run all demos
python -m src.main --demo

# Run single query
python -m src.main --query "What was our GMV last month?"

# Interactive mode
python -m src.main --interactive
```
