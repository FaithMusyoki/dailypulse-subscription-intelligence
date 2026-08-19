# DAILYPULSE MEDIA

## Subscription Intelligence — Data Dictionary

**Project:** DAILYPULSE Subscription Intelligence

**Version:** 1.0

**Database:** PostgreSQL

---

## 1. Purpose

This document defines the data fields, relationships, allowed values and business rules for the DAILYPULSE MEDIA Subscription Intelligence database.

The v1 database contains 12 core tables:

1. `customers`
2. `products`
3. `plans`
4. `subscriptions`
5. `subscription_events`
6. `payments`
7. `organisations`
8. `organisation_users`
9. `marketing_touchpoints`
10. `trials`
11. `customer_engagement`
12. `support_interactions`

The model is designed to preserve historical subscription behaviour while supporting revenue, retention, lifecycle, marketing, organisation and customer intelligence analysis.

---

# 2. CUSTOMERS

Represents individual registered DAILYPULSE MEDIA users.

| Column           | Data Type | Required | Key    | Description                                    |
| ---------------- | --------- | -------: | ------ | ---------------------------------------------- |
| `customer_id`    | VARCHAR   |      Yes | PK     | Unique customer identifier                     |
| `first_name`     | VARCHAR   |      Yes |        | Customer first name                            |
| `last_name`      | VARCHAR   |      Yes |        | Customer surname                               |
| `email`          | VARCHAR   |      Yes | UNIQUE | Registered email address                       |
| `signup_date`    | DATE      |      Yes |        | Date customer created their DAILYPULSE account |
| `country`        | VARCHAR   |      Yes |        | Customer country                               |
| `account_status` | VARCHAR   |      Yes |        | Operational state of the account               |

### Allowed `account_status`

* `active`
* `suspended`
* `closed`

### Business Rules

* Each customer must have one unique `customer_id`.
* Each email address must be unique.
* Account status describes the customer's DAILYPULSE account and does **not** indicate subscription status.
* A customer may have an active account without having an active subscription.
* Subscription activity and churn must not be stored in this table.

---

# 3. PRODUCTS

Represents the products sold by DAILYPULSE MEDIA.

| Column           | Data Type | Required | Key    | Description                            |
| ---------------- | --------- | -------: | ------ | -------------------------------------- |
| `product_id`     | VARCHAR   |      Yes | PK     | Unique product identifier              |
| `product_name`   | VARCHAR   |      Yes | UNIQUE | Commercial product name                |
| `product_family` | VARCHAR   |      Yes |        | Broad product family                   |
| `target_segment` | VARCHAR   |      Yes |        | Primary target customer segment        |
| `is_active`      | BOOLEAN   |      Yes |        | Whether product is currently available |

### Product Catalogue

| Product          | Product Family | Target Segment |
| ---------------- | -------------- | -------------- |
| Digital Basic    | Digital News   | General        |
| Digital Premium  | Digital News   | General        |
| ePaper           | ePaper         | General        |
| Weekend ePaper   | ePaper         | General        |
| Student Digital  | Digital News   | Student        |
| Corporate ePaper | ePaper         | Organisation   |

### Allowed `product_family`

* `Digital News`
* `ePaper`

### Business Rules

* Product records should not be deleted when discontinued.
* Discontinued products should instead use `is_active = FALSE`.
* Pricing does not belong in this table.
* Billing frequency does not belong in this table.

---

# 4. PLANS

Represents purchasable versions of each product.

| Column                | Data Type     | Required | Key    | Description                                       |
| --------------------- | ------------- | -------: | ------ | ------------------------------------------------- |
| `plan_id`             | VARCHAR       |      Yes | PK     | Unique plan identifier                            |
| `product_id`          | VARCHAR       |      Yes | FK     | Product associated with the plan                  |
| `plan_name`           | VARCHAR       |      Yes | UNIQUE | Human-readable subscription plan name             |
| `billing_frequency`   | VARCHAR       |      Yes |        | Billing cadence                                   |
| `billing_period_days` | INTEGER       |      Yes |        | Nominal billing-period duration                   |
| `unit_price`          | DECIMAL(12,2) |      Yes |        | Standard price per subscription or corporate seat |
| `currency`            | VARCHAR       |      Yes |        | Billing currency                                  |
| `is_active`           | BOOLEAN       |      Yes |        | Whether plan can currently be purchased           |

