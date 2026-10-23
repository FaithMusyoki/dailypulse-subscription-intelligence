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

-- ============================================================
-- ANALYTICS VIEW 05: ACQUISITION PERFORMANCE
--
-- Grain:
-- One row per acquisition channel
--
-- Attribution model:
-- First-touch attribution.
--
-- Each customer is assigned to the channel associated with
-- their earliest recorded marketing touchpoint.
-- ============================================================

CREATE OR REPLACE VIEW vw_acquisition_performance AS

WITH


-- ============================================================
-- 1. RANK CUSTOMER TOUCHPOINTS
--
-- Rank every customer's marketing interactions
-- chronologically so we can identify the first touch.
-- ============================================================

ranked_touchpoints AS (

    SELECT

        mt.touchpoint_id,
        mt.customer_id,
        mt.touchpoint_at,
        mt.channel,
        mt.campaign_name,
        mt.touchpoint_type,
        mt.attributed_cost,

        ROW_NUMBER() OVER (

            PARTITION BY mt.customer_id

            ORDER BY
                mt.touchpoint_at,
                mt.touchpoint_id

        ) AS touchpoint_rank

    FROM marketing_touchpoints AS mt
),


-- ============================================================
-- 2. FIRST TOUCH PER CUSTOMER
--
-- Exactly one acquisition channel per customer.
-- ============================================================

first_touch AS (

    SELECT

        customer_id,
        touchpoint_id AS first_touchpoint_id,
        touchpoint_at AS first_touch_at,
        channel AS first_touch_channel,
        campaign_name AS first_touch_campaign,
        touchpoint_type AS first_touch_type

    FROM ranked_touchpoints

    WHERE touchpoint_rank = 1
),


-- ============================================================
-- 3. OVERALL CHANNEL ACTIVITY
--
-- This describes all marketing activity recorded for each
-- channel, not just first-touch interactions.
-- ============================================================

channel_activity AS (

    SELECT

        channel,

        COUNT(*)
            AS total_touchpoints,

        COUNT(
            DISTINCT customer_id
        ) AS unique_touched_customers,

        ROUND(
            SUM(attributed_cost),
            2
        ) AS channel_attributed_cost

    FROM marketing_touchpoints

    GROUP BY channel
),


-- ============================================================
-- 4. FIRST-TOUCH CUSTOMER OUTCOMES
--
-- Connect each customer's assigned acquisition channel to
-- their downstream subscription lifecycle.
-- ============================================================

first_touch_outcomes AS (

    SELECT

        ft.first_touch_channel AS channel,


        COUNT(*)
            AS first_touch_customers,


        COUNT(*) FILTER (
            WHERE cl.ever_trialled = TRUE
        ) AS trial_customers,


        COUNT(*) FILTER (
            WHERE cl.ever_converted_trial = TRUE
        ) AS converted_trial_customers,


        COUNT(*) FILTER (
            WHERE cl.ever_subscribed = TRUE
        ) AS paid_subscribers,


        COUNT(*) FILTER (
            WHERE cl.current_subscriber = TRUE
        ) AS current_subscribers,


        COUNT(*) FILTER (
            WHERE cl.ever_had_payment_failure = TRUE
        ) AS customers_with_payment_failure,


        COUNT(*) FILTER (
            WHERE cl.ever_reactivated = TRUE
        ) AS reactivated_customers,


        SUM(
            cl.total_trials
        ) AS total_trials,


        ROUND(
            SUM(
                cl.lifetime_successful_payment_value
            ),
            2
        ) AS observed_successful_payment_value


    FROM first_touch AS ft


    INNER JOIN vw_customer_lifecycle AS cl
        ON ft.customer_id = cl.customer_id


    GROUP BY ft.first_touch_channel
)


-- ============================================================
-- 5. FINAL ACQUISITION PERFORMANCE OUTPUT
-- ============================================================

