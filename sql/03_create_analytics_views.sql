-- ============================================================
-- DAILYPULSE MEDIA
-- SUBSCRIPTION INTELLIGENCE
--
-- ANALYTICS VIEW 01: SUBSCRIPTION FACT
--
-- Grain:
-- One row per subscription_id
-- ============================================================

CREATE OR REPLACE VIEW vw_subscription_fact AS

SELECT

    -- ========================================================
    -- 1. SUBSCRIPTION IDENTITY
    -- ========================================================

    s.subscription_id,
    s.customer_id,
    s.organisation_id,
    s.plan_id,

    CASE
        WHEN s.organisation_id IS NOT NULL
            THEN 'organisation'
        ELSE 'individual'
    END AS subscriber_type,


    -- ========================================================
    -- 2. SUBSCRIPTION LIFECYCLE
    -- ========================================================

    s.subscription_start_date,
    s.subscription_end_date,
    s.status AS subscription_status,
    s.end_reason,
    s.seats_purchased,


    -- ========================================================
    -- 3. CUSTOMER CONTEXT
    -- Existing columns preserved in original order
    -- ========================================================

    c.country AS customer_country,
    c.signup_date AS customer_signup_date,


    -- ========================================================
    -- 4. ORGANISATION CONTEXT
    -- Existing columns preserved in original order
    -- ========================================================

    o.organisation_name,
    o.organisation_type,
    o.organisation_size,


    -- ========================================================
    -- 5. ADDITIONAL ACCOUNT CONTEXT
    -- New columns appended after existing view columns
    -- ========================================================

    c.account_status AS customer_account_status,
    o.account_status AS organisation_account_status,


    -- ========================================================
    -- 6. PLAN CONTEXT
    -- ========================================================

    p.plan_name,
    p.billing_frequency,
    p.billing_period_days,
    p.unit_price,
    p.currency AS plan_currency,
    p.is_active AS plan_is_active,


    -- ========================================================
    -- 7. PRODUCT CONTEXT
    -- ========================================================

    pr.product_id,
    pr.product_name,
    pr.product_family,
    pr.target_segment,
    pr.is_active AS product_is_active


FROM subscriptions AS s

LEFT JOIN customers AS c
    ON s.customer_id = c.customer_id

LEFT JOIN organisations AS o
    ON s.organisation_id = o.organisation_id

LEFT JOIN plans AS p
    ON s.plan_id = p.plan_id

LEFT JOIN products AS pr
    ON p.product_id = pr.product_id;

-- ============================================================
-- ANALYTICS VIEW 02: PAYMENT FACT
--
-- Grain:
-- One row per payment attempt
-- ============================================================

CREATE OR REPLACE VIEW vw_payment_fact AS

SELECT

    -- ========================================================
    -- 1. PAYMENT IDENTITY
    -- ========================================================

    p.payment_id,
    p.subscription_id,
    p.transaction_reference,


    -- ========================================================
    -- 2. PAYMENT TIMING
    -- ========================================================

    p.payment_attempted_at,

    CAST(p.payment_attempted_at AS DATE)
        AS payment_attempt_date,

    DATE_TRUNC('month', p.payment_attempted_at)
        AS payment_month,


    -- ========================================================
    -- 3. PAYMENT VALUE
    -- ========================================================

    p.amount,
    p.currency,

    CASE
        WHEN p.payment_status = 'successful'
            THEN p.amount
        ELSE 0
    END AS successful_payment_value,


    -- ========================================================
    -- 4. PAYMENT OUTCOME
    -- ========================================================

    p.payment_status,
    p.payment_method,
    p.failure_reason,

    CASE
        WHEN p.payment_status = 'successful'
            THEN 1
        ELSE 0
    END AS successful_payment_flag,

    CASE
        WHEN p.payment_status = 'failed'
            THEN 1
        ELSE 0
    END AS failed_payment_flag,


    -- ========================================================
    -- 5. SUBSCRIBER CONTEXT
    -- ========================================================

    sf.customer_id,
    sf.organisation_id,
    sf.subscriber_type,

    sf.customer_country,
    sf.organisation_name,
    sf.organisation_type,
    sf.organisation_size,


    -- ========================================================
    -- 6. SUBSCRIPTION LIFECYCLE
    -- ========================================================

    sf.subscription_start_date,
    sf.subscription_end_date,
    sf.subscription_status,
    sf.end_reason,
    sf.seats_purchased,


    -- ========================================================
    -- 7. PLAN CONTEXT
    -- ========================================================

    sf.plan_id,
    sf.plan_name,
    sf.billing_frequency,
    sf.billing_period_days,
    sf.unit_price AS plan_unit_price,


    -- ========================================================
    -- 8. PRODUCT CONTEXT
    -- ========================================================

    sf.product_id,
    sf.product_name,
    sf.product_family,
    sf.target_segment,


    -- ========================================================
    -- 9. SYSTEM METADATA
    -- ========================================================

    p.created_at


FROM payments AS p

LEFT JOIN vw_subscription_fact AS sf
    ON p.subscription_id = sf.subscription_id;

