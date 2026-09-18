"""
DAILYPULSE MEDIA
Subscription Intelligence

File: generate_commercial_data.py

Purpose:
    Generate the financial and event history behind
    the approved subscription lifecycle.

Generates:
    1. payments.csv
    2. subscription_events.csv

Important:
    - One payment row represents one payment attempt.
    - Failed retries therefore create additional payment rows.
    - Existing subscription records are NOT modified.
"""

from pathlib import Path
import random

import numpy as np
import pandas as pd

from generate_subscription_data import (
    PLAN_CATALOG,
    next_period_start,
    period_end_from_start,
)


# ============================================================
# CONFIGURATION
# ============================================================

RANDOM_SEED = 42

SUBSCRIPTIONS_PATH = Path(
    "data/raw/subscriptions.csv"
)

TRIALS_PATH = Path(
    "data/raw/trials.csv"
)

CUSTOMERS_PATH = Path(
    "data/raw/customers.csv"
)

ORGANISATIONS_PATH = Path(
    "data/raw/organisations.csv"
)

OUTPUT_DIR = Path(
    "data/raw"
)

DATA_END_AT = pd.Timestamp(
    "2026-08-20 23:59:59"
)

random.seed(
    RANDOM_SEED
)

np.random.seed(
    RANDOM_SEED
)

rng = np.random.default_rng(
    RANDOM_SEED
)


# ============================================================
# PAYMENT ASSUMPTIONS
# ============================================================

PAYMENT_METHOD_WEIGHTS = {

    "Kenya": {
        "mobile_money": 0.75,
        "card": 0.22,
        "bank_transfer": 0.03,
    },

    "East Africa": {
        "mobile_money": 0.58,
        "card": 0.35,
        "bank_transfer": 0.07,
    },

    "International": {
        "mobile_money": 0.05,
        "card": 0.70,
        "bank_transfer": 0.25,
    },

    "Organisation": {
        "mobile_money": 0.05,
        "card": 0.15,
        "bank_transfer": 0.80,
    },
}


FIRST_ATTEMPT_FAILURE_RATE = {
    "mobile_money": 0.035,
    "card": 0.055,
    "bank_transfer": 0.018,
}


FAILURE_REASONS = {

    "mobile_money": [
        "insufficient_funds",
        "network_error",
        "customer_timeout",
    ],

    "card": [
        "card_declined",
        "insufficient_funds",
        "expired_card",
        "bank_rejection",
    ],

    "bank_transfer": [
        "bank_rejection",
        "processing_error",
        "insufficient_funds",
    ],
}


EAST_AFRICAN_COUNTRIES = {
    "Kenya",
    "Uganda",
    "Tanzania",
    "Rwanda",
}


# ============================================================
# ALLOWED EVENT TYPES
# ============================================================

ALLOWED_EVENT_TYPES = {
    "subscription_started",
    "renewed",
    "cancellation_requested",
    "cancellation_reversed",
    "plan_changed",
    "past_due_started",
    "past_due_resolved",
    "subscription_ended",
    "reactivated",
    "seats_changed",
}


# ============================================================
# HELPERS
# ============================================================

def weighted_choice(
    weight_map
):
    """Choose one item using predefined probabilities."""

    values = list(
        weight_map.keys()
    )

    probabilities = list(
        weight_map.values()
    )

    return rng.choice(
        values,
        p=probabilities
    )


def clean_optional_id(
    value
):
    """Convert pandas NaN IDs into None."""

    if pd.isna(
        value
    ):
        return None

    return str(
        value
    )


# ============================================================
# READ INPUTS
# ============================================================

def read_inputs():

    subscriptions = pd.read_csv(
        SUBSCRIPTIONS_PATH
    )

    trials = pd.read_csv(
        TRIALS_PATH
    )

    customers = pd.read_csv(
        CUSTOMERS_PATH
    )

    organisations = pd.read_csv(
        ORGANISATIONS_PATH
    )

    date_columns = [
        "subscription_start_date",
        "current_period_start",
        "current_period_end",
        "subscription_end_date",
        "cancellation_requested_at",
        "created_at",
    ]

    for column in date_columns:

        subscriptions[column] = pd.to_datetime(
            subscriptions[column],
            errors="coerce"
        )

    trials[
        "trial_started_at"
    ] = pd.to_datetime(
        trials[
            "trial_started_at"
        ],
        errors="coerce"
    )

    return (
        subscriptions,
        trials,
        customers,
        organisations
    )


