"""
DAILYPULSE MEDIA
Subscription Intelligence

File: load_subscription_data.py

Purpose:
    Synchronise reconciled account statuses and load
    subscriptions and final trial records into PostgreSQL.

Load order:
    1. Reconcile customer and organisation account statuses
    2. Load subscriptions
    3. Load trials

Subscriptions must be loaded before trials because converted
trials reference subscription_id.
"""

from pathlib import Path
import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


# ============================================================
# CONFIGURATION
# ============================================================

CUSTOMERS_PATH = Path("data/raw/customers.csv")
ORGANISATIONS_PATH = Path("data/raw/organisations.csv")
SUBSCRIPTIONS_PATH = Path("data/raw/subscriptions.csv")
TRIALS_PATH = Path("data/raw/trials.csv")

EXPECTED_CUSTOMERS = 5_000
EXPECTED_ORGANISATIONS = 100
EXPECTED_SUBSCRIPTIONS = 3_333
EXPECTED_TRIALS = 1_917
EXPECTED_CONVERTED_TRIALS = 982


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_database_engine():

    load_dotenv()

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError(
            "DATABASE_URL was not found in .env."
        )

    if database_url.startswith("postgresql://"):
        database_url = database_url.replace(
            "postgresql://",
            "postgresql+psycopg://",
            1
        )

    return create_engine(
        database_url,
        pool_pre_ping=True
    )


# ============================================================
# READ DATA
# ============================================================

def read_data():

    customers = pd.read_csv(
        CUSTOMERS_PATH
    )

    organisations = pd.read_csv(
        ORGANISATIONS_PATH
    )

    subscriptions = pd.read_csv(
        SUBSCRIPTIONS_PATH
    )

    trials = pd.read_csv(
        TRIALS_PATH
    )

    # Subscription date fields
    for column in [
        "subscription_start_date",
        "current_period_start",
        "current_period_end",
        "subscription_end_date",
    ]:

        subscriptions[column] = pd.to_datetime(
            subscriptions[column],
            errors="coerce"
        )

    subscriptions[
        "cancellation_requested_at"
    ] = pd.to_datetime(
        subscriptions[
            "cancellation_requested_at"
        ],
        errors="coerce"
    )

    subscriptions["created_at"] = pd.to_datetime(
        subscriptions["created_at"],
        errors="coerce"
    )

    # Trial timestamp fields
    for column in [
        "trial_started_at",
        "scheduled_end_at",
        "actual_end_at",
        "created_at",
    ]:

        trials[column] = pd.to_datetime(
            trials[column],
            errors="coerce"
        )

    return (
        customers,
        organisations,
        subscriptions,
        trials
    )


# ============================================================
# LOCAL VALIDATION
# ============================================================

def validate_local_data(
    customers,
    organisations,
    subscriptions,
    trials
):

    if len(customers) != EXPECTED_CUSTOMERS:
        raise ValueError(
            f"Expected {EXPECTED_CUSTOMERS:,} customers."
        )

    if len(organisations) != EXPECTED_ORGANISATIONS:
        raise ValueError(
            f"Expected {EXPECTED_ORGANISATIONS:,} organisations."
        )

    if len(subscriptions) != EXPECTED_SUBSCRIPTIONS:
        raise ValueError(
            f"Expected {EXPECTED_SUBSCRIPTIONS:,} subscriptions, "
            f"found {len(subscriptions):,}."
        )

    if len(trials) != EXPECTED_TRIALS:
        raise ValueError(
            f"Expected {EXPECTED_TRIALS:,} trials, "
            f"found {len(trials):,}."
        )

    if not subscriptions[
        "subscription_id"
    ].is_unique:
        raise ValueError(
            "Duplicate subscription IDs detected."
        )

    if not trials[
        "trial_id"
    ].is_unique:
        raise ValueError(
            "Duplicate trial IDs detected."
        )

    converted_trials = trials[
        trials["trial_status"] == "converted"
    ]

    if len(
        converted_trials
    ) != EXPECTED_CONVERTED_TRIALS:

        raise ValueError(
            "Unexpected converted trial count."
        )

    if converted_trials[
        "converted_subscription_id"
    ].isna().any():

        raise ValueError(
            "Converted trial missing subscription linkage."
        )

    subscription_ids = set(
        subscriptions["subscription_id"]
    )

    converted_ids = set(
        converted_trials[
            "converted_subscription_id"
        ]
    )

    if not converted_ids.issubset(
        subscription_ids
    ):
        raise ValueError(
            "Trial references unknown subscription ID."
        )


# ============================================================
# CHECK DATABASE STATE
# ============================================================