-- ============================================================
-- ANALYTICS VIEW 03: CUSTOMER LIFECYCLE
--
-- Grain:
-- One row per customer_id
-- ============================================================

CREATE OR REPLACE VIEW vw_customer_lifecycle AS

WITH


-- ============================================================
-- 1. TRIAL ACTIVITY
-- One row per customer
-- ============================================================

trial_summary AS (

    SELECT
        customer_id,

        COUNT(*) AS total_trials,

        COUNT(*) FILTER (
            WHERE trial_status = 'converted'
        ) AS converted_trials,

        COUNT(*) FILTER (
            WHERE trial_status = 'expired'
        ) AS expired_trials,

        COUNT(*) FILTER (
            WHERE trial_status = 'cancelled'
        ) AS cancelled_trials,

        COUNT(*) FILTER (
            WHERE trial_status = 'active'
        ) AS active_trials,

        MIN(trial_started_at)
            AS first_trial_started_at,

        MAX(trial_started_at)
            AS latest_trial_started_at,

        MIN(actual_end_at) FILTER (
            WHERE trial_status = 'converted'
        ) AS first_trial_conversion_at

    FROM trials

    GROUP BY customer_id
),


-- ============================================================
-- 2. SUBSCRIPTION ACTIVITY
-- One row per customer
-- ============================================================

subscription_summary AS (

    SELECT
        customer_id,

        COUNT(*) AS total_subscription_records,

        COUNT(*) FILTER (
            WHERE subscription_status = 'active'
        ) AS active_subscription_records,

        COUNT(*) FILTER (
            WHERE subscription_status = 'ended'
        ) AS ended_subscription_records,

        COUNT(*) FILTER (
            WHERE end_reason = 'voluntary_cancel'
        ) AS voluntary_cancellations,

        COUNT(*) FILTER (
            WHERE end_reason = 'plan_change'
        ) AS plan_change_terminations,

        COUNT(DISTINCT plan_id)
            AS distinct_plans_used,

        COUNT(DISTINCT product_id)
            AS distinct_products_used,

        MIN(subscription_start_date)
            AS first_subscription_start_date,

        MAX(subscription_start_date)
            AS latest_subscription_start_date,

        MAX(subscription_end_date)
            AS latest_subscription_end_date

    FROM vw_subscription_fact

    WHERE customer_id IS NOT NULL

    GROUP BY customer_id
),


-- ============================================================
-- 3. PAYMENT ACTIVITY
-- One row per customer
-- ============================================================

payment_summary AS (

    SELECT
        customer_id,

        COUNT(*) AS total_payment_attempts,

        SUM(successful_payment_flag)
            AS successful_payments,

        SUM(failed_payment_flag)
            AS failed_payments,

        SUM(successful_payment_value)
            AS lifetime_successful_payment_value,

        MIN(payment_attempted_at) FILTER (
            WHERE payment_status = 'successful'
        ) AS first_successful_payment_at,

        MAX(payment_attempted_at) FILTER (
            WHERE payment_status = 'successful'
        ) AS latest_successful_payment_at,

        MIN(payment_attempted_at) FILTER (
            WHERE payment_status = 'failed'
        ) AS first_failed_payment_at,

        MAX(payment_attempted_at) FILTER (
            WHERE payment_status = 'failed'
        ) AS latest_failed_payment_at

    FROM vw_payment_fact

    WHERE customer_id IS NOT NULL

    GROUP BY customer_id
),


-- ============================================================
-- 4. SUBSCRIPTION EVENT ACTIVITY
-- Events are mapped back to customers through subscriptions
-- ============================================================

event_summary AS (

    SELECT
        sf.customer_id,

        COUNT(*) AS total_subscription_events,

        COUNT(*) FILTER (
            WHERE se.event_type = 'subscription_started'
        ) AS subscription_started_events,

        COUNT(*) FILTER (
            WHERE se.event_type = 'renewed'
        ) AS renewal_events,

        COUNT(*) FILTER (
            WHERE se.event_type = 'plan_changed'
        ) AS plan_change_events,

        COUNT(*) FILTER (
            WHERE se.event_type = 'cancellation_requested'
        ) AS cancellation_requested_events,

        COUNT(*) FILTER (
            WHERE se.event_type = 'subscription_ended'
        ) AS subscription_ended_events,

        COUNT(*) FILTER (
            WHERE se.event_type = 'reactivated'
        ) AS reactivation_events,

        COUNT(*) FILTER (
            WHERE se.event_type = 'past_due_started'
        ) AS past_due_started_events,

        COUNT(*) FILTER (
            WHERE se.event_type = 'past_due_resolved'
        ) AS past_due_resolved_events,

        MIN(se.event_at) FILTER (
            WHERE se.event_type = 'reactivated'
        ) AS first_reactivation_at,

        MAX(se.event_at) FILTER (
            WHERE se.event_type = 'reactivated'
        ) AS latest_reactivation_at,

        MIN(se.event_at) FILTER (
            WHERE se.event_type = 'cancellation_requested'
        ) AS first_cancellation_requested_at,

        MAX(se.event_at) FILTER (
            WHERE se.event_type = 'cancellation_requested'
        ) AS latest_cancellation_requested_at

    FROM subscription_events AS se

    INNER JOIN vw_subscription_fact AS sf
        ON se.subscription_id = sf.subscription_id

    WHERE sf.customer_id IS NOT NULL

    GROUP BY sf.customer_id
)