# ============================================================
# OWNER KEYS
# ============================================================

def add_owner_keys(
    subscriptions
):

    subscriptions = subscriptions.copy()

    subscriptions[
        "owner_key"
    ] = subscriptions.apply(
        lambda row:
            (
                "C:"
                + str(
                    row["customer_id"]
                )
            )
            if pd.notna(
                row["customer_id"]
            )
            else
            (
                "O:"
                + str(
                    row["organisation_id"]
                )
            ),
        axis=1
    )

    return subscriptions


# ============================================================
# BUILD SUBSCRIPTION RELATIONSHIPS
# ============================================================

def build_subscription_relationships(
    subscriptions,
    trials
):
    """
    Identify:
        - plan-change chains
        - reactivations
        - subscription start reasons
    """

    plan_change_target = {}

    reactivation_origin = {}

    start_reason = {}

    converted_trial_subscriptions = set(
        trials.loc[
            (
                trials["trial_status"]
                == "converted"
            ),
            "converted_subscription_id"
        ]
        .dropna()
        .astype(str)
    )

    for (
        owner_key,
        group
    ) in subscriptions.groupby(
        "owner_key"
    ):

        group = group.sort_values(
            "subscription_start_date"
        )

        rows = list(
            group.itertuples(
                index=False
            )
        )

        for index, current in enumerate(
            rows
        ):

            current_id = str(
                current.subscription_id
            )

            if (
                current_id
                in converted_trial_subscriptions
            ):

                start_reason[
                    current_id
                ] = "trial_conversion"

            elif index == 0:

                start_reason[
                    current_id
                ] = "new_subscription"

            if index == 0:
                continue

            previous = rows[
                index - 1
            ]

            previous_id = str(
                previous.subscription_id
            )

            current_start = pd.Timestamp(
                current.subscription_start_date
            )

            previous_end = pd.Timestamp(
                previous.subscription_end_date
            )

            if (
                previous.end_reason
                == "plan_change"
                and pd.notna(
                    previous_end
                )
                and current_start.normalize()
                == (
                    previous_end
                    + pd.Timedelta(days=1)
                ).normalize()
            ):

                plan_change_target[
                    previous_id
                ] = current_id

                start_reason[
                    current_id
                ] = "plan_change"

            elif (
                previous.status
                == "ended"
                and previous.end_reason
                in {
                    "voluntary_cancel",
                    "non_renewal",
                    "payment_failure",
                }
                and pd.notna(
                    previous_end
                )
                and current_start
                > previous_end
            ):

                reactivation_origin[
                    current_id
                ] = previous_id

                start_reason[
                    current_id
                ] = "reactivation"

            elif (
                current_id
                not in start_reason
            ):

                start_reason[
                    current_id
                ] = "new_subscription"

    # Every plan_change should point to a successor.
    expected_plan_changes = set(
        subscriptions.loc[
            subscriptions[
                "end_reason"
            ].eq(
                "plan_change"
            ),
            "subscription_id"
        ].astype(str)
    )

    missing_plan_changes = (
        expected_plan_changes
        - set(
            plan_change_target.keys()
        )
    )

    if missing_plan_changes:

        raise ValueError(
            "Plan-change subscription(s) "
            "have no successor: "
            + ", ".join(
                sorted(
                    missing_plan_changes
                )[:10]
            )
        )

    return {
        "plan_change_target":
            plan_change_target,

        "reactivation_origin":
            reactivation_origin,

        "start_reason":
            start_reason,
    }


# ============================================================
# PAYMENT METHOD
# ============================================================

def determine_owner_payment_method(
    subscription,
    customer_country_lookup
):
    """Assign a stable payment method to an owner."""

    if pd.notna(
        subscription.organisation_id
    ):

        segment = "Organisation"

    else:

        country = customer_country_lookup.get(
            str(
                subscription.customer_id
            ),
            "International"
        )

        if country == "Kenya":

            segment = "Kenya"

        elif country in EAST_AFRICAN_COUNTRIES:

            segment = "East Africa"

        else:

            segment = "International"

    return weighted_choice(
        PAYMENT_METHOD_WEIGHTS[
            segment
        ]
    )


