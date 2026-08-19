-- ============================================================
-- DAILYPULSE MEDIA
-- Subscription Intelligence Database
-- File: 01_create_schema.sql
-- Version: 1.0
-- Database: PostgreSQL
-- ============================================================


-- ============================================================
-- 1. CUSTOMERS
-- ============================================================

CREATE TABLE customers (
    customer_id VARCHAR(20) PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    signup_date DATE NOT NULL,
    country VARCHAR(100) NOT NULL,
    account_status VARCHAR(20) NOT NULL,

    CONSTRAINT chk_customer_account_status
        CHECK (account_status IN ('active', 'suspended', 'closed'))
);


-- ============================================================
-- 2. PRODUCTS
-- ============================================================

CREATE TABLE products (
    product_id VARCHAR(20) PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL UNIQUE,
    product_family VARCHAR(50) NOT NULL,
    target_segment VARCHAR(50) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT chk_product_family
        CHECK (product_family IN ('Digital News', 'ePaper')),

    CONSTRAINT chk_target_segment
        CHECK (target_segment IN ('General', 'Student', 'Organisation'))
);


-- ============================================================
-- 3. PLANS
-- ============================================================

CREATE TABLE plans (
    plan_id VARCHAR(20) PRIMARY KEY,
    product_id VARCHAR(20) NOT NULL,
    plan_name VARCHAR(150) NOT NULL UNIQUE,
    billing_frequency VARCHAR(20) NOT NULL,
    billing_period_days INTEGER NOT NULL,
    unit_price NUMERIC(12,2) NOT NULL,
    currency VARCHAR(10) NOT NULL DEFAULT 'KES',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT fk_plan_product
        FOREIGN KEY (product_id)
        REFERENCES products(product_id),

    CONSTRAINT chk_billing_frequency
        CHECK (
            billing_frequency IN (
                'Daily',
                'Weekly',
                'Monthly',
                'Annual'
            )
        ),

    CONSTRAINT chk_billing_period_days
        CHECK (billing_period_days > 0),

    CONSTRAINT chk_plan_unit_price
        CHECK (unit_price >= 0)
);


-- ============================================================
-- 4. ORGANISATIONS
-- ============================================================

CREATE TABLE organisations (
    organisation_id VARCHAR(20) PRIMARY KEY,
    organisation_name VARCHAR(200) NOT NULL,
    organisation_type VARCHAR(50) NOT NULL,
    industry VARCHAR(100) NOT NULL,
    organisation_size INTEGER NOT NULL,
    signup_date DATE NOT NULL,
    billing_contact_name VARCHAR(150) NOT NULL,
    billing_contact_email VARCHAR(255) NOT NULL,
    account_status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_organisation_type
        CHECK (
            organisation_type IN (
                'Corporate',
                'University',
                'Government',
                'NGO',
                'Professional Association',
                'Other'
            )
        ),

    CONSTRAINT chk_organisation_size
        CHECK (organisation_size > 0),

    CONSTRAINT chk_organisation_account_status
        CHECK (
            account_status IN (
                'active',
                'suspended',
                'closed'
            )
        )
);


-- ============================================================
-- 5. SUBSCRIPTIONS
-- ============================================================

CREATE TABLE subscriptions (
    subscription_id VARCHAR(20) PRIMARY KEY,

    customer_id VARCHAR(20),
    organisation_id VARCHAR(20),

    plan_id VARCHAR(20) NOT NULL,

    subscription_start_date DATE NOT NULL,
    current_period_start DATE NOT NULL,
    current_period_end DATE NOT NULL,
    subscription_end_date DATE,

    status VARCHAR(20) NOT NULL,
    auto_renew BOOLEAN NOT NULL DEFAULT TRUE,

    cancellation_requested_at TIMESTAMP,
    end_reason VARCHAR(30),

    seats_purchased INTEGER,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_subscription_customer
        FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id),

    CONSTRAINT fk_subscription_organisation
        FOREIGN KEY (organisation_id)
        REFERENCES organisations(organisation_id),

    CONSTRAINT fk_subscription_plan
        FOREIGN KEY (plan_id)
        REFERENCES plans(plan_id),

    -- A subscription must belong to either an individual
    -- customer OR an organisation, but never both.
    CONSTRAINT chk_subscription_owner
        CHECK (
            (customer_id IS NOT NULL AND organisation_id IS NULL)
            OR
            (customer_id IS NULL AND organisation_id IS NOT NULL)
        ),

    CONSTRAINT chk_subscription_status
        CHECK (
            status IN (
                'active',
                'past_due',
                'ended'
            )
        ),

    CONSTRAINT chk_subscription_end_reason
        CHECK (
            end_reason IS NULL
            OR end_reason IN (
                'plan_change',
                'voluntary_cancel',
                'payment_failure',
                'non_renewal'
            )
        ),

    CONSTRAINT chk_subscription_period
        CHECK (
            current_period_end >= current_period_start
        ),

    CONSTRAINT chk_subscription_start_period
        CHECK (
            current_period_start >= subscription_start_date
        ),

    CONSTRAINT chk_subscription_end_date
        CHECK (
            subscription_end_date IS NULL
            OR subscription_end_date >= subscription_start_date
        ),

    -- Organisation subscriptions require seats.
    -- Individual subscriptions do not use seats.
    CONSTRAINT chk_subscription_seats
        CHECK (
            (organisation_id IS NOT NULL AND seats_purchased > 0)
            OR
            (organisation_id IS NULL AND seats_purchased IS NULL)
        ),

    -- An ended subscription should have an end date and reason.
    CONSTRAINT chk_ended_subscription
        CHECK (
            status <> 'ended'
            OR (
                subscription_end_date IS NOT NULL
                AND end_reason IS NOT NULL
            )
        )
);


