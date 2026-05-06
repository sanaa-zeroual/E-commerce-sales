from src.config import DATABASE_PATH, TABLES
from src.utils.db_connection import get_connection


def count_rows(connection, table_name):
    cursor = connection.execute(f"SELECT COUNT(*) FROM {table_name};")
    return cursor.fetchone()[0]


def check_relationships(connection):
    orders_without_customer = connection.execute(
        """
        SELECT COUNT(*)
        FROM orders AS o
        LEFT JOIN customers AS c
            ON o.customer_id = c.customer_id
        WHERE c.customer_id IS NULL;
        """
    ).fetchone()[0]

    items_without_order = connection.execute(
        """
        SELECT COUNT(*)
        FROM order_items AS oi
        LEFT JOIN orders AS o
            ON oi.order_id = o.order_id
        WHERE o.order_id IS NULL;
        """
    ).fetchone()[0]

    return orders_without_customer, items_without_order


def check_database():
    """Print basic checks for the SQLite database."""
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH}\n"
            "Run: python -m src.database.load_csv_to_sqlite"
        )

    with get_connection() as connection:
        available_tables = [
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table';"
            ).fetchall()
        ]

        print("[INFO] Database path:")
        print(f"       {DATABASE_PATH}")
        print()

        print("[INFO] Tables found:")
        for table in available_tables:
            print(f"       - {table}")
        print()

        print("[INFO] Row counts:")
        for table in TABLES:
            if table in available_tables:
                print(f"       {table}: {count_rows(connection, table):,} rows")
            else:
                print(f"       {table}: NOT FOUND")
        print()

        orders_without_customer, items_without_order = check_relationships(connection)

        print("[INFO] Relationship checks:")
        print(f"       Orders without customer: {orders_without_customer:,}")
        print(f"       Order items without order: {items_without_order:,}")
        print()

        if orders_without_customer == 0 and items_without_order == 0:
            print("[OK] Database check completed successfully.")
        else:
            print("[WARNING] Some relationship issues were found.")


if __name__ == "__main__":
    check_database()