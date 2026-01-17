# Silver Layer – Clean Operational Tables

Silver tables are cleaned, normalized representations of BNPL business entities.
They are derived from Bronze events and are trusted across BI, ML, and AI agents.

The schema below reflects the source-of-truth CSV files located in `data/silver/`.

---

## users

- user_id (string)
- signup_date (date)
- kyc_level (string)
- city (string)
- account_status (string)
- created_at (timestamp)
- updated_at (timestamp)

---

## merchants

- merchant_id (string)
- merchant_name (string)
- category (string)
- city (string)
- merchant_status (string)
- created_at (timestamp)
- updated_at (timestamp)

---

## orders

- order_id (string)
- user_id (string)
- merchant_id (string)
- order_date (date)
- amount (float)
- currency (string)
- installments_count (int)
- status (string)

---

## installments

- installment_id (string)
- order_id (string)
- user_id (string)
- merchant_id (string)
- installment_number (int)
- due_date (date)
- paid_date (date, nullable)
- status (string)
- late_days (float, nullable)

---

## payments

- payment_id (string)
- installment_id (string)
- order_id (string)
- user_id (string)
- merchant_id (string)
- payment_date (date)
- amount (float)
- payment_channel (string)
- status (string)

---

## disputes

- dispute_id (string)
- order_id (string)
- user_id (string)
- merchant_id (string)
- dispute_date (date)
- reason (string)
- status (string)

---

## refunds

- refund_id (string)
- order_id (string)
- user_id (string)
- merchant_id (string)
- refund_date (date)
- amount (float)

---

## checkout_events

- checkout_event_id (string)
- order_id (string)
- user_id (string)
- event_type (string)
- event_date (timestamp)
