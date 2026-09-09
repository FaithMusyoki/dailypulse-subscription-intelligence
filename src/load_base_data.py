"""
DAILYPULSE MEDIA
Subscription Intelligence

File: load_base_data.py

Purpose:
    Load the approved synthetic base datasets into the
    DAILYPULSE PostgreSQL database hosted on Supabase.

Loads:
    1. customers.csv      -> customers
    2. organisations.csv  -> organisations
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

EXPECTED_CUSTOMERS = 5_000
EXPECTED_ORGANISATIONS = 100


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_database_engine():
    """
    Read the Supabase connection string from .env
    and create a SQLAlchemy database engine.
    """

    load_dotenv()

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError(
            "DATABASE_URL was not found. "
            "Check that your .env file exists and contains DATABASE_URL."
        )

    # Explicitly tell SQLAlchemy to use psycopg v3.
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace(
            "postgresql://",
            "postgresql+psycopg://",
            1
        )

    engine = create_engine(
        database_url,
        pool_pre_ping=True
    )

    return engine


# ============================================================
# CHECK INPUT FILES
# ============================================================

def validate_input_files():
    """Confirm that the generated CSV files exist."""

    missing_files = []

    if not CUSTOMERS_PATH.exists():
        missing_files.append(str(CUSTOMERS_PATH))

    if not ORGANISATIONS_PATH.exists():
        missing_files.append(str(ORGANISATIONS_PATH))

    if missing_files:
        raise FileNotFoundError(
            "Missing required input file(s): "
            + ", ".join(missing_files)
        )


# ============================================================
# READ DATA
# ============================================================

def read_base_data():
    """Read and correctly type the approved synthetic base datasets."""

    customers_df = pd.read_csv(
        CUSTOMERS_PATH
    )

    organisations_df = pd.read_csv(
        ORGANISATIONS_PATH
    )

    # Convert customer date fields from CSV text to real dates.
    customers_df["signup_date"] = pd.to_datetime(
        customers_df["signup_date"]
    ).dt.date

    # Convert organisation date/timestamp fields.
    organisations_df["signup_date"] = pd.to_datetime(
        organisations_df["signup_date"]
    ).dt.date

    organisations_df["created_at"] = pd.to_datetime(
        organisations_df["created_at"]
    )

    return customers_df, organisations_df

# ============================================================
# VALIDATE DATA
# ============================================================

def validate_base_data(customers_df, organisations_df):
    """
    Run final checks before anything is sent
    to PostgreSQL.
    """

    if len(customers_df) != EXPECTED_CUSTOMERS:
        raise ValueError(
            f"Expected {EXPECTED_CUSTOMERS:,} customers, "
            f"but found {len(customers_df):,}."
        )

    if len(organisations_df) != EXPECTED_ORGANISATIONS:
        raise ValueError(
            f"Expected {EXPECTED_ORGANISATIONS:,} organisations, "
            f"but found {len(organisations_df):,}."
        )

    if not customers_df["customer_id"].is_unique:
        raise ValueError(
            "Duplicate customer_id values detected."
        )

    if not customers_df["email"].is_unique:
        raise ValueError(
            "Duplicate customer email addresses detected."
        )

    if not organisations_df["organisation_id"].is_unique:
        raise ValueError(
            "Duplicate organisation_id values detected."
        )


# ============================================================
# TEST DATABASE CONNECTION
# ============================================================

def test_connection(engine):
    """
    Confirm that Codespaces can successfully communicate
    with the Supabase PostgreSQL database.
    """

    with engine.connect() as connection:

        result = connection.execute(
            text(
                """
                SELECT
                    current_database() AS database_name,
                    current_user AS database_user;
                """
            )
        ).mappings().one()

    print("\nDatabase connection successful.")
    print(
        f"Database: {result['database_name']}"
    )
    print(
        f"Connected user: {result['database_user']}"
    )


# ============================================================
# CHECK EXISTING RECORDS
# ============================================================

def check_existing_records(engine):
    """
    Check whether the destination tables already contain data.

    The loader deliberately stops if records already exist
    to protect against accidental duplicate inserts.
    """

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

    print("\nCurrent database counts:")
    print(
        f"- customers: {customer_count:,}"
    )
    print(
        f"- organisations: {organisation_count:,}"
    )

    if customer_count > 0 or organisation_count > 0:
        raise RuntimeError(
            "\nLOAD STOPPED.\n"
            "The customers or organisations table already "
            "contains records. No data has been inserted."
        )


# ============================================================
# LOAD DATA
# ============================================================

def load_data(
    engine,
    customers_df,
    organisations_df
):
    """
    Insert the two base datasets into PostgreSQL.

    Both tables are loaded inside one database transaction.
    If either insert fails, the entire transaction is rolled back.
    """

    with engine.begin() as connection:

        customers_df.to_sql(
            "customers",
            con=connection,
            if_exists="append",
            index=False,
            chunksize=500,
            method="multi"
        )

        organisations_df.to_sql(
            "organisations",
            con=connection,
            if_exists="append",
            index=False,
            chunksize=100,
            method="multi"
        )


# ============================================================
# VERIFY LOAD
# ============================================================

def verify_load(engine):
    """
    Verify the number of records actually stored
    in PostgreSQL after loading.
    """

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

    print("\nDatabase verification:")
    print(
        f"- customers: {customer_count:,}"
    )
    print(
        f"- organisations: {organisation_count:,}"
    )

    if customer_count != EXPECTED_CUSTOMERS:
        raise RuntimeError(
            "Customer count does not match expected total."
        )

    if organisation_count != EXPECTED_ORGANISATIONS:
        raise RuntimeError(
            "Organisation count does not match expected total."
        )

    print(
        "\nBase data loaded and verified successfully."
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("DAILYPULSE MEDIA — BASE DATABASE LOAD")
    print("=" * 60)

    validate_input_files()

    customers_df, organisations_df = read_base_data()

    validate_base_data(
        customers_df,
        organisations_df
    )

    print("\nLocal data validation successful.")
    print(
        f"Customers ready: {len(customers_df):,}"
    )
    print(
        f"Organisations ready: {len(organisations_df):,}"
    )

    engine = get_database_engine()

    test_connection(engine)

    check_existing_records(engine)

    print("\nLoading base data into PostgreSQL...")

    load_data(
        engine,
        customers_df,
        organisations_df
    )

    verify_load(engine)

    engine.dispose()


if __name__ == "__main__":
    main()