### Allowed `billing_frequency`

* `Daily`
* `Weekly`
* `Monthly`
* `Annual`

### Nominal Billing Periods

| Billing Frequency | Days |
| ----------------- | ---: |
| Daily             |    1 |
| Weekly            |    7 |
| Monthly           |   30 |
| Annual            |  365 |

Calendar logic should be used when calculating actual monthly and annual renewal dates.

### Available Plans

| Product          | Available Billing Frequencies  |
| ---------------- | ------------------------------ |
| Digital Basic    | Daily, Weekly, Monthly, Annual |
| Digital Premium  | Weekly, Monthly, Annual        |
| ePaper           | Daily, Weekly, Monthly, Annual |
| Weekend ePaper   | Weekly, Monthly                |
| Student Digital  | Weekly, Monthly, Annual        |
| Corporate ePaper | Monthly, Annual                |

### Business Rules

* `unit_price` represents the price of one individual subscription for consumer plans.
* For Corporate ePaper, `unit_price` represents the **price per seat**.
* Corporate subscription total value is calculated using the number of seats purchased.
* Product information should be retrieved through `product_id` rather than duplicated.

---

# 5. SUBSCRIPTIONS

Represents one continuous period during which a customer or organisation is subscribed to one specific plan.

| Column                      | Data Type |    Required | Key | Description                                           |
| --------------------------- | --------- | ----------: | --- | ----------------------------------------------------- |
| `subscription_id`           | VARCHAR   |         Yes | PK  | Unique subscription record                            |
| `customer_id`               | VARCHAR   | Conditional | FK  | Individual owner                                      |
| `organisation_id`           | VARCHAR   | Conditional | FK  | Organisation owner                                    |
| `plan_id`                   | VARCHAR   |         Yes | FK  | Purchased subscription plan                           |
| `subscription_start_date`   | DATE      |         Yes |     | Date this plan relationship began                     |
| `current_period_start`      | DATE      |         Yes |     | Start of current billing period                       |
| `current_period_end`        | DATE      |         Yes |     | Scheduled end of current billing period               |
| `subscription_end_date`     | DATE      |          No |     | Actual date this subscription record ended            |
| `status`                    | VARCHAR   |         Yes |     | Current/final state of subscription record            |
| `auto_renew`                | BOOLEAN   |         Yes |     | Whether subscription should renew automatically       |
| `cancellation_requested_at` | TIMESTAMP |          No |     | Timestamp of current outstanding cancellation request |
| `end_reason`                | VARCHAR   |          No |     | Reason this subscription record ended                 |
| `seats_purchased`           | INTEGER   | Conditional |     | Current number of corporate seats                     |
| `created_at`                | TIMESTAMP |         Yes |     | Record creation timestamp                             |

### Allowed `status`

* `active`
* `past_due`
* `ended`

### Allowed `end_reason`

* `plan_change`
* `voluntary_cancel`
* `payment_failure`
* `non_renewal`

### Ownership Rules

A subscription belongs to either:

* one individual customer; or
* one organisation.

It must never belong to both.

For an individual subscription:

```text
customer_id = populated
organisation_id = NULL
```

For an organisation subscription:

```text
customer_id = NULL
organisation_id = populated
```

### Subscription History Rules

* One subscription record represents **one continuous period on one plan**.
* A normal renewal does **not** create a new subscription record.
* A plan change creates a new subscription record.
* Billing-frequency changes count as plan changes.
* Product changes count as plan changes.
* Previous subscription records must never be overwritten.

### Cancellation Rules

A cancellation request represents **churn intent**, not completed churn.

A customer may request cancellation while retaining access until the end of the current billing period.

During this period:

```text
status = active
auto_renew = FALSE
cancellation_requested_at = populated
```

If cancellation is reversed, `cancellation_requested_at` returns to `NULL` and the historical event remains in `subscription_events`.

### Churn Rule

Churn is **derived**, not stored.

It should be determined using:

