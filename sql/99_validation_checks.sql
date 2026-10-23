-- ============================================================
-- DAILYPULSE MEDIA
-- SUBSCRIPTION INTELLIGENCE
--
-- FINAL ANALYTICS VALIDATION SUITE
--
-- Purpose:
-- Reconcile the operational database and analytical layer
-- before Phase 2 is formally closed.
--
-- This script is read-only.
-- It does not CREATE, DROP, UPDATE, INSERT or DELETE anything.
-- ============================================================


WITH validation_checks AS (


-- ============================================================
-- 1. CORE OPERATIONAL TABLES
-- ============================================================

SELECT
    10 AS check_order,
    '01 Core Tables' AS section,
    'Customers' AS check_name,
    (SELECT COUNT(*)::text FROM customers) AS actual_value,
    '5000' AS expected_value,
    (SELECT COUNT(*) = 5000 FROM customers) AS passed

UNION ALL

SELECT
    11,
    '01 Core Tables',
    'Organisations',
    (SELECT COUNT(*)::text FROM organisations),
    '100',
    (SELECT COUNT(*) = 100 FROM organisations)

UNION ALL

SELECT
    12,
    '01 Core Tables',
    'Marketing touchpoints',
    (SELECT COUNT(*)::text FROM marketing_touchpoints),
    '18992',
    (SELECT COUNT(*) = 18992 FROM marketing_touchpoints)

UNION ALL

SELECT
    13,
    '01 Core Tables',
    'Trials',
    (SELECT COUNT(*)::text FROM trials),
    '1917',
    (SELECT COUNT(*) = 1917 FROM trials)

UNION ALL

SELECT
    14,
    '01 Core Tables',
    'Subscriptions',
    (SELECT COUNT(*)::text FROM subscriptions),
    '3333',
    (SELECT COUNT(*) = 3333 FROM subscriptions)

UNION ALL

SELECT
    15,
    '01 Core Tables',
    'Payments',
    (SELECT COUNT(*)::text FROM payments),
    '13259',
    (SELECT COUNT(*) = 13259 FROM payments)

UNION ALL

SELECT
    16,
    '01 Core Tables',
    'Subscription events',
    (SELECT COUNT(*)::text FROM subscription_events),
    '16668',
    (SELECT COUNT(*) = 16668 FROM subscription_events)


-- ============================================================
-- 2. RELATIONAL INTEGRITY
-- ============================================================

UNION ALL

SELECT
    20,
    '02 Relational Integrity',
    'Converted trials linked to subscriptions',
    (
        SELECT COUNT(*)::text
        FROM trials
        WHERE trial_status = 'converted'
          AND converted_subscription_id IS NOT NULL
    ),
    '982',
    (
        SELECT COUNT(*) = 982
        FROM trials
        WHERE trial_status = 'converted'
          AND converted_subscription_id IS NOT NULL
    )

UNION ALL

SELECT
    21,
    '02 Relational Integrity',
    'Invalid converted-trial subscription links',
    (
        SELECT COUNT(*)::text
        FROM trials AS t
        LEFT JOIN subscriptions AS s
            ON t.converted_subscription_id = s.subscription_id
        WHERE t.converted_subscription_id IS NOT NULL
          AND s.subscription_id IS NULL
    ),
    '0',
    (
        SELECT COUNT(*) = 0
        FROM trials AS t
        LEFT JOIN subscriptions AS s
            ON t.converted_subscription_id = s.subscription_id
        WHERE t.converted_subscription_id IS NOT NULL
          AND s.subscription_id IS NULL
    )

UNION ALL

SELECT
    22,
    '02 Relational Integrity',
    'Orphan payments',
    (
        SELECT COUNT(*)::text
        FROM payments AS p
        LEFT JOIN subscriptions AS s
            ON p.subscription_id = s.subscription_id
        WHERE s.subscription_id IS NULL
    ),
    '0',
    (
        SELECT COUNT(*) = 0
        FROM payments AS p
        LEFT JOIN subscriptions AS s
            ON p.subscription_id = s.subscription_id
        WHERE s.subscription_id IS NULL
    )

UNION ALL

SELECT
    23,
    '02 Relational Integrity',
    'Orphan subscription events',
    (
        SELECT COUNT(*)::text
        FROM subscription_events AS se
        LEFT JOIN subscriptions AS s
            ON se.subscription_id = s.subscription_id
        WHERE s.subscription_id IS NULL
    ),
    '0',
    (
        SELECT COUNT(*) = 0
        FROM subscription_events AS se
        LEFT JOIN subscriptions AS s
            ON se.subscription_id = s.subscription_id
        WHERE s.subscription_id IS NULL
    )

UNION ALL

SELECT
    24,
    '02 Relational Integrity',
    'Invalid triggering payment links',
    (
        SELECT COUNT(*)::text
        FROM subscription_events AS se
        LEFT JOIN payments AS p
            ON se.triggering_payment_id = p.payment_id
        WHERE se.triggering_payment_id IS NOT NULL
          AND p.payment_id IS NULL
    ),
    '0',
    (
        SELECT COUNT(*) = 0
        FROM subscription_events AS se
        LEFT JOIN payments AS p
            ON se.triggering_payment_id = p.payment_id
        WHERE se.triggering_payment_id IS NOT NULL
          AND p.payment_id IS NULL
    )


-- ============================================================
-- 3. VIEW 01 — SUBSCRIPTION FACT
-- ============================================================

UNION ALL

SELECT
    30,
    '03 Subscription Fact',
    'Subscription fact rows',
    (SELECT COUNT(*)::text FROM vw_subscription_fact),
    '3333',
    (SELECT COUNT(*) = 3333 FROM vw_subscription_fact)

UNION ALL

SELECT
    31,
    '03 Subscription Fact',
    'Unique subscription IDs',
    (
        SELECT COUNT(DISTINCT subscription_id)::text
        FROM vw_subscription_fact
    ),
    '3333',
    (
        SELECT COUNT(DISTINCT subscription_id) = 3333
        FROM vw_subscription_fact
    )

UNION ALL

SELECT
    32,
    '03 Subscription Fact',
    'Missing plan context',
    (
        SELECT COUNT(*)::text
        FROM vw_subscription_fact
        WHERE plan_name IS NULL
    ),
    '0',
    (
        SELECT COUNT(*) = 0
        FROM vw_subscription_fact
        WHERE plan_name IS NULL
    )

UNION ALL

SELECT
    33,
    '03 Subscription Fact',
    'Missing product context',
    (
        SELECT COUNT(*)::text
        FROM vw_subscription_fact
        WHERE product_name IS NULL
    ),
    '0',
    (
        SELECT COUNT(*) = 0
        FROM vw_subscription_fact
        WHERE product_name IS NULL
    )


-- ============================================================
-- 4. VIEW 02 — PAYMENT FACT
-- ============================================================

UNION ALL

SELECT
    40,
    '04 Payment Fact',
    'Payment fact rows',
    (SELECT COUNT(*)::text FROM vw_payment_fact),
    '13259',
    (SELECT COUNT(*) = 13259 FROM vw_payment_fact)

UNION ALL

SELECT
    41,
    '04 Payment Fact',
    'Unique payment IDs',
    (
        SELECT COUNT(DISTINCT payment_id)::text
        FROM vw_payment_fact
    ),
    '13259',
    (
        SELECT COUNT(DISTINCT payment_id) = 13259
        FROM vw_payment_fact
    )

UNION ALL

SELECT
    42,
    '04 Payment Fact',
    'Successful payments',
    (
        SELECT COUNT(*)::text
        FROM vw_payment_fact
        WHERE payment_status = 'successful'
    ),
    '12817',
    (
        SELECT COUNT(*) = 12817
        FROM vw_payment_fact
        WHERE payment_status = 'successful'
    )

UNION ALL

SELECT
    43,
    '04 Payment Fact',
    'Failed payments',
    (
        SELECT COUNT(*)::text
        FROM vw_payment_fact
        WHERE payment_status = 'failed'
    ),
    '442',
    (
        SELECT COUNT(*) = 442
        FROM vw_payment_fact
        WHERE payment_status = 'failed'
    )

UNION ALL

SELECT
    44,
    '04 Payment Fact',
    'Successful payment value',
    (
        SELECT ROUND(
            SUM(successful_payment_value),
            2
        )::text
        FROM vw_payment_fact
    ),
    '112124300.00',
    (
        SELECT ROUND(
            SUM(successful_payment_value),
            2
        ) = 112124300.00
        FROM vw_payment_fact
    )


-- ============================================================
-- 5. VIEW 03 — CUSTOMER LIFECYCLE
-- ============================================================

UNION ALL

SELECT
    50,
    '05 Customer Lifecycle',
    'Customer lifecycle rows',
    (SELECT COUNT(*)::text FROM vw_customer_lifecycle),
    '5000',
    (SELECT COUNT(*) = 5000 FROM vw_customer_lifecycle)

UNION ALL

SELECT
    51,
    '05 Customer Lifecycle',
    'Individual subscription records',
    (
        SELECT SUM(total_subscription_records)::text
        FROM vw_customer_lifecycle
    ),
    '3248',
    (
        SELECT SUM(total_subscription_records) = 3248
        FROM vw_customer_lifecycle
    )

UNION ALL

SELECT
    52,
    '05 Customer Lifecycle',
    'Individual payment attempts',
    (
        SELECT SUM(total_payment_attempts)::text
        FROM vw_customer_lifecycle
    ),
    '12931',
    (
        SELECT SUM(total_payment_attempts) = 12931
        FROM vw_customer_lifecycle
    )

UNION ALL

SELECT
    53,
    '05 Customer Lifecycle',
    'Individual successful payment value',
    (
        SELECT ROUND(
            SUM(lifetime_successful_payment_value),
            2
        )::text
        FROM vw_customer_lifecycle
    ),
    '11883940.00',
    (
        SELECT ROUND(
            SUM(lifetime_successful_payment_value),
            2
        ) = 11883940.00
        FROM vw_customer_lifecycle
    )


-- ============================================================
-- 6. VIEW 04 — MONTHLY SUBSCRIPTION METRICS
-- ============================================================

UNION ALL

SELECT
    60,
    '06 Monthly Metrics',
    'Reporting months',
    (
        SELECT COUNT(*)::text
        FROM vw_monthly_subscription_metrics
    ),
    '18',
    (
        SELECT COUNT(*) = 18
        FROM vw_monthly_subscription_metrics
    )

UNION ALL

SELECT
    61,
    '06 Monthly Metrics',
    'First reporting month',
    (
        SELECT MIN(month_start)::text
        FROM vw_monthly_subscription_metrics
    ),
    '2025-03-01',
    (
        SELECT MIN(month_start) = DATE '2025-03-01'
        FROM vw_monthly_subscription_metrics
    )

UNION ALL

SELECT
    62,
    '06 Monthly Metrics',
    'Latest reporting month',
    (
        SELECT MAX(month_start)::text
        FROM vw_monthly_subscription_metrics
    ),
    '2026-08-01',
    (
        SELECT MAX(month_start) = DATE '2026-08-01'
        FROM vw_monthly_subscription_metrics
    )

UNION ALL

SELECT
    63,
    '06 Monthly Metrics',
    'First-time paid subscribers',
    (
        SELECT SUM(first_time_paid_subscribers)::text
        FROM vw_monthly_subscription_metrics
    ),
    '2872',
    (
        SELECT SUM(first_time_paid_subscribers) = 2872
        FROM vw_monthly_subscription_metrics
    )

UNION ALL

SELECT
    64,
    '06 Monthly Metrics',
    'Renewals',
    (
        SELECT SUM(renewals)::text
        FROM vw_monthly_subscription_metrics
    ),
    '9484',
    (
        SELECT SUM(renewals) = 9484
        FROM vw_monthly_subscription_metrics
    )

UNION ALL

SELECT
    65,
    '06 Monthly Metrics',
    'Reactivations',
    (
        SELECT SUM(reactivations)::text
        FROM vw_monthly_subscription_metrics
    ),
    '93',
    (
        SELECT SUM(reactivations) = 93
        FROM vw_monthly_subscription_metrics
    )

UNION ALL

SELECT
    66,
    '06 Monthly Metrics',
    'Monthly successful payment value',
    (
        SELECT ROUND(
            SUM(successful_payment_value),
            2
        )::text
        FROM vw_monthly_subscription_metrics
    ),
    '112124300.00',
    (
        SELECT ROUND(
            SUM(successful_payment_value),
            2
        ) = 112124300.00
        FROM vw_monthly_subscription_metrics
    )


-- ============================================================
-- 7. VIEW 05 — ACQUISITION PERFORMANCE
-- ============================================================

UNION ALL

SELECT
    70,
    '07 Acquisition Performance',
    'Acquisition channels',
    (SELECT COUNT(*)::text FROM vw_acquisition_performance),
    '10',
    (SELECT COUNT(*) = 10 FROM vw_acquisition_performance)

UNION ALL

SELECT
    71,
    '07 Acquisition Performance',
    'Touchpoints reconciled',
    (
        SELECT SUM(total_touchpoints)::text
        FROM vw_acquisition_performance
    ),
    '18992',
    (
        SELECT SUM(total_touchpoints) = 18992
        FROM vw_acquisition_performance
    )

UNION ALL

SELECT
    72,
    '07 Acquisition Performance',
    'Customers attributed exactly once',
    (
        SELECT SUM(first_touch_customers)::text
        FROM vw_acquisition_performance
    ),
    '5000',
    (
        SELECT SUM(first_touch_customers) = 5000
        FROM vw_acquisition_performance
    )

UNION ALL

SELECT
    73,
    '07 Acquisition Performance',
    'Attributed marketing cost',
    (
        SELECT ROUND(
            SUM(channel_attributed_cost),
            2
        )::text
        FROM vw_acquisition_performance
    ),
    '161828.56',
    (
        SELECT ROUND(
            SUM(channel_attributed_cost),
            2
        ) = 161828.56
        FROM vw_acquisition_performance
    )

UNION ALL

SELECT
    74,
    '07 Acquisition Performance',
    'Attributed paid subscribers',
    (
        SELECT SUM(paid_subscribers)::text
        FROM vw_acquisition_performance
    ),
    '2795',
    (
        SELECT SUM(paid_subscribers) = 2795
        FROM vw_acquisition_performance
    )


-- ============================================================
-- 8. VIEW 06 — SUBSCRIPTION COHORTS
-- ============================================================

UNION ALL

SELECT
    80,
    '08 Subscription Cohorts',
    'Total cohort members at M0',
    (
        SELECT SUM(cohort_size)::text
        FROM vw_subscription_cohorts
        WHERE months_since_acquisition = 0
    ),
    '2872',
    (
        SELECT SUM(cohort_size) = 2872
        FROM vw_subscription_cohorts
        WHERE months_since_acquisition = 0
    )

UNION ALL

SELECT
    81,
    '08 Subscription Cohorts',
    'Invalid cohort states',
    (
        SELECT COUNT(*)::text
        FROM vw_subscription_cohorts
        WHERE active_subscribers > cohort_size
           OR active_subscribers < 0
           OR month_end_active_rate_pct > 100
           OR month_end_active_rate_pct < 0
    ),
    '0',
    (
        SELECT COUNT(*) = 0
        FROM vw_subscription_cohorts
        WHERE active_subscribers > cohort_size
           OR active_subscribers < 0
           OR month_end_active_rate_pct > 100
           OR month_end_active_rate_pct < 0
    )

UNION ALL

SELECT
    82,
    '08 Subscription Cohorts',
    'August 2026 active cohort subscribers',
    (
        SELECT SUM(active_subscribers)::text
        FROM vw_subscription_cohorts
        WHERE observation_month = DATE '2026-08-01'
    ),
    '1697',
    (
        SELECT SUM(active_subscribers) = 1697
        FROM vw_subscription_cohorts
        WHERE observation_month = DATE '2026-08-01'
    )


-- ============================================================
-- 9. VIEW 07 — ORGANISATION PERFORMANCE
-- ============================================================

UNION ALL

SELECT
    90,
    '09 Organisation Performance',
    'Organisation rows',
    (
        SELECT COUNT(*)::text
        FROM vw_organisation_performance
    ),
    '100',
    (
        SELECT COUNT(*) = 100
        FROM vw_organisation_performance
    )

UNION ALL

SELECT
    91,
    '09 Organisation Performance',
    'Subscribing organisations',
    (
        SELECT COUNT(*)::text
        FROM vw_organisation_performance
        WHERE ever_subscribed = TRUE
    ),
    '77',
    (
        SELECT COUNT(*) = 77
        FROM vw_organisation_performance
        WHERE ever_subscribed = TRUE
    )

UNION ALL

SELECT
    92,
    '09 Organisation Performance',
    'Organisation subscription records',
    (
        SELECT SUM(total_subscription_records)::text
        FROM vw_organisation_performance
    ),
    '85',
    (
        SELECT SUM(total_subscription_records) = 85
        FROM vw_organisation_performance
    )

UNION ALL

SELECT
    93,
    '09 Organisation Performance',
    'Organisation successful payment value',
    (
        SELECT ROUND(
            SUM(observed_successful_payment_value),
            2
        )::text
        FROM vw_organisation_performance
    ),
    '100240360.00',
    (
        SELECT ROUND(
            SUM(observed_successful_payment_value),
            2
        ) = 100240360.00
        FROM vw_organisation_performance
    )


-- ============================================================
-- 10. VIEW 08 — RECURRING REVENUE
-- ============================================================

UNION ALL

SELECT
    100,
    '10 Recurring Revenue',
    'Recurring revenue reporting months',
    (
        SELECT COUNT(DISTINCT month_start)::text
        FROM vw_recurring_revenue_fact
    ),
    '18',
    (
        SELECT COUNT(DISTINCT month_start) = 18
        FROM vw_recurring_revenue_fact
    )

UNION ALL

SELECT
    101,
    '10 Recurring Revenue',
    'August 2026 active subscribers',
    (
        SELECT COUNT(DISTINCT subscriber_key)::text
        FROM vw_recurring_revenue_fact
        WHERE month_start = DATE '2026-08-01'
    ),
    '1697',
    (
        SELECT COUNT(DISTINCT subscriber_key) = 1697
        FROM vw_recurring_revenue_fact
        WHERE month_start = DATE '2026-08-01'
    )

UNION ALL

SELECT
    102,
    '10 Recurring Revenue',
    'August 2026 MRR',
    (
        SELECT ROUND(
            SUM(normalized_mrr),
            2
        )::text
        FROM vw_recurring_revenue_fact
        WHERE month_start = DATE '2026-08-01'
    ),
    '9617936.00',
    (
        SELECT ROUND(
            SUM(normalized_mrr),
            2
        ) = 9617936.00
        FROM vw_recurring_revenue_fact
        WHERE month_start = DATE '2026-08-01'
    )

UNION ALL

SELECT
    103,
    '10 Recurring Revenue',
    'August 2026 ARR run-rate',
    (
        SELECT ROUND(
            SUM(annualized_recurring_revenue),
            2
        )::text
        FROM vw_recurring_revenue_fact
        WHERE month_start = DATE '2026-08-01'
    ),
    '115415220.00',
    (
        SELECT ROUND(
            SUM(annualized_recurring_revenue),
            2
        ) = 115415220.00
        FROM vw_recurring_revenue_fact
        WHERE month_start = DATE '2026-08-01'
    )

UNION ALL

SELECT
    104,
    '10 Recurring Revenue',
    'Invalid recurring revenue rows',
    (
        SELECT COUNT(*)::text
        FROM vw_recurring_revenue_fact
        WHERE normalized_mrr IS NULL
           OR normalized_mrr < 0
           OR annualized_recurring_revenue IS NULL
           OR annualized_recurring_revenue < 0
    ),
    '0',
    (
        SELECT COUNT(*) = 0
        FROM vw_recurring_revenue_fact
        WHERE normalized_mrr IS NULL
           OR normalized_mrr < 0
           OR annualized_recurring_revenue IS NULL
           OR annualized_recurring_revenue < 0
    )

UNION ALL

SELECT
    105,
    '10 Recurring Revenue',
    'MRR / ARR inconsistencies',
    (
        SELECT COUNT(*)::text
        FROM vw_recurring_revenue_fact
        WHERE ABS(
            annualized_recurring_revenue
            - (normalized_mrr * 12)
        ) > 0.12
    ),
    '0',
    (
        SELECT COUNT(*) = 0
        FROM vw_recurring_revenue_fact
        WHERE ABS(
            annualized_recurring_revenue
            - (normalized_mrr * 12)
        ) > 0.12
    )


-- ============================================================
-- 11. CROSS-VIEW RECONCILIATION
-- ============================================================

UNION ALL

SELECT
    110,
    '11 Cross-View Reconciliation',
    'Individual + organisation payment value = total',
    (
        SELECT ROUND(
            (
                SELECT SUM(
                    lifetime_successful_payment_value
                )
                FROM vw_customer_lifecycle
            )
            +
            (
                SELECT SUM(
                    observed_successful_payment_value
                )
                FROM vw_organisation_performance
            ),
            2
        )::text
    ),
    '112124300.00',
    (
        SELECT ROUND(
            (
                SELECT SUM(
                    lifetime_successful_payment_value
                )
                FROM vw_customer_lifecycle
            )
            +
            (
                SELECT SUM(
                    observed_successful_payment_value
                )
                FROM vw_organisation_performance
            ),
            2
        ) = 112124300.00
    )

UNION ALL

SELECT
    111,
    '11 Cross-View Reconciliation',
    'August monthly vs recurring active subscribers',
    (
        SELECT ABS(
            (
                SELECT active_subscribers
                FROM vw_monthly_subscription_metrics
                WHERE month_start = DATE '2026-08-01'
            )
            -
            (
                SELECT COUNT(DISTINCT subscriber_key)
                FROM vw_recurring_revenue_fact
                WHERE month_start = DATE '2026-08-01'
            )
        )::text
    ),
    '0',
    (
        SELECT
            (
                SELECT active_subscribers
                FROM vw_monthly_subscription_metrics
                WHERE month_start = DATE '2026-08-01'
            )
            =
            (
                SELECT COUNT(DISTINCT subscriber_key)
                FROM vw_recurring_revenue_fact
                WHERE month_start = DATE '2026-08-01'
            )
    )

)


-- ============================================================
-- FINAL VALIDATION REPORT
-- ============================================================

SELECT

    section,
    check_name,
    actual_value,
    expected_value,

    CASE
        WHEN passed = TRUE
            THEN 'PASS'
        ELSE 'FAIL'
    END AS status

FROM validation_checks

ORDER BY check_order;