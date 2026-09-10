"""
DAILYPULSE MEDIA
Subscription Intelligence

File: generate_acquisition_data.py

Purpose:
    Generate realistic synthetic customer acquisition journeys.

Generates:
    1. marketing_touchpoints.csv
    2. trial_staging.csv

Important:
    trial_staging.csv is NOT loaded directly into PostgreSQL.
    Converted trials require a subscription_id, which will only
    exist after the subscription lifecycle is generated.
"""

from pathlib import Path
import random

import numpy as np
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

RANDOM_SEED = 42

CUSTOMERS_PATH = Path("data/raw/customers.csv")
OUTPUT_DIR = Path("data/raw")

DATA_END_AT = pd.Timestamp("2026-08-20 23:59:59")

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

rng = np.random.default_rng(RANDOM_SEED)


# ============================================================
# FIRST-TOUCH CHANNEL ASSUMPTIONS
# ============================================================

FIRST_TOUCH_CHANNELS = {
    "Organic Search": 0.25,
    "Direct": 0.17,
    "Organic Social": 0.13,
    "Paid Social": 0.13,
    "Email": 0.09,
    "Paid Search": 0.08,
    "Referral": 0.06,
    "Affiliate / Partner": 0.04,
    "Promotional Campaign": 0.03,
    "Campus Activation": 0.02,
}


# Number of touchpoints in a customer's acquisition journey.
# Average is approximately 3.8 touchpoints.

TOUCHPOINT_COUNTS = {
    1: 0.08,
    2: 0.16,
    3: 0.22,
    4: 0.22,
    5: 0.16,
    6: 0.09,
    7: 0.05,
    8: 0.02,
}


# ============================================================
# TOUCHPOINT TYPES BY CHANNEL
# ============================================================

TOUCHPOINT_TYPES = {
    "Organic Search": [
        "click",
        "visit",
    ],
    "Direct": [
        "visit",
    ],
    "Email": [
        "email_open",
        "email_click",
        "visit",
    ],
    "Organic Social": [
        "impression",
        "click",
        "visit",
    ],
    "Paid Social": [
        "impression",
        "click",
        "visit",
    ],
    "Paid Search": [
        "impression",
        "click",
        "visit",
    ],
    "Referral": [
        "referral",
        "visit",
    ],
    "Affiliate / Partner": [
        "referral",
        "click",
        "visit",
    ],
    "Campus Activation": [
        "campaign_response",
        "visit",
    ],
    "Promotional Campaign": [
        "campaign_response",
        "click",
        "visit",
    ],
}


# ============================================================
# CAMPAIGN NAMES
# ============================================================

CAMPAIGNS = {
    "Paid Social": [
        "Stay Informed",
        "Premium Perspective",
        "DAILYPULSE Digital Access",
        "News Without Limits",
    ],
    "Paid Search": [
        "Digital News Subscription",
        "Premium News Search",
        "ePaper Search Acquisition",
    ],
    "Email": [
        "Morning Brief Conversion",
        "Reader Upgrade Series",
        "DAILYPULSE Newsletter Conversion",
    ],
    "Affiliate / Partner": [
        "Partner Reader Offer",
        "Member Access Campaign",
    ],
    "Campus Activation": [
        "Campus News Access",
        "Student Digital Drive",
        "DAILYPULSE Campus Week",
    ],
    "Promotional Campaign": [
        "Digital Access Offer",
        "Subscriber Month",
        "Premium Trial Campaign",
    ],
}


# ============================================================
# FOLLOW-UP CHANNEL LOGIC
# ============================================================