SELECT

    ca.channel,


    -- ========================================================
    -- CHANNEL ACTIVITY
    -- ========================================================

    ca.total_touchpoints,

    ca.unique_touched_customers,

    ca.channel_attributed_cost,


    -- ========================================================
    -- FIRST-TOUCH ATTRIBUTION
    -- ========================================================

    COALESCE(
        fto.first_touch_customers,
        0
    ) AS first_touch_customers,


    ROUND(

        (
            COALESCE(
                fto.first_touch_customers,
                0
            )::numeric

            /

            NULLIF(
                SUM(
                    COALESCE(
                        fto.first_touch_customers,
                        0
                    )
                ) OVER (),
                0
            )

        ) * 100,

        2

    ) AS first_touch_customer_share_pct,


    -- ========================================================
    -- TRIAL FUNNEL
    -- ========================================================

    COALESCE(
        fto.trial_customers,
        0
    ) AS trial_customers,


    COALESCE(
        fto.total_trials,
        0
    ) AS total_trials,


    COALESCE(
        fto.converted_trial_customers,
        0
    ) AS converted_trial_customers,


    ROUND(

        (
            COALESCE(
                fto.trial_customers,
                0
            )::numeric

            /

            NULLIF(
                fto.first_touch_customers,
                0
            )

        ) * 100,

        2

    ) AS trial_rate_pct,


    ROUND(

        (
            COALESCE(
                fto.converted_trial_customers,
                0
            )::numeric

            /

            NULLIF(
                fto.trial_customers,
                0
            )

        ) * 100,

        2

    ) AS trial_conversion_rate_pct,


    -- ========================================================
    -- PAID CONVERSION
    -- ========================================================

    COALESCE(
        fto.paid_subscribers,
        0
    ) AS paid_subscribers,


    ROUND(

        (
            COALESCE(
                fto.paid_subscribers,
                0
            )::numeric

            /

            NULLIF(
                fto.first_touch_customers,
                0
            )

        ) * 100,

        2

    ) AS paid_conversion_rate_pct,


    -- ========================================================
    -- CURRENT SUBSCRIBER BASE
    -- ========================================================

    COALESCE(
        fto.current_subscribers,
        0
    ) AS current_subscribers,


    ROUND(

        (
            COALESCE(
                fto.current_subscribers,
                0
            )::numeric

            /

            NULLIF(
                fto.paid_subscribers,
                0
            )

        ) * 100,

        2

    ) AS current_share_of_paid_pct,


    -- ========================================================
    -- LIFECYCLE QUALITY
    -- ========================================================

    COALESCE(
        fto.customers_with_payment_failure,
        0
    ) AS customers_with_payment_failure,


    COALESCE(
        fto.reactivated_customers,
        0
    ) AS reactivated_customers,


    -- ========================================================
    -- COMMERCIAL VALUE
    --
    -- This is observed historical successful payment value
    -- within the available dataset, not predicted LTV.
    -- ========================================================

    COALESCE(
        fto.observed_successful_payment_value,
        0
    ) AS observed_successful_payment_value,


    ROUND(

        COALESCE(
            fto.observed_successful_payment_value,
            0
        )

        /

        NULLIF(
            fto.paid_subscribers,
            0
        ),

        2

    ) AS avg_payment_value_per_paid_subscriber,


    -- ========================================================
    -- ACQUISITION EFFICIENCY
    --
    -- Channel cost includes all recorded touchpoint costs
    -- for that channel.
    --
    -- Paid subscribers and value are credited using
    -- first-touch attribution.
    -- ========================================================

    ROUND(

        ca.channel_attributed_cost

        /

        NULLIF(
            fto.paid_subscribers,
            0
        ),

        2

    ) AS cost_per_paid_subscriber,


    CASE

        WHEN ca.channel_attributed_cost = 0
            THEN NULL

        ELSE ROUND(

            COALESCE(
                fto.observed_successful_payment_value,
                0
            )

            / ca.channel_attributed_cost,

            2
        )

    END AS payment_value_to_cost_ratio


FROM channel_activity AS ca


LEFT JOIN first_touch_outcomes AS fto
    ON ca.channel = fto.channel


ORDER BY
    paid_subscribers DESC,
    ca.channel;