# ============================================================
# PERIOD BUILDING
# ============================================================

def build_subscription_periods(
    subscription
):
    """
    Reconstruct every billing period represented by
    the subscription record.
    """

    plan = PLAN_CATALOG[
        subscription.plan_id
    ]

    frequency = plan[
        "frequency"
    ]

    current_start = pd.Timestamp(
        subscription.subscription_start_date
    ).normalize()

    final_period_start = pd.Timestamp(
        subscription.current_period_start
    ).normalize()

    periods = []

    max_cycles = 600

    for _ in range(
        max_cycles
    ):

        if (
            current_start
            > final_period_start
        ):
            break

        current_end = (
            period_end_from_start(
                current_start,
                frequency
            )
        )

        periods.append(
            (
                current_start,
                current_end
            )
        )

        if (
            current_start
            == final_period_start
        ):
            break

        current_start = (
            next_period_start(
                current_start,
                frequency
            )
        )

    if (
        not periods
        or periods[-1][0]
        != final_period_start
    ):

        raise ValueError(
            f"Could not reconstruct billing "
            f"periods for "
            f"{subscription.subscription_id}."
        )

    return periods

# HELPER
# discounting orgs depending on the seat purchased volume
def calculate_progressive_seat_value(
    seats,
    base_price
):
    """
    Calculate institutional contract value using
    progressive seat pricing.

    Each additional seat band receives a deeper
    effective discount.
    """

    tiers = [
        (49, 1.00),
        (50, 0.60),
        (150, 0.40),
        (250, 0.25),
        (500, 0.15),
        (None, 0.10),
    ]

    remaining_seats = int(seats)
    total = 0.0

    for tier_size, price_factor in tiers:

        if remaining_seats <= 0:
            break

        if tier_size is None:
            seats_in_tier = remaining_seats
        else:
            seats_in_tier = min(
                remaining_seats,
                tier_size
            )

        total += (
            seats_in_tier
            * base_price
            * price_factor
        )

        remaining_seats -= seats_in_tier

    return round(total, 2)
# ============================================================
# PAYMENT AMOUNT
# ============================================================

def calculate_payment_amount(
    subscription
):
    """
    Calculate one billing-period payment.

    Individuals pay standard plan price.

    Institutional subscriptions use progressive
    volume pricing.
    """

    plan = PLAN_CATALOG[
        subscription.plan_id
    ]

    base_price = float(
        plan["price"]
    )

    if pd.isna(
        subscription.organisation_id
    ):
        return round(
            base_price,
            2
        )

    seats = int(
        subscription.seats_purchased
    )

    return calculate_progressive_seat_value(
        seats,
        base_price
    )

# ============================================================
# PAYMENT TIMESTAMPS
# ============================================================

def initial_attempt_at(
    period_start,
    payment_method
):

    if (
        payment_method
        == "bank_transfer"
    ):

        hour = int(
            rng.integers(
                9,
                17
            )
        )

    else:

        hour = int(
            rng.integers(
                6,
                22
            )
        )

    minute = int(
        rng.integers(
            0,
            60
        )
    )

    return (
        pd.Timestamp(
            period_start
        )
        + pd.Timedelta(
            hours=hour,
            minutes=minute
        )
    )


def retry_delay(
    frequency
):
    """Generate a realistic retry delay."""

    if frequency == "Daily":

        return pd.Timedelta(
            hours=int(
                rng.integers(
                    2,
                    8
                )
            )
        )

    return pd.Timedelta(
        hours=int(
            rng.integers(
                8,
                25
            )
        )
    )


# ============================================================
# GENERATE PAYMENTS
# ============================================================