FOLLOWUP_CHANNELS = {
    "Organic Search": {
        "Organic Search": 0.35,
        "Direct": 0.30,
        "Email": 0.15,
        "Organic Social": 0.10,
        "Paid Social": 0.10,
    },

    "Direct": {
        "Direct": 0.45,
        "Organic Search": 0.20,
        "Email": 0.15,
        "Organic Social": 0.10,
        "Paid Social": 0.10,
    },

    "Organic Social": {
        "Organic Social": 0.35,
        "Direct": 0.25,
        "Organic Search": 0.15,
        "Email": 0.10,
        "Paid Social": 0.15,
    },

    "Paid Social": {
        "Paid Social": 0.35,
        "Direct": 0.30,
        "Organic Search": 0.15,
        "Email": 0.15,
        "Organic Social": 0.05,
    },

    "Email": {
        "Email": 0.40,
        "Direct": 0.30,
        "Organic Search": 0.15,
        "Organic Social": 0.10,
        "Paid Social": 0.05,
    },

    "Paid Search": {
        "Paid Search": 0.35,
        "Direct": 0.30,
        "Organic Search": 0.20,
        "Email": 0.10,
        "Paid Social": 0.05,
    },

    "Referral": {
        "Referral": 0.30,
        "Direct": 0.35,
        "Organic Search": 0.20,
        "Email": 0.10,
        "Organic Social": 0.05,
    },

    "Affiliate / Partner": {
        "Affiliate / Partner": 0.30,
        "Direct": 0.30,
        "Organic Search": 0.15,
        "Email": 0.15,
        "Paid Social": 0.10,
    },

    "Promotional Campaign": {
        "Promotional Campaign": 0.30,
        "Direct": 0.30,
        "Email": 0.20,
        "Paid Social": 0.15,
        "Organic Search": 0.05,
    },

    "Campus Activation": {
        "Campus Activation": 0.35,
        "Direct": 0.20,
        "Organic Social": 0.20,
        "Email": 0.15,
        "Organic Search": 0.10,
    },
}


# ============================================================
# TRIAL ASSUMPTIONS
# ============================================================

TRIAL_PROBABILITY_BY_FIRST_CHANNEL = {
    "Organic Search": 0.32,
    "Direct": 0.30,
    "Organic Social": 0.37,
    "Paid Social": 0.46,
    "Email": 0.40,
    "Paid Search": 0.44,
    "Referral": 0.34,
    "Affiliate / Partner": 0.42,
    "Promotional Campaign": 0.52,
    "Campus Activation": 0.70,
}


TRIAL_PRODUCTS = {
    "Digital Basic": "PROD001",
    "Digital Premium": "PROD002",
    "Student Digital": "PROD005",
}


BASE_TRIAL_PRODUCT_WEIGHTS = {
    "Digital Basic": 0.50,
    "Digital Premium": 0.35,
    "Student Digital": 0.15,
}


TRIAL_PRODUCT_WEIGHTS_BY_CHANNEL = {
    "Campus Activation": {
        "Digital Basic": 0.20,
        "Digital Premium": 0.05,
        "Student Digital": 0.75,
    },

    "Paid Search": {
        "Digital Basic": 0.40,
        "Digital Premium": 0.45,
        "Student Digital": 0.15,
    },

    "Promotional Campaign": {
        "Digital Basic": 0.45,
        "Digital Premium": 0.40,
        "Student Digital": 0.15,
    },
}


BASE_CONVERSION_PROBABILITY = {
    "Digital Basic": 0.48,
    "Digital Premium": 0.58,
    "Student Digital": 0.52,
}


