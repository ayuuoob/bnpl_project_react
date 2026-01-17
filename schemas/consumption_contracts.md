# Data Consumption Contracts – BNPL Intelligent Analytics

## 1. Project Overview & Objective
**BNPL Intelligent Analytics** is a data platform designed to transform raw transactional events into trustworthy, high-value insights.

**Primary Goal**: Enable data-driven decision-making for:
- **Risk Management**: Detecting late payments and fraud early.
- **Business Growth**: Monitoring GMV, approval rates, and merchant performance.
- **AI Integration**: Empowering AI Agents to answer natural language queries about business health.

---

## 2. Authorized Consumers

Data is served exclusively from the **Gold Layer**. Direct access to Bronze or Silver is restricted to Data Engineering pipelines.

### A. Executive & Risk Dashboards (BI)
*Visualizing the health of the BNPL portfolio.*

- **Source**: `gold_orders_analytics`
- **Key Metrics**:
    - **GMV**: Total volume of approved orders.
    - **Approval Rate**: `count(status='approved') / count(total)`.
    - **Delinquency Rate**: `% orders with late_installments > 0`.
    - **Dispute Rate**: `% orders with has_dispute = 1`.
- **Refresh**: Daily (T+1).

### B. Merchant Analytics Portal
*Empowering merchants with insights.*

- **Source**: `gold_orders_analytics`, `merchant_features_daily` (future)
- **Scope**: Filtered by `merchant_id`.
- **Insights**:
    - Sales volume trends.
    - Customer repayment behavior (Risk of their specific customer base).

### C. Credit Risk Models (ML)
*Predicting user default probability.*

- **Source**: `user_features_daily`, `labels`
- **Target**: `late_next_30d` (as defined in `labels.md`).
- **Features**: 
    - Payment history (on-time streaks).
    - Debt-to-income proxies (active installment burden).

### D. AI Copilot (GenAI Agents)
*Answering ad-hoc business questions.*

- **Source**: All Gold Tables
- **Interface**: Text-to-SQL or Semantic Layer.
- **Capabilities**:
    - "Show me the top 5 merchants by dispute rate."
    - "Why is approval rate dropping in Casablanca?"
- **Constraint**: Must cite the specific Gold table used in the answer.

---

## 3. Data Interface & SLA

| Consumer | Interface | Latency | Reliability |
| :--- | :--- | :--- | :--- |
| **Dashboards** | SQL / JDBC | Daily Batch | High (99.9%) |
| **ML Training** | Parquet / Feature Store | Weekly/Daily | High (Data consistency critical) |
| **AI Agents** | Vector Store / API | Near-Real-Time (Metadata) | Medium (Best effort interpretation) |

---

## 4. Governance & Compliance

1.  **Read-Only Access**: Consumers cannot modify data.
2.  **Privacy**: PII (Personally Identifiable Information) in `users` table is masked for non-admin roles.
3.  **Source of Truth**: If a metric conflicts between a Dashboard and an AI Agent, the Dashboard (SQL definition) is the master definition.
