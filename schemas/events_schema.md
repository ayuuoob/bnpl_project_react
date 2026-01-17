# BNPL Event Schema (Data Contract)

This document defines all events emitted by the BNPL application.
All pipelines, simulations, ML models, dashboards, and agents
must respect this schema.

---

## Common Fields (for ALL events)

- event_id (string, UUID)
- event_type (string)
- ts (timestamp, UTC)
- user_id (string)
- merchant_id (string, nullable)
- order_id (string, nullable)
- device_id (string, nullable)
- city (string, nullable)
- payload_json (JSON)

---

## Event Types

### 1. SIGNUP
Triggered when a user creates an account.

payload_json:
- signup_channel (web / mobile)
- referral_code (nullable)

---

### 2. KYC_OK
Triggered when KYC is successfully completed.

payload_json:
- kyc_level (basic / full)
- verification_provider

---



### 4. ORDER_OK
BNPL order approved.

payload_json:
- amount
- currency
- installments_count
- credit_limit_used

---

### 5. ORDER_REJ
BNPL order rejected.

payload_json:
- rejection_reason (risk / limit / fraud)

---

### 6. INST_DUE
Installment becomes due.

payload_json:
- installment_id
- due_date
- installment_amount

---

### 7. INST_PAID
Installment paid.

payload_json:
- installment_id
- paid_date
- installment_amount
- payment_channel

---

### 8. INST_LATE
Installment marked late.

payload_json:
- installment_id
- due_date
- late_days

---

### 9. DISPUTE
User opens a dispute or return.

payload_json:
- dispute_reason
- dispute_amount
