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

-- ============================================================
-- ANALYTICS VIEW 04: MONTHLY SUBSCRIPTION METRICS
--
-- Grain:
-- One row per calendar month
--
-- Purpose:
-- Track subscriber growth, subscription lifecycle activity,
-- payment performance and successful payment value over time.
-- ============================================================

CREATE OR REPLACE VIEW vw_monthly_subscription_metrics AS

WITH


-- ============================================================
-- 1. ANALYTICAL DATE RANGE
--
-- Find the earliest and latest month containing subscription,
-- payment or lifecycle-event activity.
-- ============================================================

activity_dates AS (

    SELECT
        subscription_start_date::date AS activity_date
    FROM subscriptions


    UNION ALL


    SELECT
        subscription_end_date::date AS activity_date
    FROM subscriptions
    WHERE subscription_end_date IS NOT NULL


    UNION ALL


    SELECT
        payment_attempted_at::date AS activity_date
    FROM payments


    UNION ALL


    SELECT
        event_at::date AS activity_date
    FROM subscription_events
),


date_bounds AS (

    SELECT

        DATE_TRUNC(
            'month',
            MIN(activity_date)
        )::date AS first_month,

        DATE_TRUNC(
            'month',
            MAX(activity_date)
        )::date AS last_month

    FROM activity_dates
),


-- ============================================================
-- 2. CALENDAR MONTHS
--
-- Generate one row for every month in the reporting period,
-- including months where a particular metric may be zero.
-- ============================================================

months AS (

    SELECT

        month_start::date AS month_start,

        (
            month_start
            + INTERVAL '1 month'
            - INTERVAL '1 day'
        )::date AS month_end

    FROM date_bounds

    CROSS JOIN GENERATE_SERIES(
        first_month,
        last_month,
        INTERVAL '1 month'
    ) AS month_start
),


-- ============================================================
-- 3. COMMON SUBSCRIBER KEY
--
-- Individuals and organisations use different identifiers.
-- This creates one common analytical subscriber identifier.
-- ============================================================

subscription_base AS (

    SELECT

        sf.*,

        CASE
            WHEN sf.organisation_id IS NOT NULL
                THEN 'ORG:' || sf.organisation_id

            ELSE 'CUST:' || sf.customer_id

        END AS subscriber_key

    FROM vw_subscription_fact AS sf
),


-- ============================================================
-- 4. FIRST PAID SUBSCRIPTION
--
-- Determine when each subscriber first became paid.
-- This prevents plan changes/reactivations being mistaken
-- for newly acquired subscribers.
-- ============================================================

first_subscription AS (

    SELECT

        subscriber_key,

        MIN(subscription_start_date)
            AS first_subscription_start_date

    FROM subscription_base

    GROUP BY subscriber_key
),


-- ============================================================
-- 5. MONTHLY SUBSCRIPTION STARTS
-- ============================================================

subscription_starts AS (

    SELECT

        DATE_TRUNC(
            'month',
            sb.subscription_start_date
        )::date AS month_start,


        COUNT(*)
            AS subscription_records_started,


        COUNT(*) FILTER (
            WHERE sb.subscriber_type = 'individual'
        ) AS individual_subscription_records_started,


        COUNT(*) FILTER (
            WHERE sb.subscriber_type = 'organisation'
        ) AS organisation_subscription_records_started,


        COUNT(
            DISTINCT sb.subscriber_key
        ) FILTER (

            WHERE sb.subscription_start_date
                = fs.first_subscription_start_date

        ) AS first_time_paid_subscribers,


        COUNT(
            DISTINCT sb.subscriber_key
        ) FILTER (

            WHERE sb.subscription_start_date
                = fs.first_subscription_start_date

              AND sb.subscriber_type = 'individual'

        ) AS first_time_individual_subscribers,


        COUNT(
            DISTINCT sb.subscriber_key
        ) FILTER (

            WHERE sb.subscription_start_date
                = fs.first_subscription_start_date

              AND sb.subscriber_type = 'organisation'

        ) AS first_time_organisation_subscribers


    FROM subscription_base AS sb


    INNER JOIN first_subscription AS fs
        ON sb.subscriber_key = fs.subscriber_key


    GROUP BY 1
),