def generate_payments(
    subscriptions,
    customers
):
    """
    Generate one row per payment attempt.

    Existing subscription records imply that each represented
    billing period was ultimately paid, so temporary failures
    may retry but must resolve successfully.
    """

    payment_records = []

    period_payment_lookup = {}

    payment_counter = 1

    customer_country_lookup = (
        customers
        .set_index(
            "customer_id"
        )[
            "country"
        ]
        .to_dict()
    )

    owner_method_lookup = {}

    subscriptions_sorted = (
        subscriptions
        .sort_values(
            [
                "owner_key",
                "subscription_start_date",
            ]
        )
    )

    for subscription in (
        subscriptions_sorted
        .itertuples(
            index=False
        )
    ):

        owner_key = (
            subscription.owner_key
        )

        if (
            owner_key
            not in owner_method_lookup
        ):

            owner_method_lookup[
                owner_key
            ] = determine_owner_payment_method(
                subscription,
                customer_country_lookup
            )

        payment_method = (
            owner_method_lookup[
                owner_key
            ]
        )

        plan = PLAN_CATALOG[
            subscription.plan_id
        ]

        frequency = plan[
            "frequency"
        ]

        amount = calculate_payment_amount(
            subscription
        )

        periods = build_subscription_periods(
            subscription
        )

        for (
            period_index,
            (
                period_start,
                period_end
            )
        ) in enumerate(
            periods
        ):

            first_attempt_at = (
                initial_attempt_at(
                    period_start,
                    payment_method
                )
            )

            failed_attempts = []

            # Initial subscription payments must succeed.
            # Temporary payment friction begins on renewals.
            allow_failure = (
                period_index > 0
                and first_attempt_at
                + pd.Timedelta(days=2)
                <= DATA_END_AT
            )

            should_fail = (
                allow_failure
                and rng.random()
                < FIRST_ATTEMPT_FAILURE_RATE[
                    payment_method
                ]
            )

            if should_fail:

                number_of_failures = (
                    2
                    if rng.random() < 0.12
                    else 1
                )

                attempt_at = (
                    first_attempt_at
                )

                for _ in range(
                    number_of_failures
                ):

                    payment_id = (
                        f"PAY{payment_counter:08d}"
                    )

                    payment_counter += 1

                    failure_reason = rng.choice(
                        FAILURE_REASONS[
                            payment_method
                        ]
                    )

                    payment_records.append({
                        "payment_id":
                            payment_id,

                        "subscription_id":
                            subscription.subscription_id,

                        "payment_attempted_at":
                            attempt_at,

                        "amount":
                            amount,

                        "currency":
                            "KES",

                        "payment_status":
                            "failed",

                        "payment_method":
                            payment_method,

                        "transaction_reference":
                            None,

                        "failure_reason":
                            failure_reason,

                        "created_at":
                            attempt_at
                            + pd.Timedelta(
                                seconds=int(
                                    rng.integers(
                                        5,
                                        90
                                    )
                                )
                            ),
                    })

                    failed_attempts.append({
                        "payment_id":
                            payment_id,

                        "attempted_at":
                            attempt_at,

                        "failure_reason":
                            failure_reason,
                    })

                    attempt_at = (
                        attempt_at
                        + retry_delay(
                            frequency
                        )
                    )

                successful_attempt_at = (
                    attempt_at
                )

            else:

                successful_attempt_at = (
                    first_attempt_at
                )

            # Every represented billing period eventually succeeds.
            payment_id = (
                f"PAY{payment_counter:08d}"
            )

            payment_counter += 1

            transaction_reference = (
                f"DPTXN{payment_counter:09d}"
            )

            payment_records.append({
                "payment_id":
                    payment_id,

                "subscription_id":
                    subscription.subscription_id,

                "payment_attempted_at":
                    successful_attempt_at,

                "amount":
                    amount,

                "currency":
                    "KES",

                "payment_status":
                    "successful",

                "payment_method":
                    payment_method,

                "transaction_reference":
                    transaction_reference,

                "failure_reason":
                    None,

                "created_at":
                    successful_attempt_at
                    + pd.Timedelta(
                        seconds=int(
                            rng.integers(
                                5,
                                90
                            )
                        )
                    ),
            })

            period_key = (
                str(
                    subscription.subscription_id
                ),
                period_start.date(),
            )

            period_payment_lookup[
                period_key
            ] = {
                "period_start":
                    period_start,

                "period_end":
                    period_end,

                "successful_payment_id":
                    payment_id,

                "successful_at":
                    successful_attempt_at,

                "failed_attempts":
                    failed_attempts,
            }

    return (
        pd.DataFrame(
            payment_records
        ),
        period_payment_lookup,
    )


