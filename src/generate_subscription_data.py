"""
DAILYPULSE MEDIA
Subscription Intelligence

File: generate_subscription_data.py

Purpose:
    Generate realistic subscription histories for individual
    customers and organisations.

Also resolves converted trial staging records to the actual
paid subscription created from the trial.

Generates:
    1. subscriptions.csv
    2. trials.csv

Payments and detailed subscription events are generated
in the next commercial-lifecycle step.
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
ORGANISATIONS_PATH = Path("data/raw/organisations.csv")
TOUCHPOINTS_PATH = Path("data/raw/marketing_touchpoints.csv")
TRIAL_STAGING_PATH = Path("data/raw/trial_staging.csv")

OUTPUT_DIR = Path("data/raw")

DATA_END_DATE = pd.Timestamp("2026-08-20")

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

rng = np.random.default_rng(RANDOM_SEED)


# ============================================================
# PLAN CATALOGUE
# Must match sql/02_seed_reference_data.sql
# ============================================================

PLAN_CATALOG = {

    "PLN001": {
        "product_id": "PROD001",
        "product_name": "Digital Basic",
        "frequency": "Daily",
        "price": 30.00,
    },

    "PLN002": {
        "product_id": "PROD001",
        "product_name": "Digital Basic",
        "frequency": "Weekly",
        "price": 150.00,
    },

    "PLN003": {
        "product_id": "PROD001",
        "product_name": "Digital Basic",
        "frequency": "Monthly",
        "price": 500.00,
    },

    "PLN004": {
        "product_id": "PROD001",
        "product_name": "Digital Basic",
        "frequency": "Annual",
        "price": 5000.00,
    },

    "PLN005": {
        "product_id": "PROD002",
        "product_name": "Digital Premium",
        "frequency": "Weekly",
        "price": 250.00,
    },

    "PLN006": {
        "product_id": "PROD002",
        "product_name": "Digital Premium",
        "frequency": "Monthly",
        "price": 800.00,
    },

    "PLN007": {
        "product_id": "PROD002",
        "product_name": "Digital Premium",
        "frequency": "Annual",
        "price": 8000.00,
    },

    "PLN008": {
        "product_id": "PROD003",
        "product_name": "ePaper",
        "frequency": "Daily",
        "price": 60.00,
    },

    "PLN009": {
        "product_id": "PROD003",
        "product_name": "ePaper",
        "frequency": "Weekly",
        "price": 300.00,
    },

    "PLN010": {
        "product_id": "PROD003",
        "product_name": "ePaper",
        "frequency": "Monthly",
        "price": 1000.00,
    },

    "PLN011": {
        "product_id": "PROD003",
        "product_name": "ePaper",
        "frequency": "Annual",
        "price": 10000.00,
    },

    "PLN012": {
        "product_id": "PROD004",
        "product_name": "Weekend ePaper",
        "frequency": "Weekly",
        "price": 150.00,
    },

    "PLN013": {
        "product_id": "PROD004",
        "product_name": "Weekend ePaper",
        "frequency": "Monthly",
        "price": 500.00,
    },

    "PLN014": {
        "product_id": "PROD005",
        "product_name": "Student Digital",
        "frequency": "Weekly",
        "price": 100.00,
    },

    "PLN015": {
        "product_id": "PROD005",
        "product_name": "Student Digital",
        "frequency": "Monthly",
        "price": 300.00,
    },

    "PLN016": {
        "product_id": "PROD005",
        "product_name": "Student Digital",
        "frequency": "Annual",
        "price": 3000.00,
    },

    "PLN017": {
        "product_id": "PROD006",
        "product_name": "Corporate ePaper",
        "frequency": "Monthly",
        "price": 800.00,
    },

    "PLN018": {
        "product_id": "PROD006",
        "product_name": "Corporate ePaper",
        "frequency": "Annual",
        "price": 8000.00,
    },
}


# ============================================================
# PLAN OPTIONS BY PRODUCT
# ============================================================

PRODUCT_PLAN_WEIGHTS = {

    "Digital Basic": {
        "PLN001": 0.08,
        "PLN002": 0.20,
        "PLN003": 0.52,
        "PLN004": 0.20,
    },

    "Digital Premium": {
        "PLN005": 0.15,
        "PLN006": 0.60,
        "PLN007": 0.25,
    },

    "ePaper": {
        "PLN008": 0.08,
        "PLN009": 0.17,
        "PLN010": 0.50,
        "PLN011": 0.25,
    },

    "Weekend ePaper": {
        "PLN012": 0.45,
        "PLN013": 0.55,
    },

    "Student Digital": {
        "PLN014": 0.25,
        "PLN015": 0.60,
        "PLN016": 0.15,
    },
}


# ============================================================
# DIRECT SUBSCRIPTION PRODUCT MIX BY CHANNEL
# ============================================================

PRODUCT_WEIGHTS_BY_CHANNEL = {

    "Organic Search": {
        "Digital Basic": 0.28,
        "Digital Premium": 0.25,
        "ePaper": 0.22,
        "Weekend ePaper": 0.10,
        "Student Digital": 0.15,
    },

    "Direct": {
        "Digital Basic": 0.25,
        "Digital Premium": 0.25,
        "ePaper": 0.25,
        "Weekend ePaper": 0.15,
        "Student Digital": 0.10,
    },

    "Organic Social": {
        "Digital Basic": 0.32,
        "Digital Premium": 0.25,
        "ePaper": 0.15,
        "Weekend ePaper": 0.10,
        "Student Digital": 0.18,
    },

    "Paid Social": {
        "Digital Basic": 0.35,
        "Digital Premium": 0.30,
        "ePaper": 0.14,
        "Weekend ePaper": 0.08,
        "Student Digital": 0.13,
    },

    "Email": {
        "Digital Basic": 0.25,
        "Digital Premium": 0.30,
        "ePaper": 0.25,
        "Weekend ePaper": 0.12,
        "Student Digital": 0.08,
    },

    "Paid Search": {
        "Digital Basic": 0.24,
        "Digital Premium": 0.30,
        "ePaper": 0.27,
        "Weekend ePaper": 0.10,
        "Student Digital": 0.09,
    },

    "Referral": {
        "Digital Basic": 0.25,
        "Digital Premium": 0.30,
        "ePaper": 0.22,
        "Weekend ePaper": 0.10,
        "Student Digital": 0.13,
    },

    "Affiliate / Partner": {
        "Digital Basic": 0.28,
        "Digital Premium": 0.27,
        "ePaper": 0.22,
        "Weekend ePaper": 0.11,
        "Student Digital": 0.12,
    },

    "Promotional Campaign": {
        "Digital Basic": 0.38,
        "Digital Premium": 0.28,
        "ePaper": 0.14,
        "Weekend ePaper": 0.08,
        "Student Digital": 0.12,
    },

    "Campus Activation": {
        "Digital Basic": 0.14,
        "Digital Premium": 0.06,
        "ePaper": 0.05,
        "Weekend ePaper": 0.05,
        "Student Digital": 0.70,
    },
}


# ============================================================
# DIRECT SUBSCRIPTION PROBABILITY
# ============================================================

DIRECT_SUBSCRIPTION_PROBABILITY = {
    "Organic Search": 0.62,
    "Direct": 0.58,
    "Organic Social": 0.50,
    "Paid Social": 0.48,
    "Email": 0.62,
    "Paid Search": 0.65,
    "Referral": 0.68,
    "Affiliate / Partner": 0.60,
    "Promotional Campaign": 0.45,
    "Campus Activation": 0.60,
}


# ============================================================
# ORGANISATION SUBSCRIPTION PROBABILITY
# ============================================================

ORGANISATION_SUBSCRIPTION_PROBABILITY = {
    "Corporate": 0.85,
    "University": 0.90,
    "NGO": 0.70,
    "Government": 0.75,
    "Professional Association": 0.75,
    "Other": 0.60,
}


# ============================================================
# HELPERS
# ============================================================

def weighted_choice(weight_map):
    """Choose one value using predefined probabilities."""

    values = list(weight_map.keys())
    probabilities = list(weight_map.values())

    return rng.choice(
        values,
        p=probabilities
    )


def next_period_start(date, frequency):
    """Calculate the next billing-period start using calendar logic."""

    date = pd.Timestamp(date)

    if frequency == "Daily":
        return date + pd.Timedelta(days=1)

    if frequency == "Weekly":
        return date + pd.Timedelta(days=7)

    if frequency == "Monthly":
        return date + pd.DateOffset(months=1)

    if frequency == "Annual":
        return date + pd.DateOffset(years=1)

    raise ValueError(
        f"Unknown billing frequency: {frequency}"
    )


def period_end_from_start(date, frequency):
    """Calculate inclusive billing-period end date."""

    start = pd.Timestamp(date)

    next_start = next_period_start(
        start,
        frequency
    )

    return next_start - pd.Timedelta(days=1)


def choose_plan_for_product(product_name):
    """Select a billing plan for a known product."""

    return weighted_choice(
        PRODUCT_PLAN_WEIGHTS[
            product_name
        ]
    )


def choose_direct_plan(first_channel):
    """Select product and plan for a direct subscriber."""

    product_name = weighted_choice(
        PRODUCT_WEIGHTS_BY_CHANNEL[
            first_channel
        ]
    )

    return choose_plan_for_product(
        product_name
    )


# ============================================================
# READ INPUT DATA
# ============================================================

def read_inputs():

    customers = pd.read_csv(
        CUSTOMERS_PATH
    )

    organisations = pd.read_csv(
        ORGANISATIONS_PATH
    )

    touchpoints = pd.read_csv(
        TOUCHPOINTS_PATH
    )

    trials = pd.read_csv(
        TRIAL_STAGING_PATH
    )

    customers["signup_date"] = pd.to_datetime(
        customers["signup_date"]
    )

    organisations["signup_date"] = pd.to_datetime(
        organisations["signup_date"]
    )

    touchpoints["touchpoint_at"] = pd.to_datetime(
        touchpoints["touchpoint_at"]
    )

    trials["trial_started_at"] = pd.to_datetime(
        trials["trial_started_at"]
    )

    trials["scheduled_end_at"] = pd.to_datetime(
        trials["scheduled_end_at"]
    )

    trials["actual_end_at"] = pd.to_datetime(
        trials["actual_end_at"]
    )

    return (
        customers,
        organisations,
        touchpoints,
        trials
    )


# ============================================================
# FIRST-TOUCH CHANNEL LOOKUP
# ============================================================

def build_first_channel_lookup(
    touchpoints
):

    first_touch = (
        touchpoints
        .sort_values("touchpoint_at")
        .groupby("customer_id")
        .first()
    )

    return first_touch[
        "channel"
    ].to_dict()


# ============================================================
# SUBSCRIPTION TENURE ASSUMPTIONS
# ============================================================

def continuation_probability(
    plan_id,
    first_channel,
    from_trial
):
    """
    Probability that a subscriber continues after
    a completed billing period.

    Longer-term plans have stronger retention.
    """

    frequency = PLAN_CATALOG[
        plan_id
    ]["frequency"]

    base = {
        "Daily": 0.70,
        "Weekly": 0.78,
        "Monthly": 0.90,
        "Annual": 0.92,
    }[frequency]

    channel_adjustment = {
        "Organic Search": 0.02,
        "Referral": 0.03,
        "Direct": 0.01,
        "Email": 0.01,
        "Paid Search": 0.00,
        "Organic Social": 0.00,
        "Affiliate / Partner": -0.01,
        "Paid Social": -0.03,
        "Promotional Campaign": -0.05,
        "Campus Activation": -0.01,
    }[first_channel]

    if from_trial:
        base += 0.02

    return float(
        np.clip(
            base + channel_adjustment,
            0.55,
            0.97
        )
    )


# ============================================================
# PLAN CHANGE LOGIC
# ============================================================

def plan_change_probability(
    plan_id
):
    """Chance of changing plan at a renewal boundary."""

    frequency = PLAN_CATALOG[
        plan_id
    ]["frequency"]

    return {
        "Daily": 0.04,
        "Weekly": 0.035,
        "Monthly": 0.045,
        "Annual": 0.025,
    }[frequency]


def choose_next_plan(
    current_plan_id
):
    """Choose a realistic upgrade/downgrade path."""

    transitions = {

        "PLN001": ["PLN002", "PLN003", "PLN005"],
        "PLN002": ["PLN003", "PLN004", "PLN005"],
        "PLN003": ["PLN004", "PLN006", "PLN010"],
        "PLN004": ["PLN007", "PLN011"],

        "PLN005": ["PLN006", "PLN003"],
        "PLN006": ["PLN007", "PLN003", "PLN010"],
        "PLN007": ["PLN004", "PLN011"],

        "PLN008": ["PLN009", "PLN010", "PLN012"],
        "PLN009": ["PLN010", "PLN011", "PLN013"],
        "PLN010": ["PLN011", "PLN006", "PLN013"],
        "PLN011": ["PLN010", "PLN007"],

        "PLN012": ["PLN013", "PLN009"],
        "PLN013": ["PLN010", "PLN012"],

        "PLN014": ["PLN015", "PLN003"],
        "PLN015": ["PLN016", "PLN003", "PLN006"],
        "PLN016": ["PLN004", "PLN007"],
    }

    candidates = transitions.get(
        current_plan_id
    )

    if not candidates:
        return current_plan_id

    return rng.choice(
        candidates
    )


# ============================================================
# SIMULATE ONE INDIVIDUAL SUBSCRIPTION SEGMENT
# ============================================================

def simulate_individual_segment(
    subscription_id,
    customer_id,
    plan_id,
    start_date,
    first_channel,
    from_trial
):
    """
    Simulate one continuous subscription period on one plan.

    Renewals remain within the same subscription record.
    """

    plan = PLAN_CATALOG[
        plan_id
    ]

    frequency = plan["frequency"]

    current_start = pd.Timestamp(
        start_date
    ).normalize()

    current_end = period_end_from_start(
        current_start,
        frequency
    )

    continuation = continuation_probability(
        plan_id,
        first_channel,
        from_trial
    )

    number_of_completed_periods = 0

    outcome = "active"
    end_reason = None
    end_date = pd.NaT
    next_plan_id = None

    max_cycles = 550

    for _ in range(max_cycles):

        if current_start > DATA_END_DATE:
            break

        if current_end >= DATA_END_DATE:

            outcome = "active"
            break

        number_of_completed_periods += 1

        # Plan migration becomes possible after at least
        # some history exists.
        eligible_for_plan_change = (
            number_of_completed_periods >= 2
        )

        if (
            eligible_for_plan_change
            and rng.random()
            < plan_change_probability(
                plan_id
            )
        ):

            outcome = "ended"
            end_reason = "plan_change"
            end_date = current_end

            next_plan_id = choose_next_plan(
                plan_id
            )

            break

        if rng.random() > continuation:

            outcome = "ended"

            # Most customer-led endings are voluntary;
            # a smaller share simply do not renew.
            if rng.random() < 0.72:
                end_reason = "voluntary_cancel"
            else:
                end_reason = "non_renewal"

            end_date = current_end

            break

        current_start = next_period_start(
            current_start,
            frequency
        )

        current_end = period_end_from_start(
            current_start,
            frequency
        )

    auto_renew = (
        outcome == "active"
    )

    cancellation_requested_at = pd.NaT

    if (
        outcome == "ended"
        and end_reason == "voluntary_cancel"
    ):

        request_days_before_end = int(
            rng.integers(1, 8)
        )

        cancellation_requested_at = (
            pd.Timestamp(end_date)
            - pd.Timedelta(
                days=request_days_before_end
            )
            + pd.Timedelta(
                hours=int(
                    rng.integers(8, 21)
                )
            )
        )

        if (
            cancellation_requested_at
            < pd.Timestamp(start_date)
        ):
            cancellation_requested_at = (
                pd.Timestamp(start_date)
                + pd.Timedelta(hours=12)
            )

    # Some currently active customers have already
    # requested cancellation for the next renewal.
    if (
        outcome == "active"
        and current_start <= DATA_END_DATE
        and rng.random() < 0.035
    ):

        cancellation_requested_at = (
            DATA_END_DATE
            - pd.Timedelta(
                days=int(
                    rng.integers(0, 10)
                )
            )
            + pd.Timedelta(
                hours=int(
                    rng.integers(8, 21)
                )
            )
        )

        auto_renew = False

    record = {
        "subscription_id": subscription_id,
        "customer_id": customer_id,
        "organisation_id": None,
        "plan_id": plan_id,
        "subscription_start_date":
            pd.Timestamp(start_date).date(),
        "current_period_start":
            current_start.date(),
        "current_period_end":
            current_end.date(),
        "subscription_end_date":
            (
                pd.Timestamp(end_date).date()
                if pd.notna(end_date)
                else None
            ),
        "status":
            "ended"
            if outcome == "ended"
            else "active",
        "auto_renew":
            auto_renew,
        "cancellation_requested_at":
            cancellation_requested_at,
        "end_reason":
            end_reason,
        "seats_purchased":
            None,
        "created_at":
            pd.Timestamp(start_date)
            + pd.Timedelta(
                hours=int(
                    rng.integers(0, 24)
                )
            ),
    }

    return (
        record,
        next_plan_id
    )


# ============================================================
# DETERMINE INDIVIDUAL SUBSCRIPTION START
# ============================================================

def determine_initial_subscription(
    customer,
    first_channel,
    trial_row
):
    """
    Determine whether and when a customer first subscribes.
    """

    signup_date = pd.Timestamp(
        customer.signup_date
    )

    # Trial converter: subscription begins when trial converts.
    if (
        trial_row is not None
        and trial_row.intended_outcome == "converted"
    ):

        product_name = (
            trial_row.product_name
        )

        plan_id = choose_plan_for_product(
            product_name
        )

        return (
            plan_id,
            pd.Timestamp(
                trial_row.actual_end_at
            ).normalize(),
            True,
            trial_row.trial_id,
        )

    # Expired trials can still subscribe later.
    if (
        trial_row is not None
        and trial_row.intended_outcome == "expired"
    ):

        if rng.random() > 0.10:
            return None

        start_date = (
            pd.Timestamp(
                trial_row.actual_end_at
            )
            + pd.Timedelta(
                days=int(
                    rng.integers(2, 46)
                )
            )
        ).normalize()

        if start_date > DATA_END_DATE:
            return None

        plan_id = choose_direct_plan(
            first_channel
        )

        return (
            plan_id,
            start_date,
            False,
            None,
        )

    # Cancelled trials occasionally come back later.
    if (
        trial_row is not None
        and trial_row.intended_outcome == "cancelled"
    ):

        if rng.random() > 0.03:
            return None

        start_date = (
            pd.Timestamp(
                trial_row.actual_end_at
            )
            + pd.Timedelta(
                days=int(
                    rng.integers(7, 61)
                )
            )
        ).normalize()

        if start_date > DATA_END_DATE:
            return None

        return (
            choose_direct_plan(
                first_channel
            ),
            start_date,
            False,
            None,
        )

    # Active trials have not reached an outcome yet.
    if (
        trial_row is not None
        and trial_row.intended_outcome == "active"
    ):
        return None

    # Customers without a trial may subscribe directly.
    probability = (
        DIRECT_SUBSCRIPTION_PROBABILITY[
            first_channel
        ]
    )

    if rng.random() > probability:
        return None

    delay_days = int(
        np.clip(
            rng.gamma(
                shape=1.7,
                scale=6.0
            ),
            0,
            45
        )
    )

    start_date = (
        signup_date
        + pd.Timedelta(
            days=delay_days
        )
    ).normalize()

    if start_date > DATA_END_DATE:
        return None

    plan_id = choose_direct_plan(
        first_channel
    )

    return (
        plan_id,
        start_date,
        False,
        None,
    )


# ============================================================
# GENERATE INDIVIDUAL SUBSCRIPTIONS
# ============================================================

def generate_individual_subscriptions(
    customers,
    trials,
    first_channel_lookup,
    subscription_counter
):
    """Generate historical subscription records."""

    records = []

    converted_trial_to_subscription = {}

    trial_lookup = {
        row.customer_id: row
        for row in trials.itertuples(
            index=False
        )
    }

    for customer in customers.itertuples(
        index=False
    ):

        customer_id = customer.customer_id

        first_channel = (
            first_channel_lookup[
                customer_id
            ]
        )

        trial_row = trial_lookup.get(
            customer_id
        )

        initial = determine_initial_subscription(
            customer,
            first_channel,
            trial_row
        )

        if initial is None:
            continue

        (
            plan_id,
            start_date,
            from_trial,
            source_trial_id,
        ) = initial

        previous_subscription_id = None

        # Maximum number of plan segments for one
        # customer journey.
        for segment_number in range(4):

            if start_date > DATA_END_DATE:
                break

            subscription_id = (
                f"SUB{subscription_counter:07d}"
            )

            subscription_counter += 1

            (
                record,
                next_plan_id
            ) = simulate_individual_segment(
                subscription_id,
                customer_id,
                plan_id,
                start_date,
                first_channel,
                from_trial
            )

            records.append(
                record
            )

            if (
                source_trial_id is not None
                and segment_number == 0
            ):

                converted_trial_to_subscription[
                    source_trial_id
                ] = subscription_id

            previous_subscription_id = (
                subscription_id
            )

            if next_plan_id is None:
                break

            start_date = (
                pd.Timestamp(
                    record[
                        "subscription_end_date"
                    ]
                )
                + pd.Timedelta(days=1)
            )

            plan_id = next_plan_id
            from_trial = False
            source_trial_id = None

        # Reactivation after true churn.
        last_record = records[-1]

        if (
            last_record["customer_id"]
            == customer_id
            and last_record["status"]
            == "ended"
            and last_record["end_reason"]
            in {
                "voluntary_cancel",
                "non_renewal",
            }
            and rng.random() < 0.12
        ):

            reactivation_date = (
                pd.Timestamp(
                    last_record[
                        "subscription_end_date"
                    ]
                )
                + pd.Timedelta(
                    days=int(
                        rng.integers(
                            14,
                            121
                        )
                    )
                )
            )

            if (
                reactivation_date
                <= DATA_END_DATE
            ):

                new_plan_id = (
                    choose_direct_plan(
                        first_channel
                    )
                )

                subscription_id = (
                    f"SUB{subscription_counter:07d}"
                )

                subscription_counter += 1

                (
                    reactivation_record,
                    _
                ) = simulate_individual_segment(
                    subscription_id,
                    customer_id,
                    new_plan_id,
                    reactivation_date,
                    first_channel,
                    False
                )

                records.append(
                    reactivation_record
                )

    return (
        records,
        converted_trial_to_subscription,
        subscription_counter
    )


# ============================================================
# ORGANISATION SEAT LOGIC
# ============================================================

def generate_seat_count(
    organisation_type,
    organisation_size
):
    """
    Generate purchased Corporate ePaper seats.

    Seats correlate with addressable population without
    simply being a fixed percentage.
    """

    coverage_ranges = {
        "Corporate": (0.04, 0.22),
        "University": (0.02, 0.10),
        "NGO": (0.08, 0.30),
        "Government": (0.03, 0.14),
        "Professional Association": (0.06, 0.25),
        "Other": (0.05, 0.22),
    }

    low, high = coverage_ranges[
        organisation_type
    ]

    coverage = float(
        rng.uniform(
            low,
            high
        )
    )

    seats = int(
        round(
            organisation_size
            * coverage
        )
    )

    seats = max(
        10,
        seats
    )

    seats = min(
        seats,
        organisation_size,
        1500
    )

    return seats


# ============================================================
# GENERATE ORGANISATION SUBSCRIPTIONS
# ============================================================

def generate_organisation_subscriptions(
    organisations,
    subscription_counter
):

    records = []

    for organisation in organisations.itertuples(
        index=False
    ):

        probability = (
            ORGANISATION_SUBSCRIPTION_PROBABILITY[
                organisation.organisation_type
            ]
        )

        if rng.random() > probability:
            continue

        start_date = (
            pd.Timestamp(
                organisation.signup_date
            )
            + pd.Timedelta(
                days=int(
                    rng.integers(
                        5,
                        91
                    )
                )
            )
        ).normalize()

        if start_date > DATA_END_DATE:
            continue

        seats = generate_seat_count(
            organisation.organisation_type,
            int(
                organisation.organisation_size
            )
        )

        # Organisations skew monthly initially,
        # but annual contracts remain meaningful.
        plan_id = rng.choice(
            ["PLN017", "PLN018"],
            p=[0.68, 0.32]
        )

        plan = PLAN_CATALOG[
            plan_id
        ]

        frequency = plan[
            "frequency"
        ]

        current_start = start_date

        current_end = period_end_from_start(
            current_start,
            frequency
        )

        outcome = "active"
        end_reason = None
        end_date = pd.NaT

        max_cycles = 36

        for cycle in range(
            max_cycles
        ):

            if current_end >= DATA_END_DATE:
                break

            if frequency == "Monthly":

                continuation = 0.965

                # Mature monthly accounts occasionally
                # migrate onto annual contracts.
                if (
                    cycle >= 2
                    and rng.random() < 0.055
                ):

                    outcome = "ended"
                    end_reason = "plan_change"
                    end_date = current_end
                    break

            else:

                continuation = 0.94

            if rng.random() > continuation:

                outcome = "ended"

                if rng.random() < 0.70:
                    end_reason = (
                        "voluntary_cancel"
                    )
                else:
                    end_reason = (
                        "non_renewal"
                    )

                end_date = current_end
                break

            current_start = next_period_start(
                current_start,
                frequency
            )

            current_end = period_end_from_start(
                current_start,
                frequency
            )

        subscription_id = (
            f"SUB{subscription_counter:07d}"
        )

        subscription_counter += 1

        cancellation_requested_at = pd.NaT

        if end_reason == "voluntary_cancel":

            cancellation_requested_at = (
                pd.Timestamp(end_date)
                - pd.Timedelta(
                    days=int(
                        rng.integers(3, 21)
                    )
                )
                + pd.Timedelta(hours=10)
            )

        records.append({
            "subscription_id":
                subscription_id,

            "customer_id":
                None,

            "organisation_id":
                organisation.organisation_id,

            "plan_id":
                plan_id,

            "subscription_start_date":
                start_date.date(),

            "current_period_start":
                current_start.date(),

            "current_period_end":
                current_end.date(),

            "subscription_end_date":
                (
                    pd.Timestamp(
                        end_date
                    ).date()
                    if pd.notna(
                        end_date
                    )
                    else None
                ),

            "status":
                "ended"
                if outcome == "ended"
                else "active",

            "auto_renew":
                outcome == "active",

            "cancellation_requested_at":
                cancellation_requested_at,

            "end_reason":
                end_reason,

            "seats_purchased":
                seats,

            "created_at":
                start_date
                + pd.Timedelta(
                    hours=int(
                        rng.integers(
                            8,
                            18
                        )
                    )
                ),
        })

        # Monthly → Annual plan migration.
        if (
            end_reason == "plan_change"
            and plan_id == "PLN017"
        ):

            annual_start = (
                pd.Timestamp(end_date)
                + pd.Timedelta(days=1)
            )

            if annual_start <= DATA_END_DATE:

                annual_id = (
                    f"SUB{subscription_counter:07d}"
                )

                subscription_counter += 1

                annual_end = (
                    period_end_from_start(
                        annual_start,
                        "Annual"
                    )
                )

                records.append({
                    "subscription_id":
                        annual_id,

                    "customer_id":
                        None,

                    "organisation_id":
                        organisation.organisation_id,

                    "plan_id":
                        "PLN018",

                    "subscription_start_date":
                        annual_start.date(),

                    "current_period_start":
                        annual_start.date(),

                    "current_period_end":
                        annual_end.date(),

                    "subscription_end_date":
                        None,

                    "status":
                        "active",

                    "auto_renew":
                        True,

                    "cancellation_requested_at":
                        pd.NaT,

                    "end_reason":
                        None,

                    "seats_purchased":
                        seats,

                    "created_at":
                        annual_start
                        + pd.Timedelta(
                            hours=10
                        ),
                })

    return (
        records,
        subscription_counter
    )


# ============================================================
# FINALISE TRIAL TABLE
# ============================================================

def finalise_trials(
    trial_staging,
    converted_trial_lookup
):
    """Create database-ready trial records."""

    records = []

    for trial in trial_staging.itertuples(
        index=False
    ):

        converted_subscription_id = None

        if (
            trial.intended_outcome
            == "converted"
        ):

            converted_subscription_id = (
                converted_trial_lookup.get(
                    trial.trial_id
                )
            )

            if (
                converted_subscription_id
                is None
            ):

                raise ValueError(
                    f"Converted trial "
                    f"{trial.trial_id} "
                    "has no subscription."
                )

        records.append({
            "trial_id":
                trial.trial_id,

            "customer_id":
                trial.customer_id,

            "product_id":
                trial.product_id,

            "trial_started_at":
                trial.trial_started_at,

            "scheduled_end_at":
                trial.scheduled_end_at,

            "actual_end_at":
                trial.actual_end_at,

            "trial_status":
                trial.intended_outcome,

            "converted_subscription_id":
                converted_subscription_id,

            "created_at":
                trial.created_at,
        })

    return pd.DataFrame(
        records
    )


# ============================================================
# VALIDATION
# ============================================================

def validate_subscriptions(
    subscriptions
):

    if not subscriptions[
        "subscription_id"
    ].is_unique:

        raise ValueError(
            "Duplicate subscription IDs detected."
        )

    owner_count = (
        subscriptions[
            ["customer_id", "organisation_id"]
        ]
        .notna()
        .sum(axis=1)
    )

    if not (
        owner_count == 1
    ).all():

        raise ValueError(
            "Every subscription must have "
            "exactly one owner."
        )

    organisation_rows = (
        subscriptions[
            "organisation_id"
        ].notna()
    )

    if (
        subscriptions.loc[
            organisation_rows,
            "seats_purchased"
        ]
        .lt(10)
        .any()
    ):

        raise ValueError(
            "Organisation subscription "
            "below 10-seat minimum."
        )

    individual_rows = (
        subscriptions[
            "customer_id"
        ].notna()
    )

    if (
        subscriptions.loc[
            individual_rows,
            "seats_purchased"
        ]
        .notna()
        .any()
    ):

        raise ValueError(
            "Individual subscription "
            "contains seats."
        )

    ended = (
        subscriptions[
            "status"
        ] == "ended"
    )

    if (
        subscriptions.loc[
            ended,
            "subscription_end_date"
        ]
        .isna()
        .any()
    ):

        raise ValueError(
            "Ended subscription missing end date."
        )

    if (
        subscriptions.loc[
            ended,
            "end_reason"
        ]
        .isna()
        .any()
    ):

        raise ValueError(
            "Ended subscription missing end reason."
        )


def validate_trials(
    trials
):

    converted = (
        trials[
            "trial_status"
        ] == "converted"
    )

    if (
        trials.loc[
            converted,
            "converted_subscription_id"
        ]
        .isna()
        .any()
    ):

        raise ValueError(
            "Converted trial missing subscription."
        )

    not_converted = ~converted

    if (
        trials.loc[
            not_converted,
            "converted_subscription_id"
        ]
        .notna()
        .any()
    ):

        raise ValueError(
            "Non-converted trial references "
            "a subscription."
        )

def reconcile_account_statuses(
    customers,
    organisations,
    subscriptions
):
    """
    Reconcile current account status with subscription status.

    A closed account cannot hold an active subscription.
    Suspended accounts may retain an active subscription because
    suspension is treated as an account-level restriction rather
    than a subscription lifecycle state.
    """

    customers = customers.copy()
    organisations = organisations.copy()

    active_customer_ids = set(
        subscriptions.loc[
            (
                subscriptions["status"] == "active"
            )
            & subscriptions["customer_id"].notna(),
            "customer_id"
        ]
    )

    active_organisation_ids = set(
        subscriptions.loc[
            (
                subscriptions["status"] == "active"
            )
            & subscriptions["organisation_id"].notna(),
            "organisation_id"
        ]
    )

    customer_conflict = (
        customers["customer_id"].isin(
            active_customer_ids
        )
        & customers["account_status"].eq("closed")
    )

    organisation_conflict = (
        organisations["organisation_id"].isin(
            active_organisation_ids
        )
        & organisations["account_status"].eq("closed")
    )

    customers.loc[
        customer_conflict,
        "account_status"
    ] = "active"

    organisations.loc[
        organisation_conflict,
        "account_status"
    ] = "active"

    return (
        customers,
        organisations,
        int(customer_conflict.sum()),
        int(organisation_conflict.sum())
    )
# ============================================================
# SAVE
# ============================================================

def save_data(
    subscriptions,
    trials,
    customers,
    organisations
):
    """
    Save subscription outputs and persist reconciled
    account statuses back to the base entity files.
    """

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    subscriptions_path = (
        OUTPUT_DIR
        / "subscriptions.csv"
    )

    trials_path = (
        OUTPUT_DIR
        / "trials.csv"
    )

    customers_path = (
        OUTPUT_DIR
        / "customers.csv"
    )

    organisations_path = (
        OUTPUT_DIR
        / "organisations.csv"
    )

    subscriptions.to_csv(
        subscriptions_path,
        index=False
    )

    trials.to_csv(
        trials_path,
        index=False
    )

    customers.to_csv(
        customers_path,
        index=False
    )

    organisations.to_csv(
        organisations_path,
        index=False
    )

    return (
        subscriptions_path,
        trials_path,
        customers_path,
        organisations_path
    )

# ============================================================
# SUMMARY
# ============================================================

def print_summary(
    subscriptions,
    trials
):

    individual = subscriptions[
        subscriptions[
            "customer_id"
        ].notna()
    ]

    organisations = subscriptions[
        subscriptions[
            "organisation_id"
        ].notna()
    ]

    print("\n" + "=" * 65)
    print(
        "DAILYPULSE MEDIA — SUBSCRIPTION DATA GENERATION COMPLETE"
    )
    print("=" * 65)

    print(
        f"\nTotal subscription records: "
        f"{len(subscriptions):,}"
    )

    print(
        f"Individual subscription records: "
        f"{len(individual):,}"
    )

    print(
        f"Organisation subscription records: "
        f"{len(organisations):,}"
    )

    print(
        f"\nUnique individual subscribers: "
        f"{individual['customer_id'].nunique():,}"
    )

    print(
        f"Unique subscribing organisations: "
        f"{organisations['organisation_id'].nunique():,}"
    )

    print("\nSubscription status:")

    print(
        subscriptions[
            "status"
        ].value_counts()
    )

    print("\nEnd reasons:")

    print(
        subscriptions[
            "end_reason"
        ]
        .dropna()
        .value_counts()
    )

    print("\nConsumer plan mix:")

    print(
        individual[
            "plan_id"
        ].value_counts()
    )

    print("\nTrial linkage:")

    print(
        trials[
            "trial_status"
        ].value_counts()
    )

    print(
        "\nConverted trials linked to subscriptions: "
        f"{trials['converted_subscription_id'].notna().sum():,}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    (
        customers,
        organisations,
        touchpoints,
        trial_staging
    ) = read_inputs()

    first_channel_lookup = (
        build_first_channel_lookup(
            touchpoints
        )
    )

    subscription_counter = 1

    (
        individual_records,
        converted_trial_lookup,
        subscription_counter
    ) = generate_individual_subscriptions(
        customers,
        trial_staging,
        first_channel_lookup,
        subscription_counter
    )

    (
        organisation_records,
        subscription_counter
    ) = generate_organisation_subscriptions(
        organisations,
        subscription_counter
    )

    subscriptions = pd.DataFrame(
        individual_records
        + organisation_records
    )

    trials = finalise_trials(
        trial_staging,
        converted_trial_lookup
    )
    (
        customers,
        organisations,
        customer_status_fixes,
        organisation_status_fixes
    ) = reconcile_account_statuses(
        customers,
        organisations,
        subscriptions
    )

    print(
        "\nAccount-status reconciliation:"
    )

    print(
        f"- customer conflicts corrected: "
        f"{customer_status_fixes}"
    )

    print(
        f"- organisation conflicts corrected: "
        f"{organisation_status_fixes}"
    )
    validate_subscriptions(
        subscriptions
    )

    validate_trials(
        trials
    )

    (
        subscriptions_path,
        trials_path,
        customers_path,
        organisations_path
    ) = save_data(
        subscriptions,
        trials,
        customers,
        organisations
    )

    print_summary(
        subscriptions,
        trials
    )

    print("\nFiles created:")
    print(
        f"- {subscriptions_path}"
    )
    print(
        f"- {trials_path}"
    )
    print(
        f"- {customers_path}"
    )

    print(
        f"- {organisations_path}"
    )

if __name__ == "__main__":
    main()