* the subscription `end_reason`;
* the subscription end date; and
* whether the subscriber subsequently begins another active subscription.

### Corporate Seat Rule

* `seats_purchased` must be `NULL` for individual subscriptions.
* `seats_purchased` is required for Corporate ePaper subscriptions.
* Seat changes do not create a new subscription if the plan itself remains unchanged.

---

# 6. SUBSCRIPTION_EVENTS

Provides the historical audit trail of meaningful changes to a subscription.

| Column                    | Data Type | Required | Key | Description                                   |
| ------------------------- | --------- | -------: | --- | --------------------------------------------- |
| `event_id`                | VARCHAR   |      Yes | PK  | Unique event identifier                       |
| `subscription_id`         | VARCHAR   |      Yes | FK  | Subscription affected                         |
| `event_type`              | VARCHAR   |      Yes |     | Lifecycle event                               |
| `event_at`                | TIMESTAMP |      Yes |     | Exact event timestamp                         |
| `related_subscription_id` | VARCHAR   |       No | FK  | Related subscription where applicable         |
| `triggering_payment_id`   | VARCHAR   |       No | FK  | Payment that triggered the event              |
| `period_start`            | DATE      |       No |     | Billing-period start associated with event    |
| `period_end`              | DATE      |       No |     | Billing-period end associated with event      |
| `previous_seat_count`     | INTEGER   |       No |     | Seat quantity before organisation seat change |
| `new_seat_count`          | INTEGER   |       No |     | Seat quantity after organisation seat change  |
| `event_reason`            | VARCHAR   |       No |     | Additional context                            |
| `created_at`              | TIMESTAMP |      Yes |     | Record creation timestamp                     |

### Allowed `event_type`

* `subscription_started`
* `renewed`
* `cancellation_requested`
* `cancellation_reversed`
* `plan_changed`
* `past_due_started`
* `past_due_resolved`
* `subscription_ended`
* `reactivated`
* `seats_changed`

### Business Rules

* Payment attempts themselves belong in `payments`, not this table.
* Payment-related subscription consequences may reference `triggering_payment_id`.
* `related_subscription_id` should be used where one subscription transitions into another.
* `previous_seat_count` and `new_seat_count` apply only to `seats_changed`.
* Renewal events preserve historical billing periods without creating new subscriptions.
* Churn itself is not stored as an event.

---

# 7. PAYMENTS

Represents individual payment attempts relating to subscriptions.

| Column                  | Data Type     | Required | Key | Description                            |
| ----------------------- | ------------- | -------: | --- | -------------------------------------- |
| `payment_id`            | VARCHAR       |      Yes | PK  | Unique payment attempt                 |
| `subscription_id`       | VARCHAR       |      Yes | FK  | Subscription being charged             |
| `payment_attempted_at`  | TIMESTAMP     |      Yes |     | Exact payment-attempt timestamp        |
| `amount`                | DECIMAL(12,2) |      Yes |     | Total amount attempted                 |
| `currency`              | VARCHAR       |      Yes |     | Transaction currency                   |
| `payment_status`        | VARCHAR       |      Yes |     | Outcome of payment                     |
| `payment_method`        | VARCHAR       |      Yes |     | Method used                            |
| `transaction_reference` | VARCHAR       |       No |     | Payment-provider transaction reference |
| `failure_reason`        | VARCHAR       |       No |     | Reason unsuccessful payment failed     |
| `created_at`            | TIMESTAMP     |      Yes |     | Record creation timestamp              |

### Allowed `payment_status`

* `successful`
* `failed`
* `pending`

### Allowed `payment_method`

* `mobile_money`
* `card`
* `bank_transfer`

### Example `failure_reason`

* `insufficient_funds`
* `expired_card`
* `payment_declined`
* `invalid_payment_details`
* `timeout`
* `other`

### Business Rules

* One row represents one payment attempt.
* Failed attempts must not later be overwritten as successful.
* A retry creates another payment row.
* Revenue should only include successfully collected payments.
* For organisation subscriptions, `amount` represents the **total amount charged for all seats**, not the per-seat rate.
* `failure_reason` should normally be `NULL` for successful payments.

---

# 8. ORGANISATIONS

Represents institutions purchasing Corporate ePaper.

