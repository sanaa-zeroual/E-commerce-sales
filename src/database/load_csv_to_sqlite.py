import pandas as pd

from src.config import CSV_FILES, DATE_COLUMNS, DATABASE_PATH
from src.database.create_database import create_database
from src.utils.db_connection import get_connection


REQUIRED_COLUMNS = {
    "customers": [
        "customer_id",
        "customer_unique_id",
        "customer_zip_code_prefix",
        "customer_city",
        "customer_state",
    ],
    "orders": [
        "order_id",
        "customer_id",
        "order_status",
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
    "order_items": [
        "order_id",
        "order_item_id",
        "product_id",
        "seller_id",
        "shipping_limit_date",
        "price",
        "freight_value",
    ],
}


def validate_csv_files():
    """Check that all required CSV files exist before loading."""
    missing_files = [str(path) for path in CSV_FILES.values() if not path.exists()]

    if missing_files:
        missing_text = "\n".join(missing_files)
        raise FileNotFoundError(
            "The following CSV files were not found:\n"
            f"{missing_text}\n\n"
            "Make sure the files are inside data/raw/."
        )


def validate_columns(table_name, dataframe):
    """Check that the CSV contains the expected columns."""
    required = set(REQUIRED_COLUMNS[table_name])
    available = set(dataframe.columns)
    missing = required - available

    if missing:
        raise ValueError(
            f"Missing columns in '{table_name}' CSV: {sorted(missing)}"
        )


def read_and_prepare_csv(table_name, csv_path):
    """Read a CSV file and prepare it before inserting it into SQLite."""
    dataframe = pd.read_csv(csv_path)
    dataframe.columns = [column.strip() for column in dataframe.columns]

    validate_columns(table_name, dataframe)

    for column in DATE_COLUMNS.get(table_name, []):
        if column in dataframe.columns:
            dataframe[column] = (
                pd.to_datetime(dataframe[column], errors="coerce")
                .dt.strftime("%Y-%m-%d %H:%M:%S")
            )

    dataframe = dataframe.where(pd.notnull(dataframe), None)
    return dataframe


def load_csv_to_sqlite():
    """Create the database and load the CSV files into SQLite tables."""
    validate_csv_files()

    # Reset the database before loading. This keeps the process repeatable.
    create_database()

    load_order = ["customers", "orders", "order_items"]

    with get_connection() as connection:
        for table_name in load_order:
            csv_path = CSV_FILES[table_name]
            dataframe = read_and_prepare_csv(table_name, csv_path)

            dataframe.to_sql(
                table_name,
                connection,
                if_exists="append",
                index=False,
            )

            print(f"[OK] Loaded {len(dataframe):,} rows into '{table_name}'.")

    print("[OK] CSV files loaded into SQLite successfully.")
    print(f"[OK] Database ready: {DATABASE_PATH}")


if __name__ == "__main__":
    load_csv_to_sqlite()