-- ============================================================
-- 6. PAYMENTS
-- ============================================================

CREATE TABLE payments (
    payment_id VARCHAR(20) PRIMARY KEY,
    subscription_id VARCHAR(20) NOT NULL,

    payment_attempted_at TIMESTAMP NOT NULL,
    amount NUMERIC(12,2) NOT NULL,
    currency VARCHAR(10) NOT NULL DEFAULT 'KES',

    payment_status VARCHAR(20) NOT NULL,
    payment_method VARCHAR(30) NOT NULL,

    transaction_reference VARCHAR(100) UNIQUE,
    failure_reason VARCHAR(50),

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_payment_subscription
        FOREIGN KEY (subscription_id)
        REFERENCES subscriptions(subscription_id),

    CONSTRAINT chk_payment_amount
        CHECK (amount > 0),

    CONSTRAINT chk_payment_status
        CHECK (
            payment_status IN (
                'successful',
                'failed',
                'pending'
            )
        ),

    CONSTRAINT chk_payment_method
        CHECK (
            payment_method IN (
                'mobile_money',
                'card',
                'bank_transfer'
            )
        ),

    CONSTRAINT chk_payment_failure_reason
        CHECK (
            failure_reason IS NULL
            OR failure_reason IN (
                'insufficient_funds',
                'expired_card',
                'payment_declined',
                'invalid_payment_details',
                'timeout',
                'other'
            )
        ),

    -- Successful transactions should not have a failure reason.
    CONSTRAINT chk_successful_payment_no_failure
        CHECK (
            payment_status <> 'successful'
            OR failure_reason IS NULL
        )
);


-- ============================================================
-- 7. SUBSCRIPTION EVENTS
-- ============================================================

CREATE TABLE subscription_events (
    event_id VARCHAR(20) PRIMARY KEY,

    subscription_id VARCHAR(20) NOT NULL,
    related_subscription_id VARCHAR(20),
    triggering_payment_id VARCHAR(20),

    event_type VARCHAR(40) NOT NULL,
    event_at TIMESTAMP NOT NULL,

    period_start DATE,
    period_end DATE,

    previous_seat_count INTEGER,
    new_seat_count INTEGER,

    event_reason VARCHAR(255),

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_event_subscription
        FOREIGN KEY (subscription_id)
        REFERENCES subscriptions(subscription_id),

    CONSTRAINT fk_event_related_subscription
        FOREIGN KEY (related_subscription_id)
        REFERENCES subscriptions(subscription_id),

    CONSTRAINT fk_event_payment
        FOREIGN KEY (triggering_payment_id)
        REFERENCES payments(payment_id),

    CONSTRAINT chk_subscription_event_type
        CHECK (
            event_type IN (
                'subscription_started',
                'renewed',
                'cancellation_requested',
                'cancellation_reversed',
                'plan_changed',
                'past_due_started',
                'past_due_resolved',
                'subscription_ended',
                'reactivated',
                'seats_changed'
            )
        ),

    CONSTRAINT chk_event_period
        CHECK (
            period_start IS NULL
            OR period_end IS NULL
            OR period_end >= period_start
        ),

    CONSTRAINT chk_previous_seat_count
        CHECK (
            previous_seat_count IS NULL
            OR previous_seat_count > 0
        ),

    CONSTRAINT chk_new_seat_count
        CHECK (
            new_seat_count IS NULL
            OR new_seat_count > 0
        ),

    -- Seat-count fields should only appear on seat-change events.
    CONSTRAINT chk_seat_change_event
        CHECK (
            event_type = 'seats_changed'
            OR (
                previous_seat_count IS NULL
                AND new_seat_count IS NULL
            )
        )
);