# ============================================================
# EVENT RECORD HELPER
# ============================================================

def build_event_record(
    event_id,
    subscription_id,
    event_type,
    event_at,
    related_subscription_id=None,
    triggering_payment_id=None,
    period_start=None,
    period_end=None,
    previous_seat_count=None,
    new_seat_count=None,
    event_reason=None,
):

    event_at = pd.Timestamp(
        event_at
    )

    return {
        "event_id":
            event_id,

        "subscription_id":
            subscription_id,

        "event_type":
            event_type,

        "event_at":
            event_at,

        "related_subscription_id":
            related_subscription_id,

        "triggering_payment_id":
            triggering_payment_id,

        "period_start":
            (
                pd.Timestamp(
                    period_start
                ).date()
                if period_start is not None
                else None
            ),

        "period_end":
            (
                pd.Timestamp(
                    period_end
                ).date()
                if period_end is not None
                else None
            ),

        "previous_seat_count":
            previous_seat_count,

        "new_seat_count":
            new_seat_count,

        "event_reason":
            event_reason,

        "created_at":
            event_at
            + pd.Timedelta(
                seconds=5
            ),
    }


# ============================================================
# GENERATE SUBSCRIPTION EVENTS
# ============================================================

def generate_subscription_events(
    subscriptions,
    period_payment_lookup,
    relationships
):

    records = []

    event_counter = 1

    plan_change_target = (
        relationships[
            "plan_change_target"
        ]
    )

    reactivation_origin = (
        relationships[
            "reactivation_origin"
        ]
    )

    start_reason = (
        relationships[
            "start_reason"
        ]
    )

    subscriptions_lookup = {
        str(
            row.subscription_id
        ): row
        for row in subscriptions.itertuples(
            index=False
        )
    }

    for subscription in (
        subscriptions
        .sort_values(
            "subscription_start_date"
        )
        .itertuples(
            index=False
        )
    ):

        subscription_id = str(
            subscription.subscription_id
        )

        periods = build_subscription_periods(
            subscription
        )

        # ----------------------------------------------------
        # START + RENEWAL EVENTS
        # ----------------------------------------------------

        for (
            period_index,
            (
                period_start,
                period_end
            )
        ) in enumerate(
            periods
        ):

            period_key = (
                subscription_id,
                period_start.date(),
            )

            payment_info = (
                period_payment_lookup[
                    period_key
                ]
            )

            success_payment_id = (
                payment_info[
                    "successful_payment_id"
                ]
            )

            success_at = (
                payment_info[
                    "successful_at"
                ]
            )

            failed_attempts = (
                payment_info[
                    "failed_attempts"
                ]
            )

            if period_index == 0:

                event_id = (
                    f"EVT{event_counter:08d}"
                )

                event_counter += 1

                records.append(
                    build_event_record(
                        event_id=
                            event_id,

                        subscription_id=
                            subscription_id,

                        event_type=
                            "subscription_started",

                        event_at=
                            success_at,

                        triggering_payment_id=
                            success_payment_id,

                        period_start=
                            period_start,

                        period_end=
                            period_end,

                        event_reason=
                            start_reason.get(
                                subscription_id,
                                "new_subscription"
                            ),
                    )
                )

                if (
                    subscription_id
                    in reactivation_origin
                ):

                    event_id = (
                        f"EVT{event_counter:08d}"
                    )

                    event_counter += 1

                    records.append(
                        build_event_record(
                            event_id=
                                event_id,

                            subscription_id=
                                subscription_id,

                            event_type=
                                "reactivated",

                            event_at=
                                success_at
                                + pd.Timedelta(
                                    seconds=1
                                ),

                            related_subscription_id=
                                reactivation_origin[
                                    subscription_id
                                ],

                            triggering_payment_id=
                                success_payment_id,

                            period_start=
                                period_start,

                            period_end=
                                period_end,

                            event_reason=
                                "returning_subscriber",
                        )
                    )

            else:

                if failed_attempts:

                    first_failure = (
                        failed_attempts[
                            0
                        ]
                    )

                    event_id = (
                        f"EVT{event_counter:08d}"
                    )

                    event_counter += 1

                    records.append(
                        build_event_record(
                            event_id=
                                event_id,

                            subscription_id=
                                subscription_id,

                            event_type=
                                "past_due_started",

                            event_at=
                                first_failure[
                                    "attempted_at"
                                ],

                            triggering_payment_id=
                                first_failure[
                                    "payment_id"
                                ],

                            period_start=
                                period_start,

                            period_end=
                                period_end,

                            event_reason=
                                first_failure[
                                    "failure_reason"
                                ],
                        )
                    )

                    event_id = (
                        f"EVT{event_counter:08d}"
                    )

                    event_counter += 1

                    records.append(
                        build_event_record(
                            event_id=
                                event_id,

                            subscription_id=
                                subscription_id,

                            event_type=
                                "past_due_resolved",

                            event_at=
                                success_at,

                            triggering_payment_id=
                                success_payment_id,

                            period_start=
                                period_start,

                            period_end=
                                period_end,

                            event_reason=
                                "payment_retry_successful",
                        )
                    )

                event_id = (
                    f"EVT{event_counter:08d}"
                )

                event_counter += 1

                records.append(
                    build_event_record(
                        event_id=
                            event_id,

                        subscription_id=
                            subscription_id,

                        event_type=
                            "renewed",

                        event_at=
                            success_at,

                        triggering_payment_id=
                            success_payment_id,

                        period_start=
                            period_start,

                        period_end=
                            period_end,

                        event_reason=
                            "scheduled_renewal",
                    )
                )

        # ----------------------------------------------------
        # CANCELLATION REQUEST
        # ----------------------------------------------------

        if pd.notna(
            subscription.cancellation_requested_at
        ):

            event_id = (
                f"EVT{event_counter:08d}"
            )

            event_counter += 1

            records.append(
                build_event_record(
                    event_id=
                        event_id,

                    subscription_id=
                        subscription_id,

                    event_type=
                        "cancellation_requested",

                    event_at=
                        subscription.cancellation_requested_at,

                    event_reason=
                        "customer_requested",
                )
            )

        # ----------------------------------------------------
        # SUBSCRIPTION END
        # ----------------------------------------------------

        if (
            subscription.status
            == "ended"
        ):

            end_at = (
                pd.Timestamp(
                    subscription.subscription_end_date
                )
                + pd.Timedelta(
                    hours=23,
                    minutes=59
                )
            )

            event_id = (
                f"EVT{event_counter:08d}"
            )

            event_counter += 1

            records.append(
                build_event_record(
                    event_id=
                        event_id,

                    subscription_id=
                        subscription_id,

                    event_type=
                        "subscription_ended",

                    event_at=
                        end_at,

                    event_reason=
                        subscription.end_reason,
                )
            )

        # ----------------------------------------------------
        # PLAN CHANGE
        # ----------------------------------------------------

        if (
            subscription_id
            in plan_change_target
        ):

            target_id = (
                plan_change_target[
                    subscription_id
                ]
            )

            target_subscription = (
                subscriptions_lookup[
                    target_id
                ]
            )

            plan_change_at = (
                pd.Timestamp(
                    target_subscription
                    .subscription_start_date
                )
                + pd.Timedelta(
                    minutes=1
                )
            )

            event_id = (
                f"EVT{event_counter:08d}"
            )

            event_counter += 1

            records.append(
                build_event_record(
                    event_id=
                        event_id,

                    subscription_id=
                        subscription_id,

                    event_type=
                        "plan_changed",

                    event_at=
                        plan_change_at,

                    related_subscription_id=
                        target_id,

                    event_reason=
                        "plan_migration",
                )
            )

    return pd.DataFrame(
        records
    )