-- ============================================================
-- ANALYTICS VIEW 06: SUBSCRIPTION COHORTS
--
-- Grain:
-- One row per:
-- cohort month
-- × observation month
-- × subscriber type
-- × initial product
-- × initial billing frequency
--
-- Purpose:
-- Track how first-time paid subscriber cohorts remain active
-- over subsequent calendar months.
--
-- Important:
-- This measures month-end active rate.
-- Reactivated subscribers count as active again if they have
-- an active subscription at the relevant month-end.
-- ============================================================

CREATE OR REPLACE VIEW vw_subscription_cohorts AS

WITH


-- ============================================================
-- 1. COMMON SUBSCRIBER KEY
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
-- 2. RANK EACH SUBSCRIBER'S SUBSCRIPTIONS
--
-- This identifies the first subscription record and therefore
-- the subscriber's original product / billing configuration.
-- ============================================================

ranked_subscriptions AS (

    SELECT

        sb.*,

        ROW_NUMBER() OVER (

            PARTITION BY sb.subscriber_key

            ORDER BY
                sb.subscription_start_date,
                sb.subscription_id

        ) AS subscription_rank

    FROM subscription_base AS sb
),


-- ============================================================
-- 3. COHORT MEMBERS
--
-- Exactly one row per subscriber.
-- Cohort month = month of first paid subscription.
-- ============================================================

cohort_members AS (

    SELECT

        subscriber_key,

        subscriber_type,

        subscription_start_date
            AS first_subscription_start_date,

        DATE_TRUNC(
            'month',
            subscription_start_date
        )::date AS cohort_month,

        product_id
            AS initial_product_id,

        product_name
            AS initial_product_name,

        product_family
            AS initial_product_family,

        plan_id
            AS initial_plan_id,

        plan_name
            AS initial_plan_name,

        billing_frequency
            AS initial_billing_frequency

    FROM ranked_subscriptions

    WHERE subscription_rank = 1
),


-- ============================================================
-- 4. COHORT SIZES
-- ============================================================

cohort_sizes AS (

    SELECT

        cohort_month,
        subscriber_type,

        initial_product_id,
        initial_product_name,
        initial_product_family,

        initial_plan_id,
        initial_plan_name,
        initial_billing_frequency,

        COUNT(*)
            AS cohort_size

    FROM cohort_members

    GROUP BY
        cohort_month,
        subscriber_type,
        initial_product_id,
        initial_product_name,
        initial_product_family,
        initial_plan_id,
        initial_plan_name,
        initial_billing_frequency
),


-- ============================================================
-- 5. OBSERVATION MONTHS
--
-- Reuse the reporting calendar already validated in View 04.
-- ============================================================

observation_months AS (

    SELECT

        month_start AS observation_month,
        month_end AS observation_month_end

    FROM vw_monthly_subscription_metrics
),


-- ============================================================
-- 6. MONTH-END ACTIVE MEMBERS
--
-- Each cohort member is evaluated at each month-end from their
-- cohort month onward.
--
-- EXISTS prevents multiple active subscription records from
-- accidentally counting the same subscriber more than once.
-- ============================================================

active_cohort_members AS (

    SELECT

        cm.cohort_month,
        om.observation_month,

        cm.subscriber_type,

        cm.initial_product_id,
        cm.initial_product_name,
        cm.initial_product_family,

        cm.initial_plan_id,
        cm.initial_plan_name,
        cm.initial_billing_frequency,

        COUNT(*)
            AS active_subscribers

    FROM cohort_members AS cm


    INNER JOIN observation_months AS om

        ON om.observation_month >= cm.cohort_month


    WHERE EXISTS (

        SELECT 1

        FROM subscription_base AS sb

        WHERE sb.subscriber_key = cm.subscriber_key

          AND sb.subscription_start_date
                <= om.observation_month_end

          AND (

                sb.subscription_end_date IS NULL

                OR sb.subscription_end_date
                    >= om.observation_month_end
          )
    )


    GROUP BY
        cm.cohort_month,
        om.observation_month,
        cm.subscriber_type,
        cm.initial_product_id,
        cm.initial_product_name,
        cm.initial_product_family,
        cm.initial_plan_id,
        cm.initial_plan_name,
        cm.initial_billing_frequency
),


