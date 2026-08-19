-- ============================================================
-- DAILYPULSE MEDIA
-- Subscription Intelligence Database
-- File: 02_seed_reference_data.sql
-- Version: 1.0
-- Purpose: Seed product and subscription plan reference data
-- ============================================================

BEGIN;


-- ============================================================
-- 1. PRODUCTS
-- ============================================================

INSERT INTO products (
    product_id,
    product_name,
    product_family,
    target_segment,
    is_active
)
VALUES
    (
        'PROD001',
        'Digital Basic',
        'Digital News',
        'General',
        TRUE
    ),
    (
        'PROD002',
        'Digital Premium',
        'Digital News',
        'General',
        TRUE
    ),
    (
        'PROD003',
        'ePaper',
        'ePaper',
        'General',
        TRUE
    ),
    (
        'PROD004',
        'Weekend ePaper',
        'ePaper',
        'General',
        TRUE
    ),
    (
        'PROD005',
        'Student Digital',
        'Digital News',
        'Student',
        TRUE
    ),
    (
        'PROD006',
        'Corporate ePaper',
        'ePaper',
        'Organisation',
        TRUE
    );


-- ============================================================
-- 2. SUBSCRIPTION PLANS
-- ============================================================

INSERT INTO plans (
    plan_id,
    product_id,
    plan_name,
    billing_frequency,
    billing_period_days,
    unit_price,
    currency,
    is_active
)
VALUES

    -- --------------------------------------------------------
    -- DIGITAL BASIC
    -- --------------------------------------------------------

    (
        'PLN001',
        'PROD001',
        'Digital Basic Daily',
        'Daily',
        1,
        30.00,
        'KES',
        TRUE
    ),

    (
        'PLN002',
        'PROD001',
        'Digital Basic Weekly',
        'Weekly',
        7,
        150.00,
        'KES',
        TRUE
    ),

    (
        'PLN003',
        'PROD001',
        'Digital Basic Monthly',
        'Monthly',
        30,
        500.00,
        'KES',
        TRUE
    ),

    (
        'PLN004',
        'PROD001',
        'Digital Basic Annual',
        'Annual',
        365,
        5000.00,
        'KES',
        TRUE
    ),


    -- --------------------------------------------------------
    -- DIGITAL PREMIUM
    -- --------------------------------------------------------

    (
        'PLN005',
        'PROD002',
        'Digital Premium Weekly',
        'Weekly',
        7,
        250.00,
        'KES',
        TRUE
    ),

    (
        'PLN006',
        'PROD002',
        'Digital Premium Monthly',
        'Monthly',
        30,
        800.00,
        'KES',
        TRUE
    ),

    (
        'PLN007',
        'PROD002',
        'Digital Premium Annual',
        'Annual',
        365,
        8000.00,
        'KES',
        TRUE
    ),


    -- --------------------------------------------------------
    -- ePAPER
    -- --------------------------------------------------------

    (
        'PLN008',
        'PROD003',
        'ePaper Daily',
        'Daily',
        1,
        60.00,
        'KES',
        TRUE
    ),

    (
        'PLN009',
        'PROD003',
        'ePaper Weekly',
        'Weekly',
        7,
        300.00,
        'KES',
        TRUE
    ),

    (
        'PLN010',
        'PROD003',
        'ePaper Monthly',
        'Monthly',
        30,
        1000.00,
        'KES',
        TRUE
    ),

    (
        'PLN011',
        'PROD003',
        'ePaper Annual',
        'Annual',
        365,
        10000.00,
        'KES',
        TRUE
    ),


    -- --------------------------------------------------------
    -- WEEKEND ePAPER
    -- --------------------------------------------------------

    (
        'PLN012',
        'PROD004',
        'Weekend ePaper Weekly',
        'Weekly',
        7,
        150.00,
        'KES',
        TRUE
    ),

    (
        'PLN013',
        'PROD004',
        'Weekend ePaper Monthly',
        'Monthly',
        30,
        500.00,
        'KES',
        TRUE
    ),


    -- --------------------------------------------------------
    -- STUDENT DIGITAL
    -- --------------------------------------------------------

    (
        'PLN014',
        'PROD005',
        'Student Digital Weekly',
        'Weekly',
        7,
        100.00,
        'KES',
        TRUE
    ),

    (
        'PLN015',
        'PROD005',
        'Student Digital Monthly',
        'Monthly',
        30,
        300.00,
        'KES',
        TRUE
    ),

    (
        'PLN016',
        'PROD005',
        'Student Digital Annual',
        'Annual',
        365,
        3000.00,
        'KES',
        TRUE
    ),


    -- --------------------------------------------------------
    -- CORPORATE ePAPER
    -- Prices represent per-seat rates.
    -- Minimum purchase: 10 seats.
    -- --------------------------------------------------------

    (
        'PLN017',
        'PROD006',
        'Corporate ePaper Monthly',
        'Monthly',
        30,
        800.00,
        'KES',
        TRUE
    ),

    (
        'PLN018',
        'PROD006',
        'Corporate ePaper Annual',
        'Annual',
        365,
        8000.00,
        'KES',
        TRUE
    );


COMMIT;
