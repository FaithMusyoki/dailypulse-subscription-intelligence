"""
DAILYPULSE MEDIA
Subscription Intelligence

File: generate_base_data.py
Purpose:
    Generate the base synthetic entities for the DAILYPULSE MEDIA
    subscription intelligence project.

Generates:
    1. customers.csv
    2. organisations.csv

The generated data is fully synthetic and intended only for
portfolio and educational use.
"""

from pathlib import Path
import random
import re

import numpy as np
import pandas as pd
from faker import Faker


# ============================================================
# CONFIGURATION
# ============================================================

RANDOM_SEED = 42

NUM_CUSTOMERS = 5_000
NUM_ORGANISATIONS = 100

# Fixed dates are intentional.
# Using today's date would make the dataset change every time
# the generator is run.
DATA_START_DATE = pd.Timestamp("2025-03-01")
DATA_END_DATE = pd.Timestamp("2026-08-20")

OUTPUT_DIR = Path("data/raw")

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)
Faker.seed(RANDOM_SEED)

rng = np.random.default_rng(RANDOM_SEED)
fake = Faker("en_GB")


# ============================================================
# CUSTOMER ASSUMPTIONS
# ============================================================

CUSTOMER_COUNTRIES = {
    "Kenya": 0.72,
    "Uganda": 0.08,
    "Tanzania": 0.07,
    "Rwanda": 0.04,
    "South Africa": 0.02,
    "Nigeria": 0.02,
    "United Kingdom": 0.02,
    "United States": 0.02,
    "Canada": 0.01,
}

CUSTOMER_ACCOUNT_STATUS = {
    "active": 0.95,
    "suspended": 0.03,
    "closed": 0.02,
}


# ============================================================
# ORGANISATION ASSUMPTIONS
# ============================================================

ORGANISATION_TYPES = {
    "Corporate": 0.50,
    "University": 0.18,
    "NGO": 0.12,
    "Government": 0.10,
    "Professional Association": 0.07,
    "Other": 0.03,
}


INDUSTRIES_BY_ORGANISATION_TYPE = {
    "Corporate": [
        "Financial Services",
        "Telecommunications",
        "Manufacturing",
        "Professional Services",
        "Technology",
        "Healthcare",
        "Media",
    ],
    "University": [
        "Education",
    ],
    "NGO": [
        "Development",
        "Healthcare",
        "Education",
    ],
    "Government": [
        "Public Sector",
    ],
    "Professional Association": [
        "Professional Services",
        "Healthcare",
        "Technology",
        "Financial Services",
    ],
    "Other": [
        "Other",
        "Education",
        "Development",
        "Media",
    ],
}


# Plausible addressable population ranges.
# These are simulation assumptions rather than market statistics.