| Column                  | Data Type | Required | Key | Description                         |
| ----------------------- | --------- | -------: | --- | ----------------------------------- |
| `organisation_id`       | VARCHAR   |      Yes | PK  | Unique organisation identifier      |
| `organisation_name`     | VARCHAR   |      Yes |     | Organisation name                   |
| `organisation_type`     | VARCHAR   |      Yes |     | Broad institution type              |
| `industry`              | VARCHAR   |      Yes |     | Sector                              |
| `organisation_size`     | INTEGER   |      Yes |     | Estimated addressable population    |
| `signup_date`           | DATE      |      Yes |     | Date organisation joined DAILYPULSE |
| `billing_contact_name`  | VARCHAR   |      Yes |     | Primary commercial/billing contact  |
| `billing_contact_email` | VARCHAR   |      Yes |     | Billing contact email               |
| `account_status`        | VARCHAR   |      Yes |     | Operational account status          |
| `created_at`            | TIMESTAMP |      Yes |     | Record creation timestamp           |

### Example `organisation_type`

* `Corporate`
* `University`
* `Government`
* `NGO`
* `Professional Association`
* `Other`

### Example `industry`

* `Financial Services`
* `Education`
* `Public Sector`
* `Healthcare`
* `Telecommunications`
* `Manufacturing`
* `Professional Services`
* `Media`
* `Technology`
* `Development`
* `Other`

### Allowed `account_status`

* `active`
* `suspended`
* `closed`

### Organisation Band

`organisation_band` is **derived**, not stored.

Suggested classification:

| Organisation Size | Derived Band |
| ----------------- | ------------ |
| 1–49              | Micro        |
| 50–249            | Small        |
| 250–999           | Medium       |
| 1,000–4,999       | Large        |
| 5,000+            | Enterprise   |

### Business Rules

* Organisation account status does not represent subscription status.
* `organisation_size` represents the estimated population reasonably eligible for access.
* For universities this may include students and staff.
* Organisation subscription history belongs in `subscriptions`.

---

# 9. ORGANISATION_USERS

Represents individual users occupying seats under organisation subscriptions.

| Column                 | Data Type | Required | Key | Description                             |
| ---------------------- | --------- | -------: | --- | --------------------------------------- |
| `organisation_user_id` | VARCHAR   |      Yes | PK  | Unique organisation-user identifier     |
| `organisation_id`      | VARCHAR   |      Yes | FK  | Organisation the user belongs to        |
| `subscription_id`      | VARCHAR   |      Yes | FK  | Corporate subscription providing access |
| `email`                | VARCHAR   |      Yes |     | User access email                       |
| `activation_date`      | DATE      |      Yes |     | Date seat was activated                 |
| `deactivation_date`    | DATE      |       No |     | Date access ended                       |
| `user_status`          | VARCHAR   |      Yes |     | Current seat-user status                |
| `created_at`           | TIMESTAMP |      Yes |     | Record creation timestamp               |

### Allowed `user_status`

* `active`
* `inactive`

### Business Rules

* One active organisation user represents one activated seat.
* Historical users should not be deleted after deactivation.
* `deactivation_date` should be `NULL` while access remains active.
* Seat utilisation is derived by comparing active organisation users with `subscriptions.seats_purchased`.

---

# 10. MARKETING_TOUCHPOINTS

Represents individual customer interactions with acquisition or marketing channels.

| Column            | Data Type     | Required | Key | Description                          |
| ----------------- | ------------- | -------: | --- | ------------------------------------ |
| `touchpoint_id`   | VARCHAR       |      Yes | PK  | Unique marketing interaction         |
| `customer_id`     | VARCHAR       |      Yes | FK  | Customer associated with interaction |
| `touchpoint_at`   | TIMESTAMP     |      Yes |     | Interaction timestamp                |
| `channel`         | VARCHAR       |      Yes |     | Broad acquisition/marketing channel  |
| `campaign_name`   | VARCHAR       |       No |     | Campaign associated with interaction |
| `touchpoint_type` | VARCHAR       |      Yes |     | Type of customer interaction         |
| `attributed_cost` | DECIMAL(12,2) |       No |     | Cost attributed to the interaction   |
| `created_at`      | TIMESTAMP     |      Yes |     | Record creation timestamp            |