def check_database(engine):

    with engine.connect() as connection:

        customer_count = connection.execute(
            text(
                "SELECT COUNT(*) FROM customers;"
            )
        ).scalar_one()

        organisation_count = connection.execute(
            text(
                "SELECT COUNT(*) FROM organisations;"
            )
        ).scalar_one()

        subscription_count = connection.execute(
            text(
                "SELECT COUNT(*) FROM subscriptions;"
            )
        ).scalar_one()

        trial_count = connection.execute(
            text(
                "SELECT COUNT(*) FROM trials;"
            )
        ).scalar_one()

    print("\nCurrent database counts:")
    print(f"- customers: {customer_count:,}")
    print(f"- organisations: {organisation_count:,}")
    print(f"- subscriptions: {subscription_count:,}")
    print(f"- trials: {trial_count:,}")

    if customer_count != EXPECTED_CUSTOMERS:
        raise RuntimeError(
            "Customer base is incomplete."
        )

    if organisation_count != EXPECTED_ORGANISATIONS:
        raise RuntimeError(
            "Organisation base is incomplete."
        )

    if subscription_count > 0:
        raise RuntimeError(
            "LOAD STOPPED: subscriptions already contain data."
        )

    if trial_count > 0:
        raise RuntimeError(
            "LOAD STOPPED: trials already contain data."
        )


# ============================================================
# LOAD LIFECYCLE
# ============================================================

def load_lifecycle(
    engine,
    customers,
    organisations,
    subscriptions,
    trials
):
    """
    Run reconciliation and inserts in one transaction.

    If anything fails, PostgreSQL rolls back the entire operation.
    """

    customer_status_updates = (
        customers[
            ["customer_id", "account_status"]
        ]
        .to_dict("records")
    )

    organisation_status_updates = (
        organisations[
            ["organisation_id", "account_status"]
        ]
        .to_dict("records")
    )

    with engine.begin() as connection:

        # Synchronise reconciled customer statuses.
        connection.execute(
            text(
                """
                UPDATE customers
                SET account_status = :account_status
                WHERE customer_id = :customer_id;
                """
            ),
            customer_status_updates
        )

        # Synchronise reconciled organisation statuses.
        connection.execute(
            text(
                """
                UPDATE organisations
                SET account_status = :account_status
                WHERE organisation_id = :organisation_id;
                """
            ),
            organisation_status_updates
        )

        # Subscriptions first.
        subscriptions.to_sql(
            "subscriptions",
            con=connection,
            if_exists="append",
            index=False,
            chunksize=500,
            method="multi"
        )

        # Trials second because converted trials reference subscriptions.
        trials.to_sql(
            "trials",
            con=connection,
            if_exists="append",
            index=False,
            chunksize=500,
            method="multi"
        )


# ============================================================
# VERIFY DATABASE
# ============================================================

def verify_load(engine):

    with engine.connect() as connection:

        subscription_count = connection.execute(
            text(
                "SELECT COUNT(*) FROM subscriptions;"
            )
        ).scalar_one()

        trial_count = connection.execute(
            text(
                "SELECT COUNT(*) FROM trials;"
            )
        ).scalar_one()

        linked_converted_trials = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM trials
                WHERE trial_status = 'converted'
                  AND converted_subscription_id IS NOT NULL;
                """
            )
        ).scalar_one()

        closed_customer_conflicts = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM subscriptions s
                JOIN customers c
                  ON s.customer_id = c.customer_id
                WHERE s.status = 'active'
                  AND c.account_status = 'closed';
                """
            )
        ).scalar_one()

        closed_organisation_conflicts = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM subscriptions s
                JOIN organisations o
                  ON s.organisation_id = o.organisation_id
                WHERE s.status = 'active'
                  AND o.account_status = 'closed';
                """
            )
        ).scalar_one()

    print("\nDatabase verification:")
    print(
        f"- subscriptions: {subscription_count:,}"
    )
    print(
        f"- trials: {trial_count:,}"
    )
    print(
        f"- linked converted trials: "
        f"{linked_converted_trials:,}"
    )
    print(
        f"- closed customer conflicts: "
        f"{closed_customer_conflicts:,}"
    )
    print(
        f"- closed organisation conflicts: "
        f"{closed_organisation_conflicts:,}"
    )

    if subscription_count != EXPECTED_SUBSCRIPTIONS:
        raise RuntimeError(
            "Subscription count mismatch."
        )

    if trial_count != EXPECTED_TRIALS:
        raise RuntimeError(
            "Trial count mismatch."
        )

    if linked_converted_trials != EXPECTED_CONVERTED_TRIALS:
        raise RuntimeError(
            "Converted trial linkage mismatch."
        )

    if closed_customer_conflicts != 0:
        raise RuntimeError(
            "Closed customer still has active subscription."
        )

    if closed_organisation_conflicts != 0:
        raise RuntimeError(
            "Closed organisation still has active subscription."
        )

    print(
        "\nSubscription lifecycle loaded "
        "and verified successfully."
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 65)
    print(
        "DAILYPULSE MEDIA — SUBSCRIPTION LIFECYCLE DATABASE LOAD"
    )
    print("=" * 65)

    (
        customers,
        organisations,
        subscriptions,
        trials
    ) = read_data()

    validate_local_data(
        customers,
        organisations,
        subscriptions,
        trials
    )

    print(
        "\nLocal lifecycle validation successful."
    )

    engine = get_database_engine()

    check_database(
        engine
    )

    print(
        "\nLoading subscription lifecycle into PostgreSQL..."
    )

    load_lifecycle(
        engine,
        customers,
        organisations,
        subscriptions,
        trials
    )

    verify_load(
        engine
    )

    engine.dispose()


if __name__ == "__main__":
    main()