-- ============================================================
-- 8. ORGANISATION USERS
-- ============================================================

CREATE TABLE organisation_users (
    organisation_user_id VARCHAR(20) PRIMARY KEY,
    organisation_id VARCHAR(20) NOT NULL,
    subscription_id VARCHAR(20) NOT NULL,

    email VARCHAR(255) NOT NULL,

    activation_date DATE NOT NULL,
    deactivation_date DATE,

    user_status VARCHAR(20) NOT NULL,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_org_user_organisation
        FOREIGN KEY (organisation_id)
        REFERENCES organisations(organisation_id),

    CONSTRAINT fk_org_user_subscription
        FOREIGN KEY (subscription_id)
        REFERENCES subscriptions(subscription_id),

    CONSTRAINT chk_org_user_status
        CHECK (
            user_status IN (
                'active',
                'inactive'
            )
        ),

    CONSTRAINT chk_org_user_dates
        CHECK (
            deactivation_date IS NULL
            OR deactivation_date >= activation_date
        ),

    -- Prevent the same email from occupying the same
    -- organisation subscription more than once.
    CONSTRAINT uq_org_user_subscription_email
        UNIQUE (subscription_id, email)
);


-- ============================================================
-- 9. MARKETING TOUCHPOINTS
-- ============================================================

CREATE TABLE marketing_touchpoints (
    touchpoint_id VARCHAR(20) PRIMARY KEY,
    customer_id VARCHAR(20) NOT NULL,

    touchpoint_at TIMESTAMP NOT NULL,

    channel VARCHAR(50) NOT NULL,
    campaign_name VARCHAR(150),
    touchpoint_type VARCHAR(50) NOT NULL,

    attributed_cost NUMERIC(12,2),

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_touchpoint_customer
        FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id),

    CONSTRAINT chk_marketing_channel
        CHECK (
            channel IN (
                'Organic Search',
                'Direct',
                'Email',
                'Organic Social',
                'Paid Social',
                'Paid Search',
                'Referral',
                'Affiliate / Partner',
                'Campus Activation',
                'Promotional Campaign'
            )
        ),

    CONSTRAINT chk_touchpoint_type
        CHECK (
            touchpoint_type IN (
                'impression',
                'click',
                'visit',
                'email_open',
                'email_click',
                'referral',
                'campaign_response'
            )
        ),

    CONSTRAINT chk_attributed_cost
        CHECK (
            attributed_cost IS NULL
            OR attributed_cost >= 0
        )
);


-- ============================================================
-- 10. TRIALS
-- ============================================================

CREATE TABLE trials (
    trial_id VARCHAR(20) PRIMARY KEY,
    customer_id VARCHAR(20) NOT NULL,
    product_id VARCHAR(20) NOT NULL,

    trial_started_at TIMESTAMP NOT NULL,
    scheduled_end_at TIMESTAMP NOT NULL,
    actual_end_at TIMESTAMP,

    trial_status VARCHAR(20) NOT NULL,

    converted_subscription_id VARCHAR(20),

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_trial_customer
        FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id),

    CONSTRAINT fk_trial_product
        FOREIGN KEY (product_id)
        REFERENCES products(product_id),

    CONSTRAINT fk_trial_converted_subscription
        FOREIGN KEY (converted_subscription_id)
        REFERENCES subscriptions(subscription_id),

    -- One free trial per individual customer.
    CONSTRAINT uq_trial_customer
        UNIQUE (customer_id),

    CONSTRAINT chk_trial_status
        CHECK (
            trial_status IN (
                'active',
                'converted',
                'expired',
                'cancelled'
            )
        ),

    CONSTRAINT chk_trial_dates
        CHECK (
            scheduled_end_at > trial_started_at
        ),

    CONSTRAINT chk_trial_actual_end
        CHECK (
            actual_end_at IS NULL
            OR actual_end_at >= trial_started_at
        ),

    -- Maximum trial duration is seven days.
    CONSTRAINT chk_trial_max_duration
        CHECK (
            scheduled_end_at
            <= trial_started_at + INTERVAL '7 days'
        ),

    -- Converted trials must point to the resulting subscription.
    CONSTRAINT chk_trial_conversion
        CHECK (
            trial_status <> 'converted'
            OR converted_subscription_id IS NOT NULL
        )
);