### Allowed / Example `channel`

* `Organic Search`
* `Direct`
* `Email`
* `Organic Social`
* `Paid Social`
* `Paid Search`
* `Referral`
* `Affiliate / Partner`
* `Campus Activation`
* `Promotional Campaign`

### Example `touchpoint_type`

* `impression`
* `click`
* `visit`
* `email_open`
* `email_click`
* `referral`
* `campaign_response`

### Business Rules

* One customer may have multiple marketing touchpoints.
* Acquisition channel should not be duplicated in `customers`.
* `attributed_cost = 0` may represent a known zero direct-media cost.
* `NULL` may be used where cost is unknown or not applicable.
* Touchpoints should not directly contain a `subscription_id`.

---

# 11. TRIALS

Tracks the DAILYPULSE 7-day free-trial lifecycle separately from paid subscriptions.

| Column                      | Data Type | Required | Key | Description                                |
| --------------------------- | --------- | -------: | --- | ------------------------------------------ |
| `trial_id`                  | VARCHAR   |      Yes | PK  | Unique trial identifier                    |
| `customer_id`               | VARCHAR   |      Yes | FK  | Customer receiving the trial               |
| `product_id`                | VARCHAR   |      Yes | FK  | Digital News product being trialled        |
| `trial_started_at`          | TIMESTAMP |      Yes |     | Exact time trial begins                    |
| `scheduled_end_at`          | TIMESTAMP |      Yes |     | Maximum scheduled end                      |
| `actual_end_at`             | TIMESTAMP |       No |     | Exact time trial actually ended            |
| `trial_status`              | VARCHAR   |      Yes |     | Current/final trial state                  |
| `converted_subscription_id` | VARCHAR   |       No | FK  | Paid subscription created after conversion |
| `created_at`                | TIMESTAMP |      Yes |     | Record creation timestamp                  |

### Allowed `trial_status`

* `active`
* `converted`
* `expired`
* `cancelled`

### Trial-Eligible Products

* Digital Basic
* Digital Premium
* Student Digital

### Not Trial Eligible

* ePaper
* Weekend ePaper
* Corporate ePaper

### Business Rules

* Maximum trial duration = **7 days**.
* One free trial per individual customer.
* Organisations are not eligible.
* A trial may end earlier through conversion or cancellation.
* `converted_subscription_id` is populated only when the trial converts.
* Trial activity is not stored as a paid subscription event.

---

# 12. CUSTOMER_ENGAGEMENT

Stores daily engagement behaviour for individual customers.

One row represents one customer's recorded DAILYPULSE activity on one calendar day.

| Column                    | Data Type     | Required | Key | Description                    |
| ------------------------- | ------------- | -------: | --- | ------------------------------ |
| `engagement_id`           | VARCHAR       |      Yes | PK  | Unique daily engagement record |
| `customer_id`             | VARCHAR       |      Yes | FK  | Individual customer            |
| `engagement_date`         | DATE          |      Yes |     | Date of recorded activity      |
| `sessions_count`          | INTEGER       |      Yes |     | Number of sessions             |
| `articles_viewed`         | INTEGER       |      Yes |     | Total articles viewed          |
| `premium_articles_viewed` | INTEGER       |      Yes |     | Premium articles viewed        |
| `epaper_opens`            | INTEGER       |      Yes |     | Number of ePaper opens         |
| `reading_minutes`         | DECIMAL(10,2) |      Yes |     | Total reading minutes          |
| `created_at`              | TIMESTAMP     |      Yes |     | Record creation timestamp      |

### Business Rules

* This table applies only to individual customers in v1.
* No activity on a particular day does not require a zero-filled row.
* Engagement metrics must be non-negative.
* `premium_articles_viewed` cannot exceed `articles_viewed`.
* Metrics such as days since last activity, engagement level and churn risk should be derived rather than stored.

---

# 13. SUPPORT_INTERACTIONS

Stores lightweight customer-support activity that may help explain retention and churn.

One row represents one customer support case or interaction.

