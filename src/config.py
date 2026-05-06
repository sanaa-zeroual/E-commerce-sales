from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
DATABASE_DIR = DATA_DIR / "database"
EXPORTS_DIR = DATA_DIR / "exports"

DATABASE_PATH = DATABASE_DIR / "ecommerce.db"

CSV_FILES = {
    "customers": RAW_DATA_DIR / "olist_customers_dataset.csv",
    "orders": RAW_DATA_DIR / "olist_orders_dataset.csv",
    "order_items": RAW_DATA_DIR / "olist_order_items_dataset.csv",
}

TABLES = ["customers", "orders", "order_items"]

DATE_COLUMNS = {
    "orders": [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
    "order_items": ["shipping_limit_date"],
}


def ensure_project_dirs():
    """Create required data folders if they do not exist."""
    for path in [RAW_DATA_DIR, DATABASE_DIR, EXPORTS_DIR]:
        path.mkdir(parents=True, exist_ok=True)