# ============================================================
# VALIDATE PAYMENTS
# ============================================================

def validate_payments(
    payments,
    subscriptions
):

    if not payments[
        "payment_id"
    ].is_unique:

        raise ValueError(
            "Duplicate payment IDs detected."
        )

    allowed_statuses = {
        "successful",
        "failed",
        "pending",
    }

    if not set(
        payments[
            "payment_status"
        ]
    ).issubset(
        allowed_statuses
    ):

        raise ValueError(
            "Invalid payment status detected."
        )

    allowed_methods = {
        "mobile_money",
        "card",
        "bank_transfer",
    }

    if not set(
        payments[
            "payment_method"
        ]
    ).issubset(
        allowed_methods
    ):

        raise ValueError(
            "Invalid payment method detected."
        )

    valid_subscription_ids = set(
        subscriptions[
            "subscription_id"
        ].astype(str)
    )

    if not set(
        payments[
            "subscription_id"
        ].astype(str)
    ).issubset(
        valid_subscription_ids
    ):

        raise ValueError(
            "Payment references unknown subscription."
        )

    if (
        payments[
            "amount"
        ]
        .le(0)
        .any()
    ):

        raise ValueError(
            "Non-positive payment amount detected."
        )

    successful = payments[
        payments[
            "payment_status"
        ]
        == "successful"
    ]

    if successful[
        "transaction_reference"
    ].isna().any():

        raise ValueError(
            "Successful payment missing transaction reference."
        )

    if not successful[
        "transaction_reference"
    ].is_unique:

        raise ValueError(
            "Duplicate transaction references detected."
        )

    payment_counts = (
        payments
        .groupby(
            "subscription_id"
        )
        .size()
    )

    if len(
        payment_counts
    ) != len(
        subscriptions
    ):

        raise ValueError(
            "Every subscription must have "
            "at least one payment attempt."
        )