| Column              | Data Type | Required | Key | Description                           |
| ------------------- | --------- | -------: | --- | ------------------------------------- |
| `interaction_id`    | VARCHAR   |      Yes | PK  | Unique support interaction            |
| `customer_id`       | VARCHAR   |      Yes | FK  | Customer contacting support           |
| `subscription_id`   | VARCHAR   |       No | FK  | Related subscription where applicable |
| `interaction_at`    | TIMESTAMP |      Yes |     | When support interaction began        |
| `channel`           | VARCHAR   |      Yes |     | Support channel                       |
| `issue_category`    | VARCHAR   |      Yes |     | Broad issue classification            |
| `resolution_status` | VARCHAR   |      Yes |     | Current/final status                  |
| `resolved_at`       | TIMESTAMP |       No |     | Time issue was resolved               |
| `created_at`        | TIMESTAMP |      Yes |     | Record creation timestamp             |

### Allowed `channel`

* `email`
* `phone`
* `live_chat`
* `web_form`

### Allowed `issue_category`

* `billing`
* `payment`
* `access_login`
* `technical`
* `content`
* `subscription_change`
* `cancellation_enquiry`
* `other`

### Allowed `resolution_status`

* `open`
* `in_progress`
* `resolved`

### Business Rules

* `subscription_id` is optional because some support issues relate only to the customer account.
* `resolved_at` should normally be populated only when `resolution_status = resolved`.
* Detailed support agent, SLA and satisfaction data are outside the v1 project scope.

---

# 14. Derived Metrics and Classifications

The following fields should **not** be permanently stored as raw columns because they can be calculated from underlying facts.

### Churn Status

Derived from:

* subscription end reason;
* subscription end date;
* subsequent subscription activity.

### Churn Type

Derived classification:

| End Reason         | Derived Churn Type   |
| ------------------ | -------------------- |
| `voluntary_cancel` | Voluntary            |
| `payment_failure`  | Involuntary          |
| `non_renewal`      | Expiry / Non-renewal |
| `plan_change`      | Not churn            |

A subscriber should only be classified as churned when no continuing/replacement subscription prevents actual customer churn.

### Organisation Band

Derived from `organisation_size`.

### Seats Activated

Derived from active records in `organisation_users`.

### Seat Utilisation

Derived from:

```text
active organisation users / seats purchased
```

### Revenue

Derived from successful payment transactions.

### Customer Lifetime Value

Derived from historical revenue and customer/subscription history.

### Days Since Last Activity

Derived from `customer_engagement.engagement_date` relative to the analysis date.

### Engagement Level

Derived from observed behavioural metrics rather than permanently stored.

---

# 15. Core Relationships

```text
CUSTOMERS
├── SUBSCRIPTIONS
├── TRIALS
├── MARKETING_TOUCHPOINTS
├── CUSTOMER_ENGAGEMENT
└── SUPPORT_INTERACTIONS

ORGANISATIONS
├── SUBSCRIPTIONS
└── ORGANISATION_USERS

PRODUCTS
├── PLANS
└── TRIALS

PLANS
└── SUBSCRIPTIONS

SUBSCRIPTIONS
├── PAYMENTS
├── SUBSCRIPTION_EVENTS
├── ORGANISATION_USERS
└── SUPPORT_INTERACTIONS

PAYMENTS
└── SUBSCRIPTION_EVENTS
```

---

# 16. Historical Data Principle

DAILYPULSE MEDIA should preserve historical business activity wherever possible.

The database should therefore avoid overwriting events such as:

* previous plans;
* failed payment attempts;
* previous billing periods;
* cancellation requests;
* cancellation reversals;
* plan migrations;
* corporate seat increases;
* corporate seat decreases;
* deactivated organisation users.

Current-state tables may change as the business evolves, while event and transaction tables retain historical activity.

---

# 17. Data Model Status

**Version 1.0 Data Model: FROZEN**

The next stage of the project is the PostgreSQL implementation.

The database schema will translate the definitions and business rules in this document into:

* PostgreSQL tables
* Primary keys
* Foreign keys
* Unique constraints
* Check constraints
* Nullability rules
* Referential integrity rules

Any future changes to the data model will be documented as a new version rather than silently altering the v1 specification.