-- ============================================================
-- 11. CUSTOMER ENGAGEMENT
-- ============================================================

CREATE TABLE customer_engagement (
    engagement_id VARCHAR(20) PRIMARY KEY,
    customer_id VARCHAR(20) NOT NULL,

    engagement_date DATE NOT NULL,

    sessions_count INTEGER NOT NULL,
    articles_viewed INTEGER NOT NULL,
    premium_articles_viewed INTEGER NOT NULL,
    epaper_opens INTEGER NOT NULL,
    reading_minutes NUMERIC(10,2) NOT NULL,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_engagement_customer
        FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id),

    CONSTRAINT chk_sessions_count
        CHECK (sessions_count >= 0),

    CONSTRAINT chk_articles_viewed
        CHECK (articles_viewed >= 0),

    CONSTRAINT chk_premium_articles_viewed
        CHECK (premium_articles_viewed >= 0),

    CONSTRAINT chk_epaper_opens
        CHECK (epaper_opens >= 0),

    CONSTRAINT chk_reading_minutes
        CHECK (reading_minutes >= 0),

    CONSTRAINT chk_premium_not_greater_than_articles
        CHECK (
            premium_articles_viewed <= articles_viewed
        ),

    -- One aggregate engagement row per customer per day.
    CONSTRAINT uq_customer_engagement_day
        UNIQUE (customer_id, engagement_date)
);


-- ============================================================
-- 12. SUPPORT INTERACTIONS
-- ============================================================

CREATE TABLE support_interactions (
    interaction_id VARCHAR(20) PRIMARY KEY,
    customer_id VARCHAR(20) NOT NULL,
    subscription_id VARCHAR(20),

    interaction_at TIMESTAMP NOT NULL,

    channel VARCHAR(30) NOT NULL,
    issue_category VARCHAR(50) NOT NULL,
    resolution_status VARCHAR(20) NOT NULL,

    resolved_at TIMESTAMP,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_support_customer
        FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id),

    CONSTRAINT fk_support_subscription
        FOREIGN KEY (subscription_id)
        REFERENCES subscriptions(subscription_id),

    CONSTRAINT chk_support_channel
        CHECK (
            channel IN (
                'email',
                'phone',
                'live_chat',
                'web_form'
            )
        ),

    CONSTRAINT chk_support_issue
        CHECK (
            issue_category IN (
                'billing',
                'payment',
                'access_login',
                'technical',
                'content',
                'subscription_change',
                'cancellation_enquiry',
                'other'
            )
        ),

    CONSTRAINT chk_resolution_status
        CHECK (
            resolution_status IN (
                'open',
                'in_progress',
                'resolved'
            )
        ),

    CONSTRAINT chk_support_resolution_date
        CHECK (
            resolved_at IS NULL
            OR resolved_at >= interaction_at
        ),

    CONSTRAINT chk_resolved_interaction
        CHECK (
            resolution_status <> 'resolved'
            OR resolved_at IS NOT NULL
        )
);


-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX idx_subscriptions_customer
    ON subscriptions(customer_id);

CREATE INDEX idx_subscriptions_organisation
    ON subscriptions(organisation_id);

CREATE INDEX idx_subscriptions_plan
    ON subscriptions(plan_id);

CREATE INDEX idx_subscriptions_status
    ON subscriptions(status);

CREATE INDEX idx_payments_subscription
    ON payments(subscription_id);

CREATE INDEX idx_payments_attempted_at
    ON payments(payment_attempted_at);

CREATE INDEX idx_payments_status
    ON payments(payment_status);

CREATE INDEX idx_subscription_events_subscription
    ON subscription_events(subscription_id);

CREATE INDEX idx_subscription_events_event_at
    ON subscription_events(event_at);

CREATE INDEX idx_touchpoints_customer
    ON marketing_touchpoints(customer_id);

CREATE INDEX idx_trials_customer
    ON trials(customer_id);

CREATE INDEX idx_engagement_customer_date
    ON customer_engagement(customer_id, engagement_date);

CREATE INDEX idx_support_customer
    ON support_interactions(customer_id);

CREATE INDEX idx_organisation_users_subscription
    ON organisation_users(subscription_id);


-- ============================================================
-- END OF SCHEMA
-- ============================================================