-- ============================================================
-- 6. MONTHLY SUBSCRIPTION ENDS
-- ============================================================

subscription_ends AS (

    SELECT

        DATE_TRUNC(
            'month',
            subscription_end_date
        )::date AS month_start,


        COUNT(*)
            AS subscription_records_ended,


        COUNT(*) FILTER (
            WHERE end_reason = 'voluntary_cancel'
        ) AS voluntary_cancellation_ends,


        COUNT(*) FILTER (
            WHERE end_reason = 'non_renewal'
        ) AS non_renewal_ends,


        COUNT(*) FILTER (
            WHERE end_reason = 'plan_change'
        ) AS plan_change_ends


    FROM subscription_base

    WHERE subscription_end_date IS NOT NULL

    GROUP BY 1
),


-- ============================================================
-- 7. MONTH-END ACTIVE SUBSCRIBER BASE
--
-- A subscription is active at month-end when:
--
-- start date <= month end
-- AND
-- end date is NULL OR end date >= month end
-- ============================================================

month_end_active AS (

    SELECT

        m.month_start,


        COUNT(sb.subscription_id)
            AS active_subscription_records,


        COUNT(
            DISTINCT sb.subscriber_key
        ) AS active_subscribers,


        COUNT(sb.subscription_id) FILTER (
            WHERE sb.subscriber_type = 'individual'
        ) AS active_individual_subscriptions,


        COUNT(sb.subscription_id) FILTER (
            WHERE sb.subscriber_type = 'organisation'
        ) AS active_organisation_subscriptions,


        COUNT(
            DISTINCT sb.subscriber_key
        ) FILTER (
            WHERE sb.subscriber_type = 'individual'
        ) AS active_individual_subscribers,


        COUNT(
            DISTINCT sb.subscriber_key
        ) FILTER (
            WHERE sb.subscriber_type = 'organisation'
        ) AS active_organisation_subscribers


    FROM months AS m


    LEFT JOIN subscription_base AS sb

        ON sb.subscription_start_date <= m.month_end

        AND (
            sb.subscription_end_date IS NULL
            OR sb.subscription_end_date >= m.month_end
        )


    GROUP BY m.month_start
),


-- ============================================================
-- 8. MONTHLY LIFECYCLE EVENTS
-- ============================================================

monthly_events AS (

    SELECT

        DATE_TRUNC(
            'month',
            event_at
        )::date AS month_start,


        COUNT(*) FILTER (
            WHERE event_type = 'subscription_started'
        ) AS subscription_started_events,


        COUNT(*) FILTER (
            WHERE event_type = 'renewed'
        ) AS renewals,


        COUNT(*) FILTER (
            WHERE event_type = 'plan_changed'
        ) AS plan_changes,


        COUNT(*) FILTER (
            WHERE event_type = 'reactivated'
        ) AS reactivations,


        COUNT(*) FILTER (
            WHERE event_type = 'cancellation_requested'
        ) AS cancellation_requests,


        COUNT(*) FILTER (
            WHERE event_type = 'subscription_ended'
        ) AS subscription_ended_events,


        COUNT(*) FILTER (
            WHERE event_type = 'past_due_started'
        ) AS past_due_started,


        COUNT(*) FILTER (
            WHERE event_type = 'past_due_resolved'
        ) AS past_due_resolved


    FROM subscription_events

    GROUP BY 1
),


-- ============================================================
-- 9. MONTHLY PAYMENT PERFORMANCE
-- ============================================================

monthly_payments AS (

    SELECT

        payment_month::date AS month_start,


        COUNT(*)
            AS payment_attempts,


        SUM(successful_payment_flag)
            AS successful_payments,


        SUM(failed_payment_flag)
            AS failed_payments,


        SUM(successful_payment_value)
            AS successful_payment_value,


        SUM(successful_payment_value) FILTER (
            WHERE subscriber_type = 'individual'
        ) AS individual_successful_payment_value,


        SUM(successful_payment_value) FILTER (
            WHERE subscriber_type = 'organisation'
        ) AS organisation_successful_payment_value


    FROM vw_payment_fact

    GROUP BY 1
)


-- ============================================================
-- 10. FINAL MONTHLY ANALYTICAL OUTPUT
-- ============================================================

