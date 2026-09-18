"""
DAILYPULSE MEDIA
Subscription Intelligence

File: load_commercial_data.py

Purpose:
    Load approved payments and subscription events
    into PostgreSQL.

Load order:
    1. Payments
    2. Subscription events

Events are loaded second because some events reference
triggering_payment_id.
"""

from pathlib import Path
import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


# ============================================================
# CONFIGURATION
# ============================================================

PAYMENTS_PATH = Path(
    "data/raw/payments.csv"
)

EVENTS_PATH = Path(
    "data/raw/subscription_events.csv"
)

EXPECTED_SUBSCRIPTIONS = 3_333
EXPECTED_PAYMENTS = 13_259
EXPECTED_SUCCESSFUL_PAYMENTS = 12_817
EXPECTED_FAILED_PAYMENTS = 442
EXPECTED_EVENTS = 16_668


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_database_engine():

    load_dotenv()

    database_url = os.getenv(
        "DATABASE_URL"
    )

    if not database_url:
        raise ValueError(
            "DATABASE_URL was not found in .env."
        )

    if database_url.startswith(
        "postgresql://"
    ):
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

    payments = pd.read_csv(
        PAYMENTS_PATH
    )

    events = pd.read_csv(
        EVENTS_PATH
    )

    for column in [
        "payment_attempted_at",
        "created_at",
    ]:

        payments[column] = pd.to_datetime(
            payments[column],
            errors="coerce"
        )

    for column in [
        "event_at",
        "created_at",
    ]:

        events[column] = pd.to_datetime(
            events[column],
            errors="coerce"
        )

    for column in [
        "period_start",
        "period_end",
    ]:

        events[column] = pd.to_datetime(
            events[column],
            errors="coerce"
        ).dt.date

    return (
        payments,
        events
    )


# ============================================================
# LOCAL VALIDATION
# ============================================================

def validate_local_data(
    payments,
    events
):

    if len(payments) != EXPECTED_PAYMENTS:
        raise ValueError(
            f"Expected {EXPECTED_PAYMENTS:,} payments, "
            f"found {len(payments):,}."
        )

    if len(events) != EXPECTED_EVENTS:
        raise ValueError(
            f"Expected {EXPECTED_EVENTS:,} events, "
            f"found {len(events):,}."
        )

    if not payments[
        "payment_id"
    ].is_unique:
        raise ValueError(
            "Duplicate payment IDs detected."
        )

    if not events[
        "event_id"
    ].is_unique:
        raise ValueError(
            "Duplicate event IDs detected."
        )

    successful_count = (
        payments[
            "payment_status"
        ]
        .eq(
            "successful"
        )
        .sum()
    )

    failed_count = (
        payments[
            "payment_status"
        ]
        .eq(
            "failed"
        )
        .sum()
    )

    if (
        successful_count
        != EXPECTED_SUCCESSFUL_PAYMENTS
    ):
        raise ValueError(
            "Successful payment count mismatch."
        )

    if (
        failed_count
        != EXPECTED_FAILED_PAYMENTS
    ):
        raise ValueError(
            "Failed payment count mismatch."
        )

    valid_payment_ids = set(
        payments[
            "payment_id"
        ].astype(str)
    )

    triggering_payment_ids = set(
        events[
            "triggering_payment_id"
        ]
        .dropna()
        .astype(str)
    )

    if not triggering_payment_ids.issubset(
        valid_payment_ids
    ):
        raise ValueError(
            "Event references unknown payment ID."
        )

    print(
        "\nLocal commercial validation successful."
    )


# ============================================================
# CHECK DATABASE STATE
# ============================================================