# ============================================================
# VALIDATE EVENTS
# ============================================================

def validate_events(
    events,
    payments,
    subscriptions,
    relationships
):

    if not events[
        "event_id"
    ].is_unique:

        raise ValueError(
            "Duplicate event IDs detected."
        )

    if not set(
        events[
            "event_type"
        ]
    ).issubset(
        ALLOWED_EVENT_TYPES
    ):

        raise ValueError(
            "Invalid subscription event detected."
        )

    valid_subscription_ids = set(
        subscriptions[
            "subscription_id"
        ].astype(str)
    )

    if not set(
        events[
            "subscription_id"
        ].astype(str)
    ).issubset(
        valid_subscription_ids
    ):

        raise ValueError(
            "Event references unknown subscription."
        )

    triggering_ids = set(
        events[
            "triggering_payment_id"
        ]
        .dropna()
        .astype(str)
    )

    valid_payment_ids = set(
        payments[
            "payment_id"
        ].astype(str)
    )

    if not triggering_ids.issubset(
        valid_payment_ids
    ):

        raise ValueError(
            "Event references unknown payment."
        )

    related_ids = set(
        events[
            "related_subscription_id"
        ]
        .dropna()
        .astype(str)
    )

    if not related_ids.issubset(
        valid_subscription_ids
    ):

        raise ValueError(
            "Event references unknown related subscription."
        )

    started_count = (
        events[
            "event_type"
        ]
        .eq(
            "subscription_started"
        )
        .sum()
    )

    if started_count != len(
        subscriptions
    ):

        raise ValueError(
            "Every subscription must have "
            "one subscription_started event."
        )

    expected_ended = (
        subscriptions[
            "status"
        ]
        .eq(
            "ended"
        )
        .sum()
    )

    actual_ended = (
        events[
            "event_type"
        ]
        .eq(
            "subscription_ended"
        )
        .sum()
    )

    if (
        expected_ended
        != actual_ended
    ):

        raise ValueError(
            "Subscription-ended event count mismatch."
        )

    expected_plan_changes = len(
        relationships[
            "plan_change_target"
        ]
    )

    actual_plan_changes = (
        events[
            "event_type"
        ]
        .eq(
            "plan_changed"
        )
        .sum()
    )

    if (
        expected_plan_changes
        != actual_plan_changes
    ):

        raise ValueError(
            "Plan-change event count mismatch."
        )

    expected_reactivations = len(
        relationships[
            "reactivation_origin"
        ]
    )

    actual_reactivations = (
        events[
            "event_type"
        ]
        .eq(
            "reactivated"
        )
        .sum()
    )

    if (
        expected_reactivations
        != actual_reactivations
    ):

        raise ValueError(
            "Reactivation event count mismatch."
        )

    past_due_started = (
        events[
            "event_type"
        ]
        .eq(
            "past_due_started"
        )
        .sum()
    )

    past_due_resolved = (
        events[
            "event_type"
        ]
        .eq(
            "past_due_resolved"
        )
        .sum()
    )

    if (
        past_due_started
        != past_due_resolved
    ):

        raise ValueError(
            "Unresolved generated past-due event detected."
        )