-- ============================================================
-- 7. COMPLETE COHORT GRID
--
-- Ensure cohort/month combinations still appear even if no
-- subscribers from that cohort remain active.
-- ============================================================

cohort_grid AS (

    SELECT

        cs.cohort_month,
        om.observation_month,

        cs.subscriber_type,

        cs.initial_product_id,
        cs.initial_product_name,
        cs.initial_product_family,

        cs.initial_plan_id,
        cs.initial_plan_name,
        cs.initial_billing_frequency,

        cs.cohort_size

    FROM cohort_sizes AS cs


    INNER JOIN observation_months AS om

        ON om.observation_month >= cs.cohort_month
)


-- ============================================================
-- 8. FINAL COHORT OUTPUT
-- ============================================================

SELECT

    cg.cohort_month,
    cg.observation_month,


    -- ========================================================
    -- COHORT AGE
    -- ========================================================

    (
        (
            EXTRACT(
                YEAR FROM cg.observation_month
            )

            -

            EXTRACT(
                YEAR FROM cg.cohort_month
            )
        ) * 12

        +

        (
            EXTRACT(
                MONTH FROM cg.observation_month
            )

            -

            EXTRACT(
                MONTH FROM cg.cohort_month
            )
        )

    )::integer AS months_since_acquisition,


    -- ========================================================
    -- STARTING SEGMENT
    -- ========================================================

    cg.subscriber_type,

    cg.initial_product_id,
    cg.initial_product_name,
    cg.initial_product_family,

    cg.initial_plan_id,
    cg.initial_plan_name,
    cg.initial_billing_frequency,


    -- ========================================================
    -- COHORT PERFORMANCE
    -- ========================================================

    cg.cohort_size,


    COALESCE(
        acm.active_subscribers,
        0
    ) AS active_subscribers,


    (
        cg.cohort_size
        -
        COALESCE(
            acm.active_subscribers,
            0
        )
    ) AS inactive_subscribers,


    ROUND(

        (
            COALESCE(
                acm.active_subscribers,
                0
            )::numeric

            /

            NULLIF(
                cg.cohort_size,
                0
            )

        ) * 100,

        2

    ) AS month_end_active_rate_pct


FROM cohort_grid AS cg


LEFT JOIN active_cohort_members AS acm

    ON cg.cohort_month = acm.cohort_month

    AND cg.observation_month
        = acm.observation_month

    AND cg.subscriber_type
        = acm.subscriber_type

    AND cg.initial_plan_id
        = acm.initial_plan_id


ORDER BY
    cg.cohort_month,
    cg.observation_month,
    cg.subscriber_type,
    cg.initial_product_name,
    cg.initial_plan_name;

-- ============================================================
-- ANALYTICS VIEW 07: ORGANISATION PERFORMANCE
--
-- Grain:
-- One row per organisation_id
--
-- Purpose:
-- Analyse institutional subscription adoption, seat penetration,
-- payment behaviour, lifecycle activity and revenue concentration.
-- ============================================================

CREATE OR REPLACE VIEW vw_organisation_performance AS

WITH


-- ============================================================
-- 1. ORGANISATION SUBSCRIPTION SUMMARY
-- ============================================================

subscription_summary AS (

    SELECT

        organisation_id,

        COUNT(*)
            AS total_subscription_records,

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
            WHERE end_reason = 'non_renewal'
        ) AS non_renewals,

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
            AS latest_subscription_end_date,

        MAX(seats_purchased)
            AS max_seats_purchased,

        SUM(seats_purchased) FILTER (
            WHERE subscription_status = 'active'
        ) AS current_active_seats

    FROM vw_subscription_fact

    WHERE organisation_id IS NOT NULL

    GROUP BY organisation_id
),


-- ============================================================
-- 2. LATEST SUBSCRIPTION RECORD
--
-- Gives us the organisation's most recent commercial
-- configuration without assuming it has only one historical
-- subscription.
-- ============================================================