CONVERSION_CHANNEL_ADJUSTMENT = {
    "Organic Search": 0.05,
    "Referral": 0.06,
    "Direct": 0.02,
    "Email": 0.03,
    "Organic Social": 0.00,
    "Paid Search": 0.01,
    "Affiliate / Partner": 0.00,
    "Paid Social": -0.04,
    "Promotional Campaign": -0.06,
    "Campus Activation": 0.03,
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def weighted_choice(weight_map):
    """Select one item using predefined probabilities."""

    values = list(weight_map.keys())
    probabilities = list(weight_map.values())

    return rng.choice(
        values,
        p=probabilities
    )


def generate_signup_timestamp(signup_date):
    """
    Convert a signup DATE into a plausible signup timestamp.
    This timestamp is only used internally for acquisition logic.
    """

    signup_date = pd.Timestamp(signup_date)

    hour = int(
        rng.integers(7, 23)
    )

    minute = int(
        rng.integers(0, 60)
    )

    return signup_date + pd.Timedelta(
        hours=hour,
        minutes=minute
    )


def generate_touchpoint_times(
    signup_at,
    number_of_touchpoints
):
    """
    Generate ordered marketing interactions occurring before
    or at customer signup.

    Most acquisition journeys begin within 45 days of signup.
    """

    days_before_signup = int(
        np.clip(
            rng.gamma(
                shape=2.0,
                scale=6.0
            ),
            1,
            45
        )
    )

    first_touch_at = (
        signup_at
        - pd.Timedelta(days=days_before_signup)
    )

    if number_of_touchpoints == 1:
        return [first_touch_at]

    fractions = np.sort(
        rng.uniform(
            0,
            1,
            size=number_of_touchpoints
        )
    )

    journey_length = (
        signup_at - first_touch_at
    )

    timestamps = [
        first_touch_at
        + journey_length * float(fraction)
        for fraction in fractions
    ]

    timestamps[0] = first_touch_at

    return timestamps


def get_campaign_name(channel):
    """Return a campaign name only where one is meaningful."""

    if channel not in CAMPAIGNS:
        return None

    return rng.choice(
        CAMPAIGNS[channel]
    )


def generate_attributed_cost(
    channel,
    touchpoint_type
):
    """
    Generate plausible per-touchpoint attributed marketing cost
    in KES.

    These are simulation assumptions rather than actual media rates.
    """

    if channel in [
        "Organic Search",
        "Direct",
        "Organic Social",
        "Referral",
    ]:
        return 0.00

    if channel == "Email":
        return round(
            float(
                rng.uniform(0.25, 2.00)
            ),
            2
        )

    if channel == "Paid Social":

        if touchpoint_type == "impression":
            low, high = 0.20, 2.00
        else:
            low, high = 15.00, 85.00

    elif channel == "Paid Search":

        if touchpoint_type == "impression":
            low, high = 0.50, 3.00
        else:
            low, high = 25.00, 130.00

    elif channel == "Affiliate / Partner":
        low, high = 15.00, 90.00

    elif channel == "Campus Activation":
        low, high = 10.00, 70.00

    elif channel == "Promotional Campaign":
        low, high = 10.00, 65.00

    else:
        return None

    return round(
        float(
            rng.uniform(low, high)
        ),
        2
    )


# ============================================================
# READ CUSTOMER BASE
# ============================================================

def read_customers():
    """Read the approved customer base."""

    if not CUSTOMERS_PATH.exists():
        raise FileNotFoundError(
            f"{CUSTOMERS_PATH} does not exist. "
            "Run generate_base_data.py first."
        )

    customers_df = pd.read_csv(
        CUSTOMERS_PATH
    )

    customers_df["signup_date"] = pd.to_datetime(
        customers_df["signup_date"]
    )

    return customers_df


# ============================================================
# GENERATE MARKETING TOUCHPOINTS
# ============================================================

def generate_marketing_touchpoints(
    customers_df
):
    """
    Generate each customer's pre-signup marketing journey.

    Returns:
        marketing_touchpoints_df
        first_channel_by_customer
    """

    records = []

    first_channel_by_customer = {}

    touchpoint_counter = 1

    for customer in customers_df.itertuples(
        index=False
    ):

        signup_at = generate_signup_timestamp(
            customer.signup_date
        )

        number_of_touchpoints = int(
            weighted_choice(
                TOUCHPOINT_COUNTS
            )
        )

        first_channel = weighted_choice(
            FIRST_TOUCH_CHANNELS
        )

        first_channel_by_customer[
            customer.customer_id
        ] = first_channel

        touchpoint_times = generate_touchpoint_times(
            signup_at,
            number_of_touchpoints
        )

        channels = [
            first_channel
        ]

        for _ in range(
            number_of_touchpoints - 1
        ):

            followup_channel = weighted_choice(
                FOLLOWUP_CHANNELS[
                    first_channel
                ]
            )

            channels.append(
                followup_channel
            )

        for touchpoint_at, channel in zip(
            touchpoint_times,
            channels
        ):

            touchpoint_type = rng.choice(
                TOUCHPOINT_TYPES[channel]
            )

            campaign_name = get_campaign_name(
                channel
            )

            attributed_cost = generate_attributed_cost(
                channel,
                touchpoint_type
            )

            created_at = (
                touchpoint_at
                + pd.Timedelta(
                    seconds=int(
                        rng.integers(1, 120)
                    )
                )
            )

            records.append({
                "touchpoint_id":
                    f"TP{touchpoint_counter:07d}",

                "customer_id":
                    customer.customer_id,

                "touchpoint_at":
                    touchpoint_at,

                "channel":
                    channel,

                "campaign_name":
                    campaign_name,

                "touchpoint_type":
                    touchpoint_type,

                "attributed_cost":
                    attributed_cost,

                "created_at":
                    created_at,
            })

            touchpoint_counter += 1

    touchpoints_df = pd.DataFrame(
        records
    )

    return (
        touchpoints_df,
        first_channel_by_customer
    )


# ============================================================
# TRIAL PRODUCT SELECTION
# ============================================================

def select_trial_product(
    first_channel
):
    """Choose a trial product based partly on acquisition source."""

    product_weights = (
        TRIAL_PRODUCT_WEIGHTS_BY_CHANNEL
        .get(
            first_channel,
            BASE_TRIAL_PRODUCT_WEIGHTS
        )
    )

    product_name = weighted_choice(
        product_weights
    )

    return (
        TRIAL_PRODUCTS[product_name],
        product_name
    )


# ============================================================
# GENERATE TRIAL STAGING DATA
# ============================================================

def generate_trial_staging(
    customers_df,
    first_channel_by_customer
):
    """
    Generate trial behaviour without loading it into the final
    trials table.

    Converted trials cannot yet reference a subscription_id,
    because subscriptions are generated in the next phase.
    """

    records = []

    trial_counter = 1

    for customer in customers_df.itertuples(
        index=False
    ):

        first_channel = (
            first_channel_by_customer[
                customer.customer_id
            ]
        )

        trial_probability = (
            TRIAL_PROBABILITY_BY_FIRST_CHANNEL[
                first_channel
            ]
        )

        if rng.random() > trial_probability:
            continue

        signup_at = generate_signup_timestamp(
            customer.signup_date
        )

        available_hours = max(
            0,
            int(
                (
                    DATA_END_AT - signup_at
                ).total_seconds()
                // 3600
            )
        )

        if available_hours <= 0:
            trial_started_at = signup_at

        else:

            max_delay_hours = min(
                available_hours,
                5 * 24
            )

            trial_started_at = (
                signup_at
                + pd.Timedelta(
                    hours=int(
                        rng.integers(
                            0,
                            max_delay_hours + 1
                        )
                    )
                )
            )

        if trial_started_at > DATA_END_AT:
            trial_started_at = DATA_END_AT

        scheduled_end_at = (
            trial_started_at
            + pd.Timedelta(days=7)
        )

        product_id, product_name = (
            select_trial_product(
                first_channel
            )
        )

        conversion_probability = (
            BASE_CONVERSION_PROBABILITY[
                product_name
            ]
            + CONVERSION_CHANNEL_ADJUSTMENT[
                first_channel
            ]
        )

        conversion_probability = float(
            np.clip(
                conversion_probability,
                0.20,
                0.80
            )
        )

        cancellation_probability = 0.05

        draw = rng.random()

        actual_end_at = pd.NaT

        if draw < cancellation_probability:

            cancellation_hours = int(
                rng.integers(
                    4,
                    5 * 24
                )
            )

            candidate_end = (
                trial_started_at
                + pd.Timedelta(
                    hours=cancellation_hours
                )
            )

            if candidate_end <= DATA_END_AT:

                intended_outcome = "cancelled"

                actual_end_at = min(
                    candidate_end,
                    scheduled_end_at
                )

            elif scheduled_end_at <= DATA_END_AT:

                intended_outcome = "expired"
                actual_end_at = scheduled_end_at

            else:

                intended_outcome = "active"

        elif draw < (
            cancellation_probability
            + conversion_probability
        ):

            conversion_hours = int(
                rng.integers(
                    12,
                    7 * 24
                )
            )

            candidate_end = (
                trial_started_at
                + pd.Timedelta(
                    hours=conversion_hours
                )
            )

            candidate_end = min(
                candidate_end,
                scheduled_end_at
            )

            if candidate_end <= DATA_END_AT:

                intended_outcome = "converted"
                actual_end_at = candidate_end

            elif scheduled_end_at <= DATA_END_AT:

                intended_outcome = "expired"
                actual_end_at = scheduled_end_at

            else:

                intended_outcome = "active"

        elif scheduled_end_at <= DATA_END_AT:

            intended_outcome = "expired"
            actual_end_at = scheduled_end_at

        else:

            intended_outcome = "active"

        created_at = (
            trial_started_at
            + pd.Timedelta(
                seconds=int(
                    rng.integers(1, 120)
                )
            )
        )

        records.append({
            "trial_id":
                f"TRIAL{trial_counter:06d}",

            "customer_id":
                customer.customer_id,

            "product_id":
                product_id,

            "product_name":
                product_name,

            "trial_started_at":
                trial_started_at,

            "scheduled_end_at":
                scheduled_end_at,

            "actual_end_at":
                actual_end_at,

            "intended_outcome":
                intended_outcome,

            "acquisition_first_channel":
                first_channel,

            "created_at":
                created_at,
        })

        trial_counter += 1

    return pd.DataFrame(
        records
    )


# ============================================================
# VALIDATION
# ============================================================

def validate_marketing_touchpoints(
    touchpoints_df,
    customers_df
):
    """Validate generated marketing acquisition data."""

    if not touchpoints_df[
        "touchpoint_id"
    ].is_unique:

        raise ValueError(
            "Duplicate touchpoint IDs detected."
        )

    valid_customer_ids = set(
        customers_df["customer_id"]
    )

    if not set(
        touchpoints_df["customer_id"]
    ).issubset(
        valid_customer_ids
    ):
        raise ValueError(
            "Unknown customer_id found in marketing touchpoints."
        )

    touchpoint_counts = (
        touchpoints_df
        .groupby("customer_id")
        .size()
    )

    if len(touchpoint_counts) != len(
        customers_df
    ):
        raise ValueError(
            "Every customer must have at least one marketing touchpoint."
        )

    if touchpoint_counts.min() < 1:
        raise ValueError(
            "Customer with zero touchpoints detected."
        )

    if touchpoint_counts.max() > 8:
        raise ValueError(
            "Customer exceeds maximum acquisition journey length."
        )

    if (
        touchpoints_df["attributed_cost"]
        .dropna()
        .lt(0)
        .any()
    ):
        raise ValueError(
            "Negative attributed marketing cost detected."
        )


def validate_trial_staging(
    trials_df,
    customers_df
):
    """Validate trial staging data."""

    if not trials_df["trial_id"].is_unique:
        raise ValueError(
            "Duplicate trial IDs detected."
        )

    if not trials_df["customer_id"].is_unique:
        raise ValueError(
            "A customer received more than one trial."
        )

    valid_customers = set(
        customers_df["customer_id"]
    )

    if not set(
        trials_df["customer_id"]
    ).issubset(
        valid_customers
    ):
        raise ValueError(
            "Unknown customer_id detected in trial staging."
        )

    allowed_products = set(
        TRIAL_PRODUCTS.values()
    )

    if not set(
        trials_df["product_id"]
    ).issubset(
        allowed_products
    ):
        raise ValueError(
            "Non-trial-eligible product detected."
        )

    trial_duration = (
        pd.to_datetime(
            trials_df["scheduled_end_at"]
        )
        -
        pd.to_datetime(
            trials_df["trial_started_at"]
        )
    )

    if (
        trial_duration
        > pd.Timedelta(days=7)
    ).any():
        raise ValueError(
            "Trial longer than seven days detected."
        )

    allowed_outcomes = {
        "converted",
        "expired",
        "cancelled",
        "active",
    }

    if not set(
        trials_df["intended_outcome"]
    ).issubset(
        allowed_outcomes
    ):
        raise ValueError(
            "Invalid trial outcome detected."
        )

    # We expect a meaningful but not excessive proportion
    # of the 5,000-customer base to trial.
    if not (
        1_500
        <= len(trials_df)
        <= 2_200
    ):
        raise ValueError(
            f"Unexpected trial volume: {len(trials_df):,}"
        )


# ============================================================
# SAVE DATA
# ============================================================

def save_data(
    touchpoints_df,
    trials_df
):
    """Save acquisition datasets."""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    touchpoints_path = (
        OUTPUT_DIR
        / "marketing_touchpoints.csv"
    )

    trials_path = (
        OUTPUT_DIR
        / "trial_staging.csv"
    )

    touchpoints_df.to_csv(
        touchpoints_path,
        index=False
    )

    trials_df.to_csv(
        trials_path,
        index=False
    )

    return (
        touchpoints_path,
        trials_path
    )


# ============================================================
# SUMMARY
# ============================================================

def print_summary(
    touchpoints_df,
    trials_df
):
    """Print acquisition-generation summary."""

    customer_touchpoints = (
        touchpoints_df
        .groupby("customer_id")
        .size()
    )

    first_touch = (
        touchpoints_df
        .sort_values("touchpoint_at")
        .groupby("customer_id")
        .first()
    )

    print("\n" + "=" * 65)
    print(
        "DAILYPULSE MEDIA — ACQUISITION DATA GENERATION COMPLETE"
    )
    print("=" * 65)

    print(
        f"\nMarketing touchpoints generated: "
        f"{len(touchpoints_df):,}"
    )

    print(
        "Average touchpoints per customer: "
        f"{customer_touchpoints.mean():.2f}"
    )

    print("\nFirst-touch channel distribution (%):")

    print(
        first_touch["channel"]
        .value_counts(normalize=True)
        .mul(100)
        .round(1)
        .astype(str)
        + "%"
    )

    print(
        f"\nCustomers receiving trials: "
        f"{len(trials_df):,}"
    )

    print(
        "Trial share of customer base: "
        f"{len(trials_df) / 5000 * 100:.1f}%"
    )

    print("\nTrial product mix:")

    print(
        trials_df["product_name"]
        .value_counts()
    )

    print("\nTrial outcomes:")

    print(
        trials_df["intended_outcome"]
        .value_counts()
    )

    print("\nTrial outcomes (%):")

    print(
        trials_df["intended_outcome"]
        .value_counts(normalize=True)
        .mul(100)
        .round(1)
        .astype(str)
        + "%"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    customers_df = read_customers()

    (
        touchpoints_df,
        first_channel_by_customer
    ) = generate_marketing_touchpoints(
        customers_df
    )

    trials_df = generate_trial_staging(
        customers_df,
        first_channel_by_customer
    )

    validate_marketing_touchpoints(
        touchpoints_df,
        customers_df
    )

    validate_trial_staging(
        trials_df,
        customers_df
    )

    (
        touchpoints_path,
        trials_path
    ) = save_data(
        touchpoints_df,
        trials_df
    )

    print_summary(
        touchpoints_df,
        trials_df
    )

    print("\nFiles created:")
    print(
        f"- {touchpoints_path}"
    )
    print(
        f"- {trials_path}"
    )


if __name__ == "__main__":
    main()