# ============================================================
# SAVE
# ============================================================

def save_data(
    payments,
    events
):

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    payments_path = (
        OUTPUT_DIR
        / "payments.csv"
    )

    events_path = (
        OUTPUT_DIR
        / "subscription_events.csv"
    )

    payments.to_csv(
        payments_path,
        index=False
    )

    events.to_csv(
        events_path,
        index=False
    )

    return (
        payments_path,
        events_path
    )


# ============================================================
# SUMMARY
# ============================================================

def print_summary(
    payments,
    events,
    subscriptions
):

    successful = payments[
        payments[
            "payment_status"
        ]
        == "successful"
    ]

    failed = payments[
        payments[
            "payment_status"
        ]
        == "failed"
    ]

    individual_subscription_ids = set(
        subscriptions.loc[
            subscriptions[
                "customer_id"
            ].notna(),
            "subscription_id"
        ]
    )

    organisation_subscription_ids = set(
        subscriptions.loc[
            subscriptions[
                "organisation_id"
            ].notna(),
            "subscription_id"
        ]
    )

    individual_revenue = (
        successful.loc[
            successful[
                "subscription_id"
            ].isin(
                individual_subscription_ids
            ),
            "amount"
        ]
        .sum()
    )

    organisation_revenue = (
        successful.loc[
            successful[
                "subscription_id"
            ].isin(
                organisation_subscription_ids
            ),
            "amount"
        ]
        .sum()
    )

    total_attempts = len(
        payments
    )

    failure_rate = (
        len(
            failed
        )
        / total_attempts
        * 100
        if total_attempts
        else 0
    )

    print(
        "\n"
        + "=" * 65
    )

    print(
        "DAILYPULSE MEDIA — COMMERCIAL DATA GENERATION COMPLETE"
    )

    print(
        "=" * 65
    )

    print(
        f"\nPayment attempts generated: "
        f"{len(payments):,}"
    )

    print(
        f"Successful payments: "
        f"{len(successful):,}"
    )

    print(
        f"Failed payment attempts: "
        f"{len(failed):,}"
    )

    print(
        f"Payment-attempt failure rate: "
        f"{failure_rate:.2f}%"
    )

    print(
        "\nPayment status:"
    )

    print(
        payments[
            "payment_status"
        ].value_counts()
    )

    print(
        "\nPayment method:"
    )

    print(
        payments[
            "payment_method"
        ].value_counts()
    )

    print(
        "\nSuccessful payment value:"
    )

    print(
        f"- Individual: "
        f"KES {individual_revenue:,.2f}"
    )

    print(
        f"- Organisation: "
        f"KES {organisation_revenue:,.2f}"
    )

    print(
        f"- Total: "
        f"KES "
        f"{individual_revenue + organisation_revenue:,.2f}"
    )

    print(
        f"\nSubscription events generated: "
        f"{len(events):,}"
    )

    print(
        "\nEvent types:"
    )

    print(
        events[
            "event_type"
        ].value_counts()
    )

    print(
        "\nSubscriptions with payment friction:"
    )

    print(
        failed[
            "subscription_id"
        ].nunique()
    )


# ============================================================
# MAIN
# ============================================================

def main():

    (
        subscriptions,
        trials,
        customers,
        organisations
    ) = read_inputs()

    subscriptions = add_owner_keys(
        subscriptions
    )

    relationships = (
        build_subscription_relationships(
            subscriptions,
            trials
        )
    )

    (
        payments,
        period_payment_lookup
    ) = generate_payments(
        subscriptions,
        customers
    )

    events = (
        generate_subscription_events(
            subscriptions,
            period_payment_lookup,
            relationships
        )
    )

    validate_payments(
        payments,
        subscriptions
    )

    validate_events(
        events,
        payments,
        subscriptions,
        relationships
    )

    (
        payments_path,
        events_path
    ) = save_data(
        payments,
        events
    )

    print_summary(
        payments,
        events,
        subscriptions
    )

    print(
        "\nFiles created:"
    )

    print(
        f"- {payments_path}"
    )

    print(
        f"- {events_path}"
    )


if __name__ == "__main__":
    main()