ranked_subscriptions AS (

    SELECT

        organisation_id,
        plan_id,
        plan_name,
        product_id,
        product_name,
        product_family,
        billing_frequency,
        seats_purchased,
        subscription_status,

        ROW_NUMBER() OVER (

            PARTITION BY organisation_id

            ORDER BY
                subscription_start_date DESC,
                subscription_id DESC

        ) AS subscription_rank

    FROM vw_subscription_fact

    WHERE organisation_id IS NOT NULL
),


latest_subscription AS (

    SELECT

        organisation_id,

        plan_id
            AS latest_plan_id,

        plan_name
            AS latest_plan_name,

        product_id
            AS latest_product_id,

        product_name
            AS latest_product_name,

        product_family
            AS latest_product_family,

        billing_frequency
            AS latest_billing_frequency,

        seats_purchased
            AS latest_seats_purchased,

        subscription_status
            AS latest_subscription_status

    FROM ranked_subscriptions

    WHERE subscription_rank = 1
),


-- ============================================================
-- 3. ORGANISATION PAYMENT SUMMARY
-- ============================================================

payment_summary AS (

    SELECT

        organisation_id,

        COUNT(*)
            AS total_payment_attempts,

        SUM(successful_payment_flag)
            AS successful_payments,

        SUM(failed_payment_flag)
            AS failed_payments,

        ROUND(
            SUM(successful_payment_value),
            2
        ) AS observed_successful_payment_value,

        MIN(payment_attempted_at) FILTER (
            WHERE payment_status = 'successful'
        ) AS first_successful_payment_at,

        MAX(payment_attempted_at) FILTER (
            WHERE payment_status = 'successful'
        ) AS latest_successful_payment_at

    FROM vw_payment_fact

    WHERE organisation_id IS NOT NULL

    GROUP BY organisation_id
),


-- ============================================================
-- 4. ORGANISATION EVENT SUMMARY
-- ============================================================

event_summary AS (

    SELECT

        sf.organisation_id,

        COUNT(*) FILTER (
            WHERE se.event_type = 'renewed'
        ) AS renewal_events,

        COUNT(*) FILTER (
            WHERE se.event_type = 'plan_changed'
        ) AS plan_change_events,

        COUNT(*) FILTER (
            WHERE se.event_type = 'reactivated'
        ) AS reactivation_events,

        COUNT(*) FILTER (
            WHERE se.event_type = 'cancellation_requested'
        ) AS cancellation_requested_events,

        COUNT(*) FILTER (
            WHERE se.event_type = 'past_due_started'
        ) AS past_due_started_events,

        COUNT(*) FILTER (
            WHERE se.event_type = 'past_due_resolved'
        ) AS past_due_resolved_events

    FROM subscription_events AS se

    INNER JOIN vw_subscription_fact AS sf
        ON se.subscription_id = sf.subscription_id

    WHERE sf.organisation_id IS NOT NULL

    GROUP BY sf.organisation_id
),


-- ============================================================
-- 5. BASE ORGANISATION PERFORMANCE
-- ============================================================