def check_database(
    engine
):

    with engine.connect() as connection:

        subscription_count = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM subscriptions;
                """
            )
        ).scalar_one()

        payment_count = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM payments;
                """
            )
        ).scalar_one()

        event_count = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM subscription_events;
                """
            )
        ).scalar_one()

    print(
        "\nCurrent database counts:"
    )

    print(
        f"- subscriptions: "
        f"{subscription_count:,}"
    )

    print(
        f"- payments: "
        f"{payment_count:,}"
    )

    print(
        f"- subscription_events: "
        f"{event_count:,}"
    )

    if (
        subscription_count
        != EXPECTED_SUBSCRIPTIONS
    ):
        raise RuntimeError(
            "Subscription table does not contain "
            "the expected 3,333 records."
        )

    if payment_count > 0:
        raise RuntimeError(
            "LOAD STOPPED: payments already contain data."
        )

    if event_count > 0:
        raise RuntimeError(
            "LOAD STOPPED: subscription_events "
            "already contain data."
        )


# ============================================================
# LOAD COMMERCIAL DATA
# ============================================================

def load_commercial_data(
    engine,
    payments,
    events
):
    """
    Load both datasets inside one transaction.

    If either table fails, the entire transaction
    is rolled back.
    """

    with engine.begin() as connection:

        print(
            "\nLoading payments..."
        )

        payments.to_sql(
            "payments",
            con=connection,
            if_exists="append",
            index=False,
            chunksize=500,
            method="multi"
        )

        print(
            "Loading subscription events..."
        )

        events.to_sql(
            "subscription_events",
            con=connection,
            if_exists="append",
            index=False,
            chunksize=500,
            method="multi"
        )


# ============================================================
# VERIFY DATABASE
# ============================================================

def verify_load(
    engine
):

    with engine.connect() as connection:

        payment_count = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM payments;
                """
            )
        ).scalar_one()

        successful_count = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM payments
                WHERE payment_status = 'successful';
                """
            )
        ).scalar_one()

        failed_count = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM payments
                WHERE payment_status = 'failed';
                """
            )
        ).scalar_one()

        event_count = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM subscription_events;
                """
            )
        ).scalar_one()

        orphan_payments = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM payments p
                LEFT JOIN subscriptions s
                  ON p.subscription_id = s.subscription_id
                WHERE s.subscription_id IS NULL;
                """
            )
        ).scalar_one()

        orphan_events = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM subscription_events e
                LEFT JOIN subscriptions s
                  ON e.subscription_id = s.subscription_id
                WHERE s.subscription_id IS NULL;
                """
            )
        ).scalar_one()

        bad_payment_links = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM subscription_events e
                LEFT JOIN payments p
                  ON e.triggering_payment_id = p.payment_id
                WHERE e.triggering_payment_id IS NOT NULL
                  AND p.payment_id IS NULL;
                """
            )
        ).scalar_one()

        started_events = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM subscription_events
                WHERE event_type = 'subscription_started';
                """
            )
        ).scalar_one()

        plan_change_events = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM subscription_events
                WHERE event_type = 'plan_changed';
                """
            )
        ).scalar_one()

        ended_events = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM subscription_events
                WHERE event_type = 'subscription_ended';
                """
            )
        ).scalar_one()

    print(
        "\nDatabase verification:"
    )

    print(
        f"- payments: {payment_count:,}"
    )

    print(
        f"- successful payments: "
        f"{successful_count:,}"
    )

    print(
        f"- failed payments: "
        f"{failed_count:,}"
    )

    print(
        f"- subscription events: "
        f"{event_count:,}"
    )

    print(
        f"- subscription_started events: "
        f"{started_events:,}"
    )

    print(
        f"- plan_changed events: "
        f"{plan_change_events:,}"
    )

    print(
        f"- subscription_ended events: "
        f"{ended_events:,}"
    )

    print(
        f"- orphan payments: "
        f"{orphan_payments:,}"
    )

    print(
        f"- orphan events: "
        f"{orphan_events:,}"
    )

    print(
        f"- invalid triggering payment links: "
        f"{bad_payment_links:,}"
    )

    if payment_count != EXPECTED_PAYMENTS:
        raise RuntimeError(
            "Payment count mismatch."
        )

    if (
        successful_count
        != EXPECTED_SUCCESSFUL_PAYMENTS
    ):
        raise RuntimeError(
            "Successful payment count mismatch."
        )

    if (
        failed_count
        != EXPECTED_FAILED_PAYMENTS
    ):
        raise RuntimeError(
            "Failed payment count mismatch."
        )

    if event_count != EXPECTED_EVENTS:
        raise RuntimeError(
            "Subscription event count mismatch."
        )

    if started_events != 3_333:
        raise RuntimeError(
            "subscription_started event mismatch."
        )

    if plan_change_events != 368:
        raise RuntimeError(
            "plan_changed event mismatch."
        )

    if ended_events != 1_636:
        raise RuntimeError(
            "subscription_ended event mismatch."
        )

    if orphan_payments != 0:
        raise RuntimeError(
            "Orphan payment detected."
        )

    if orphan_events != 0:
        raise RuntimeError(
            "Orphan subscription event detected."
        )

    if bad_payment_links != 0:
        raise RuntimeError(
            "Invalid triggering payment reference."
        )

    print(
        "\nCommercial data loaded "
        "and verified successfully."
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "=" * 65
    )

    print(
        "DAILYPULSE MEDIA — COMMERCIAL DATABASE LOAD"
    )

    print(
        "=" * 65
    )

    (
        payments,
        events
    ) = read_data()

    validate_local_data(
        payments,
        events
    )

    engine = get_database_engine()

    check_database(
        engine
    )

    load_commercial_data(
        engine,
        payments,
        events
    )

    verify_load(
        engine
    )

    engine.dispose()


if __name__ == "__main__":
    main()