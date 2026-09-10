"""
DAILYPULSE MEDIA
Subscription Intelligence

File: load_acquisition_data.py

Purpose:
    Load approved marketing acquisition data into
    the DAILYPULSE PostgreSQL database.

Loads:
    marketing_touchpoints.csv -> marketing_touchpoints

Important:
    trial_staging.csv is deliberately NOT loaded yet.
"""

from pathlib import Path
import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


# ============================================================
# CONFIGURATION
# ============================================================

TOUCHPOINTS_PATH = Path(
    "data/raw/marketing_touchpoints.csv"
)

EXPECTED_MIN_TOUCHPOINTS = 15_000
EXPECTED_MAX_TOUCHPOINTS = 25_000


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_database_engine():
    """Create a secure PostgreSQL connection using .env."""

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

def read_touchpoints():
    """Read and correctly type marketing touchpoint data."""

    if not TOUCHPOINTS_PATH.exists():
        raise FileNotFoundError(
            f"{TOUCHPOINTS_PATH} not found. "
            "Run generate_acquisition_data.py first."
        )

    df = pd.read_csv(
        TOUCHPOINTS_PATH
    )

    df["touchpoint_at"] = pd.to_datetime(
        df["touchpoint_at"]
    )

    df["created_at"] = pd.to_datetime(
        df["created_at"]
    )

    return df


# ============================================================
# VALIDATE LOCAL DATA
# ============================================================

def validate_touchpoints(df):
    """Run quality checks before database insertion."""

    if not (
        EXPECTED_MIN_TOUCHPOINTS
        <= len(df)
        <= EXPECTED_MAX_TOUCHPOINTS
    ):
        raise ValueError(
            f"Unexpected touchpoint volume: {len(df):,}"
        )

    if not df["touchpoint_id"].is_unique:
        raise ValueError(
            "Duplicate touchpoint IDs detected."
        )

    required_columns = [
        "touchpoint_id",
        "customer_id",
        "touchpoint_at",
        "channel",
        "touchpoint_type",
        "created_at",
    ]

    if df[required_columns].isnull().any().any():
        raise ValueError(
            "Missing required values detected."
        )

    if (
        df["attributed_cost"]
        .dropna()
        .lt(0)
        .any()
    ):
        raise ValueError(
            "Negative attributed cost detected."
        )


# ============================================================
# CHECK DATABASE
# ============================================================

def check_database(engine, df):
    """
    Confirm customers exist and destination table is empty.
    """

    with engine.connect() as connection:

        customer_count = connection.execute(
            text(
                "SELECT COUNT(*) FROM customers;"
            )
        ).scalar_one()

        existing_touchpoints = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM marketing_touchpoints;
                """
            )
        ).scalar_one()

    print("\nCurrent database counts:")
    print(f"- customers: {customer_count:,}")
    print(
        f"- marketing_touchpoints: "
        f"{existing_touchpoints:,}"
    )

    if customer_count != 5_000:
        raise RuntimeError(
            "Expected 5,000 customers before "
            "loading marketing data."
        )

    if existing_touchpoints > 0:
        raise RuntimeError(
            "LOAD STOPPED: marketing_touchpoints "
            "already contains records."
        )

    print(
        f"\nTouchpoints ready to load: {len(df):,}"
    )


# ============================================================
# LOAD DATA
# ============================================================

def load_touchpoints(engine, df):
    """Insert marketing touchpoints inside one transaction."""

    with engine.begin() as connection:

        df.to_sql(
            "marketing_touchpoints",
            con=connection,
            if_exists="append",
            index=False,
            chunksize=1_000,
            method="multi"
        )


# ============================================================
# VERIFY LOAD
# ============================================================

def verify_load(engine, expected_count):
    """Confirm PostgreSQL received every touchpoint."""

    with engine.connect() as connection:

        database_count = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM marketing_touchpoints;
                """
            )
        ).scalar_one()

    print("\nDatabase verification:")
    print(
        f"- marketing_touchpoints: "
        f"{database_count:,}"
    )

    if database_count != expected_count:
        raise RuntimeError(
            "Database count does not match "
            "the generated touchpoint count."
        )

    print(
        "\nMarketing touchpoints loaded "
        "and verified successfully."
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print(
        "DAILYPULSE MEDIA — ACQUISITION DATABASE LOAD"
    )
    print("=" * 60)

    touchpoints_df = read_touchpoints()

    validate_touchpoints(
        touchpoints_df
    )

    print("\nLocal data validation successful.")

    engine = get_database_engine()

    check_database(
        engine,
        touchpoints_df
    )

    print(
        "\nLoading marketing touchpoints "
        "into PostgreSQL..."
    )

    load_touchpoints(
        engine,
        touchpoints_df
    )

    verify_load(
        engine,
        len(touchpoints_df)
    )

    engine.dispose()


if __name__ == "__main__":
    main()