ORGANISATION_SIZE_RANGES = {
    "Corporate": (30, 12_000),
    "University": (1_500, 30_000),
    "NGO": (20, 3_000),
    "Government": (200, 10_000),
    "Professional Association": (50, 5_000),
    "Other": (20, 2_000),
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def weighted_choice(options: dict, size: int):
    """Select values according to predefined probability weights."""

    values = list(options.keys())
    probabilities = list(options.values())

    return rng.choice(
        values,
        size=size,
        p=probabilities
    )


def create_month_weights(start_date, end_date):
    """
    Create non-uniform monthly acquisition weights.

    The weights simulate:
    - gradual business growth over time
    - mild seasonal variation
    - occasional campaign periods
    """

    months = pd.date_range(
        start=start_date,
        end=end_date,
        freq="MS"
    )

    # Gradual growth across the 18-month period.
    growth_weights = np.linspace(0.75, 1.35, len(months))

    seasonal_weights = []

    for month in months:

        # Mild boosts around common acquisition/campaign periods.
        if month.month in [1, 8, 9]:
            seasonal_weights.append(1.18)

        elif month.month in [11, 12]:
            seasonal_weights.append(1.10)

        elif month.month in [4, 5]:
            seasonal_weights.append(0.92)

        else:
            seasonal_weights.append(1.00)

    weights = growth_weights * np.array(seasonal_weights)

    return months, weights / weights.sum()


def generate_signup_dates(number_of_records):
    """
    Generate realistic signup dates.

    Signups are not distributed evenly across the historical
    period. Later months receive slightly greater probability
    to simulate subscriber growth.
    """

    months, month_probabilities = create_month_weights(
        DATA_START_DATE,
        DATA_END_DATE
    )

    selected_months = rng.choice(
        months,
        size=number_of_records,
        p=month_probabilities
    )

    dates = []

    for selected_month in selected_months:

        month_start = pd.Timestamp(selected_month)

        month_end = (
            month_start
            + pd.offsets.MonthEnd(0)
        )

        # Prevent dates beyond the data cut-off.
        month_end = min(month_end, DATA_END_DATE)

        available_days = (
            month_end - month_start
        ).days + 1

        random_day_offset = rng.integers(
            0,
            available_days
        )

        signup_date = (
            month_start
            + pd.Timedelta(days=int(random_day_offset))
        )

        dates.append(signup_date.date())

    return dates


def slugify(value):
    """Convert a string into a safe synthetic email-domain slug."""

    value = value.lower()

    value = re.sub(
        r"[^a-z0-9]+",
        "-",
        value
    )

    return value.strip("-")


def generate_customer_email(first_name, last_name, customer_id):
    """
    Produce a unique, obviously synthetic email address.

    .example is a reserved domain and therefore cannot
    accidentally correspond to a real person's mailbox.
    """

    first = slugify(first_name)
    last = slugify(last_name)

    return (
        f"{first}.{last}.{customer_id.lower()}"
        "@customer.dailypulse.example"
    )


def generate_organisation_name(org_type, counter):
    """Generate fictional organisation names."""

    prefixes = [
        "Horizon",
        "Summit",
        "Pioneer",
        "Eastlands",
        "Savannah",
        "Acacia",
        "Lakeview",
        "Rift",
        "Gateway",
        "Heritage",
        "Vertex",
        "Crescent",
        "Unity",
        "Frontier",
        "Atlas",
        "Sterling",
        "BluePeak",
        "Mosaic",
        "Nexus",
        "Amani",
    ]

    corporate_suffixes = [
        "Holdings",
        "Group",
        "Industries",
        "Solutions",
        "Enterprises",
        "Technologies",
        "Partners",
        "Services",
    ]

    university_suffixes = [
        "University",
        "Institute of Technology",
        "University College",
    ]

    ngo_suffixes = [
        "Foundation",
        "Development Initiative",
        "Africa Trust",
        "Impact Network",
    ]

    government_suffixes = [
        "Development Authority",
        "Public Service Agency",
        "National Commission",
        "Regional Authority",
    ]

    association_suffixes = [
        "Professional Association",
        "Industry Association",
        "Members Council",
        "Professional Society",
    ]

    other_suffixes = [
        "Institute",
        "Network",
        "Council",
        "Centre",
    ]

    suffix_map = {
        "Corporate": corporate_suffixes,
        "University": university_suffixes,
        "NGO": ngo_suffixes,
        "Government": government_suffixes,
        "Professional Association": association_suffixes,
        "Other": other_suffixes,
    }

    prefix = rng.choice(prefixes)
    suffix = rng.choice(suffix_map[org_type])

    # Counter helps guarantee uniqueness even if name components repeat.
    return f"{prefix} {suffix} {counter:03d}"


def generate_organisation_size(org_type):
    """
    Generate organisation size using a skewed distribution.

    Most organisations sit toward the lower/middle portion
    of their allowed range, while a smaller number become
    very large institutions.
    """

    lower, upper = ORGANISATION_SIZE_RANGES[org_type]

    # Beta distribution creates a realistic right-skew:
    # many moderate organisations, fewer very large ones.
    position = rng.beta(2.0, 4.0)

    size = lower + position * (upper - lower)

    return int(round(size))


# ============================================================
# GENERATE CUSTOMERS
# ============================================================

def generate_customers():
    """Generate the individual customer master table."""

    customer_ids = [
        f"CUST{i:06d}"
        for i in range(1, NUM_CUSTOMERS + 1)
    ]

    countries = weighted_choice(
        CUSTOMER_COUNTRIES,
        NUM_CUSTOMERS
    )

    statuses = weighted_choice(
        CUSTOMER_ACCOUNT_STATUS,
        NUM_CUSTOMERS
    )

    signup_dates = generate_signup_dates(
        NUM_CUSTOMERS
    )

    records = []

    for i, customer_id in enumerate(customer_ids):

        first_name = fake.first_name()
        last_name = fake.last_name()

        email = generate_customer_email(
            first_name,
            last_name,
            customer_id
        )

        records.append({
            "customer_id": customer_id,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "signup_date": signup_dates[i],
            "country": countries[i],
            "account_status": statuses[i],
        })

    customers_df = pd.DataFrame(records)

    return customers_df


# ============================================================
# GENERATE ORGANISATIONS
# ============================================================

def generate_organisations():
    """Generate the organisation master table."""

    organisation_types = weighted_choice(
        ORGANISATION_TYPES,
        NUM_ORGANISATIONS
    )

    signup_dates = generate_signup_dates(
        NUM_ORGANISATIONS
    )

    records = []

    for i in range(NUM_ORGANISATIONS):

        organisation_id = f"ORG{i + 1:04d}"

        org_type = organisation_types[i]

        organisation_name = generate_organisation_name(
            org_type,
            i + 1
        )

        industry = rng.choice(
            INDUSTRIES_BY_ORGANISATION_TYPE[org_type]
        )

        organisation_size = generate_organisation_size(
            org_type
        )

        billing_first_name = fake.first_name()
        billing_last_name = fake.last_name()

        billing_contact_name = (
            f"{billing_first_name} {billing_last_name}"
        )

        organisation_slug = slugify(
            organisation_name
        )

        billing_contact_email = (
            f"{slugify(billing_first_name)}."
            f"{slugify(billing_last_name)}"
            f"@{organisation_slug}.example"
        )

        # Organisation accounts are overwhelmingly active,
        # with a small number suspended or closed.
        account_status = rng.choice(
            ["active", "suspended", "closed"],
            p=[0.96, 0.02, 0.02]
        )

        signup_date = signup_dates[i]

        # Simulate database creation shortly after signup.
        created_at = pd.Timestamp(signup_date) + pd.Timedelta(
            hours=int(rng.integers(0, 24)),
            minutes=int(rng.integers(0, 60))
        )

        records.append({
            "organisation_id": organisation_id,
            "organisation_name": organisation_name,
            "organisation_type": org_type,
            "industry": industry,
            "organisation_size": organisation_size,
            "signup_date": signup_date,
            "billing_contact_name": billing_contact_name,
            "billing_contact_email": billing_contact_email,
            "account_status": account_status,
            "created_at": created_at,
        })

    organisations_df = pd.DataFrame(records)

    return organisations_df


# ============================================================
# VALIDATION
# ============================================================

def validate_customers(customers_df):
    """Run basic quality checks before saving customer data."""

    assert len(customers_df) == NUM_CUSTOMERS

    assert customers_df["customer_id"].is_unique
    assert customers_df["email"].is_unique

    assert customers_df["customer_id"].notna().all()
    assert customers_df["email"].notna().all()
    assert customers_df["signup_date"].notna().all()

    assert customers_df["account_status"].isin(
        ["active", "suspended", "closed"]
    ).all()


def validate_organisations(organisations_df):
    """Run basic quality checks before saving organisation data."""

    assert len(organisations_df) == NUM_ORGANISATIONS

    assert organisations_df["organisation_id"].is_unique
    assert organisations_df["organisation_name"].is_unique

    assert (
        organisations_df["organisation_size"] > 0
    ).all()

    assert organisations_df["account_status"].isin(
        ["active", "suspended", "closed"]
    ).all()


# ============================================================
# SAVE DATA
# ============================================================

def save_data(customers_df, organisations_df):
    """Save generated datasets as CSV files."""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    customers_path = OUTPUT_DIR / "customers.csv"
    organisations_path = OUTPUT_DIR / "organisations.csv"

    customers_df.to_csv(
        customers_path,
        index=False
    )

    organisations_df.to_csv(
        organisations_path,
        index=False
    )

    return customers_path, organisations_path


# ============================================================
# SUMMARY
# ============================================================

def print_summary(customers_df, organisations_df):
    """Display a simple validation summary after generation."""

    print("\n" + "=" * 60)
    print("DAILYPULSE MEDIA — BASE DATA GENERATION COMPLETE")
    print("=" * 60)

    print(f"\nCustomers generated: {len(customers_df):,}")
    print(f"Organisations generated: {len(organisations_df):,}")

    print("\nCustomer country distribution:")
    print(
        customers_df["country"]
        .value_counts(normalize=True)
        .mul(100)
        .round(1)
        .astype(str)
        + "%"
    )

    print("\nCustomer account status:")
    print(
        customers_df["account_status"]
        .value_counts()
    )

    print("\nOrganisation type distribution:")
    print(
        organisations_df["organisation_type"]
        .value_counts()
    )

    print("\nOrganisation size summary:")
    print(
        organisations_df["organisation_size"]
        .describe()
        .round(0)
    )


# ============================================================
# MAIN
# ============================================================

def main():

    customers_df = generate_customers()

    organisations_df = generate_organisations()

    validate_customers(
        customers_df
    )

    validate_organisations(
        organisations_df
    )

    customers_path, organisations_path = save_data(
        customers_df,
        organisations_df
    )

    print_summary(
        customers_df,
        organisations_df
    )

    print("\nFiles created:")
    print(f"- {customers_path}")
    print(f"- {organisations_path}")


if __name__ == "__main__":
    main()