-- ============================================================
-- 5. CUSTOMER LIFECYCLE OUTPUT
-- ============================================================

SELECT

    -- CUSTOMER IDENTITY

    c.customer_id,
    c.country,
    c.signup_date,

    DATE_TRUNC(
        'month',
        c.signup_date
    )::date AS signup_month,

    c.account_status,


    -- ========================================================
    -- TRIAL LIFECYCLE
    -- ========================================================

    COALESCE(t.total_trials, 0)
        AS total_trials,

    COALESCE(t.converted_trials, 0)
        AS converted_trials,

    COALESCE(t.expired_trials, 0)
        AS expired_trials,

    COALESCE(t.cancelled_trials, 0)
        AS cancelled_trials,

    COALESCE(t.active_trials, 0)
        AS active_trials,

    t.first_trial_started_at,
    t.latest_trial_started_at,
    t.first_trial_conversion_at,

    (
        COALESCE(t.total_trials, 0) > 0
    ) AS ever_trialled,

    (
        COALESCE(t.converted_trials, 0) > 0
    ) AS ever_converted_trial,


    -- ========================================================
    -- SUBSCRIPTION LIFECYCLE
    -- ========================================================

    COALESCE(s.total_subscription_records, 0)
        AS total_subscription_records,

    COALESCE(s.active_subscription_records, 0)
        AS active_subscription_records,

    COALESCE(s.ended_subscription_records, 0)
        AS ended_subscription_records,

    COALESCE(s.voluntary_cancellations, 0)
        AS voluntary_cancellations,

    COALESCE(s.plan_change_terminations, 0)
        AS plan_change_terminations,

    COALESCE(s.distinct_plans_used, 0)
        AS distinct_plans_used,

    COALESCE(s.distinct_products_used, 0)
        AS distinct_products_used,

    s.first_subscription_start_date,
    s.latest_subscription_start_date,
    s.latest_subscription_end_date,

    (
        COALESCE(s.total_subscription_records, 0) > 0
    ) AS ever_subscribed,

    (
        COALESCE(s.active_subscription_records, 0) > 0
    ) AS current_subscriber,


    -- ========================================================
    -- PAYMENT LIFECYCLE
    -- ========================================================

    COALESCE(p.total_payment_attempts, 0)
        AS total_payment_attempts,

    COALESCE(p.successful_payments, 0)
        AS successful_payments,

    COALESCE(p.failed_payments, 0)
        AS failed_payments,

    COALESCE(
        p.lifetime_successful_payment_value,
        0
    ) AS lifetime_successful_payment_value,

    p.first_successful_payment_at,
    p.latest_successful_payment_at,
    p.first_failed_payment_at,
    p.latest_failed_payment_at,

    (
        COALESCE(p.successful_payments, 0) > 0
    ) AS ever_made_successful_payment,

    (
        COALESCE(p.failed_payments, 0) > 0
    ) AS ever_had_payment_failure,


    -- ========================================================
    -- EVENT LIFECYCLE
    -- ========================================================

    COALESCE(e.total_subscription_events, 0)
        AS total_subscription_events,

    COALESCE(e.subscription_started_events, 0)
        AS subscription_started_events,

    COALESCE(e.renewal_events, 0)
        AS renewal_events,

    COALESCE(e.plan_change_events, 0)
        AS plan_change_events,

    COALESCE(e.cancellation_requested_events, 0)
        AS cancellation_requested_events,

    COALESCE(e.subscription_ended_events, 0)
        AS subscription_ended_events,

    COALESCE(e.reactivation_events, 0)
        AS reactivation_events,

    COALESCE(e.past_due_started_events, 0)
        AS past_due_started_events,

    COALESCE(e.past_due_resolved_events, 0)
        AS past_due_resolved_events,

    e.first_reactivation_at,
    e.latest_reactivation_at,

    e.first_cancellation_requested_at,
    e.latest_cancellation_requested_at,

    (
        COALESCE(e.reactivation_events, 0) > 0
    ) AS ever_reactivated,

    (
        COALESCE(e.cancellation_requested_events, 0) > 0
    ) AS ever_requested_cancellation,

    (
        COALESCE(e.past_due_started_events, 0) > 0
    ) AS ever_past_due


FROM customers AS c

LEFT JOIN trial_summary AS t
    ON c.customer_id = t.customer_id

LEFT JOIN subscription_summary AS s
    ON c.customer_id = s.customer_id

LEFT JOIN payment_summary AS p
    ON c.customer_id = p.customer_id

LEFT JOIN event_summary AS e
    ON c.customer_id = e.customer_id;