organisation_base AS (

    SELECT

        -- ORGANISATION PROFILE

        o.organisation_id,
        o.organisation_name,
        o.organisation_type,
        o.industry,
        o.organisation_size,
        o.signup_date,
        o.account_status,


        -- SUBSCRIPTION ADOPTION

        (
            COALESCE(
                ss.total_subscription_records,
                0
            ) > 0
        ) AS ever_subscribed,

        (
            COALESCE(
                ss.active_subscription_records,
                0
            ) > 0
        ) AS current_subscriber,

        COALESCE(
            ss.total_subscription_records,
            0
        ) AS total_subscription_records,

        COALESCE(
            ss.active_subscription_records,
            0
        ) AS active_subscription_records,

        COALESCE(
            ss.ended_subscription_records,
            0
        ) AS ended_subscription_records,

        ss.first_subscription_start_date,
        ss.latest_subscription_start_date,
        ss.latest_subscription_end_date,


        -- PLAN / PRODUCT HISTORY

        COALESCE(
            ss.distinct_plans_used,
            0
        ) AS distinct_plans_used,

        COALESCE(
            ss.distinct_products_used,
            0
        ) AS distinct_products_used,

        ls.latest_plan_id,
        ls.latest_plan_name,
        ls.latest_product_id,
        ls.latest_product_name,
        ls.latest_product_family,
        ls.latest_billing_frequency,
        ls.latest_subscription_status,


        -- SEAT ADOPTION

        COALESCE(
            ss.max_seats_purchased,
            0
        ) AS max_seats_purchased,

        COALESCE(
            ss.current_active_seats,
            0
        ) AS current_active_seats,

        ROUND(

            (
                COALESCE(
                    ss.max_seats_purchased,
                    0
                )::numeric

                /

                NULLIF(
                    o.organisation_size,
                    0
                )

            ) * 100,

            2

        ) AS max_seat_penetration_pct,

        ROUND(

            (
                COALESCE(
                    ss.current_active_seats,
                    0
                )::numeric

                /

                NULLIF(
                    o.organisation_size,
                    0
                )

            ) * 100,

            2

        ) AS current_seat_penetration_pct,


        -- TERMINATION HISTORY

        COALESCE(
            ss.voluntary_cancellations,
            0
        ) AS voluntary_cancellations,

        COALESCE(
            ss.non_renewals,
            0
        ) AS non_renewals,

        COALESCE(
            ss.plan_change_terminations,
            0
        ) AS plan_change_terminations,


        -- PAYMENT PERFORMANCE

        COALESCE(
            ps.total_payment_attempts,
            0
        ) AS total_payment_attempts,

        COALESCE(
            ps.successful_payments,
            0
        ) AS successful_payments,

        COALESCE(
            ps.failed_payments,
            0
        ) AS failed_payments,

        CASE

            WHEN COALESCE(
                ps.total_payment_attempts,
                0
            ) = 0

                THEN NULL

            ELSE ROUND(

                (
                    COALESCE(
                        ps.failed_payments,
                        0
                    )::numeric

                    /

                    ps.total_payment_attempts

                ) * 100,

                2
            )

        END AS payment_failure_rate_pct,

        COALESCE(
            ps.observed_successful_payment_value,
            0
        ) AS observed_successful_payment_value,

        ps.first_successful_payment_at,
        ps.latest_successful_payment_at,


        -- LIFECYCLE EVENTS

        COALESCE(
            es.renewal_events,
            0
        ) AS renewal_events,

        COALESCE(
            es.plan_change_events,
            0
        ) AS plan_change_events,

        COALESCE(
            es.reactivation_events,
            0
        ) AS reactivation_events,

        COALESCE(
            es.cancellation_requested_events,
            0
        ) AS cancellation_requested_events,

        COALESCE(
            es.past_due_started_events,
            0
        ) AS past_due_started_events,

        COALESCE(
            es.past_due_resolved_events,
            0
        ) AS past_due_resolved_events


    FROM organisations AS o


    LEFT JOIN subscription_summary AS ss
        ON o.organisation_id = ss.organisation_id


    LEFT JOIN latest_subscription AS ls
        ON o.organisation_id = ls.organisation_id


    LEFT JOIN payment_summary AS ps
        ON o.organisation_id = ps.organisation_id


    LEFT JOIN event_summary AS es
        ON o.organisation_id = es.organisation_id
)


-- ============================================================
-- 6. FINAL OUTPUT
--
-- Revenue share and rank are calculated only after each
-- organisation has been reduced to one row.
-- ============================================================

SELECT

    ob.*,


    -- ========================================================
    -- ENTERPRISE REVENUE CONCENTRATION
    -- ========================================================

    ROUND(

        (
            ob.observed_successful_payment_value

            /

            NULLIF(
                SUM(
                    ob.observed_successful_payment_value
                ) OVER (),
                0
            )

        ) * 100,

        2

    ) AS organisation_revenue_share_pct,


    CASE

        WHEN ob.ever_subscribed = TRUE

            THEN RANK() OVER (

                ORDER BY
                    ob.observed_successful_payment_value DESC
            )

        ELSE NULL

    END AS organisation_revenue_rank


FROM organisation_base AS ob

ORDER BY
    observed_successful_payment_value DESC,
    organisation_name;