SELECT

    m.month_start,
    m.month_end,


    -- ========================================================
    -- ACQUISITION / SUBSCRIPTION STARTS
    -- ========================================================

    COALESCE(
        ss.subscription_records_started,
        0
    ) AS subscription_records_started,


    COALESCE(
        ss.first_time_paid_subscribers,
        0
    ) AS first_time_paid_subscribers,


    COALESCE(
        ss.first_time_individual_subscribers,
        0
    ) AS first_time_individual_subscribers,


    COALESCE(
        ss.first_time_organisation_subscribers,
        0
    ) AS first_time_organisation_subscribers,


    COALESCE(
        ss.individual_subscription_records_started,
        0
    ) AS individual_subscription_records_started,


    COALESCE(
        ss.organisation_subscription_records_started,
        0
    ) AS organisation_subscription_records_started,


    -- ========================================================
    -- SUBSCRIPTION ENDS
    -- ========================================================

    COALESCE(
        se.subscription_records_ended,
        0
    ) AS subscription_records_ended,


    COALESCE(
        se.voluntary_cancellation_ends,
        0
    ) AS voluntary_cancellation_ends,


    COALESCE(
        se.non_renewal_ends,
        0
    ) AS non_renewal_ends,


    COALESCE(
        se.plan_change_ends,
        0
    ) AS plan_change_ends,


    -- ========================================================
    -- MONTH-END ACTIVE BASE
    -- ========================================================

    COALESCE(
        ma.active_subscription_records,
        0
    ) AS active_subscription_records,


    COALESCE(
        ma.active_subscribers,
        0
    ) AS active_subscribers,


    COALESCE(
        ma.active_individual_subscriptions,
        0
    ) AS active_individual_subscriptions,


    COALESCE(
        ma.active_organisation_subscriptions,
        0
    ) AS active_organisation_subscriptions,


    COALESCE(
        ma.active_individual_subscribers,
        0
    ) AS active_individual_subscribers,


    COALESCE(
        ma.active_organisation_subscribers,
        0
    ) AS active_organisation_subscribers,


    -- ========================================================
    -- LIFECYCLE EVENTS
    -- ========================================================

    COALESCE(
        me.subscription_started_events,
        0
    ) AS subscription_started_events,


    COALESCE(
        me.renewals,
        0
    ) AS renewals,


    COALESCE(
        me.plan_changes,
        0
    ) AS plan_changes,


    COALESCE(
        me.reactivations,
        0
    ) AS reactivations,


    COALESCE(
        me.cancellation_requests,
        0
    ) AS cancellation_requests,


    COALESCE(
        me.subscription_ended_events,
        0
    ) AS subscription_ended_events,


    COALESCE(
        me.past_due_started,
        0
    ) AS past_due_started,


    COALESCE(
        me.past_due_resolved,
        0
    ) AS past_due_resolved,


    -- ========================================================
    -- PAYMENT PERFORMANCE
    -- ========================================================

    COALESCE(
        mp.payment_attempts,
        0
    ) AS payment_attempts,


    COALESCE(
        mp.successful_payments,
        0
    ) AS successful_payments,


    COALESCE(
        mp.failed_payments,
        0
    ) AS failed_payments,


    CASE

        WHEN COALESCE(
            mp.payment_attempts,
            0
        ) = 0

            THEN 0::numeric

        ELSE ROUND(

            (
                COALESCE(
                    mp.failed_payments,
                    0
                )::numeric

                / mp.payment_attempts
            ) * 100,

            2
        )

    END AS payment_failure_rate_pct,


    COALESCE(
        mp.successful_payment_value,
        0
    ) AS successful_payment_value,


    COALESCE(
        mp.individual_successful_payment_value,
        0
    ) AS individual_successful_payment_value,


    COALESCE(
        mp.organisation_successful_payment_value,
        0
    ) AS organisation_successful_payment_value


FROM months AS m


LEFT JOIN subscription_starts AS ss
    ON m.month_start = ss.month_start


LEFT JOIN subscription_ends AS se
    ON m.month_start = se.month_start


LEFT JOIN month_end_active AS ma
    ON m.month_start = ma.month_start


LEFT JOIN monthly_events AS me
    ON m.month_start = me.month_start


LEFT JOIN monthly_payments AS mp
    ON m.month_start = mp.month_start


ORDER BY m.month_start;