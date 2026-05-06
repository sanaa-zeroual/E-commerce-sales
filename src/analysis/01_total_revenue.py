import pandas as pd

from src.utils.db_connection import get_connection
from src.utils.export_results import export_dataframe


def calculate_total_revenue():
    """
    Calculate total revenue from delivered orders only.

    Revenue definition:
        Revenue = SUM(order_items.price)

    We only count delivered orders because canceled or unavailable
    orders should not be considered as completed revenue.
    """
    query = """
        SELECT
            'delivered_orders_only' AS revenue_scope,
            ROUND(SUM(oi.price), 2) AS total_revenue,
            COUNT(DISTINCT o.order_id) AS delivered_orders,
            COUNT(oi.order_item_id) AS total_order_items
        FROM order_items AS oi
        INNER JOIN orders AS o
            ON oi.order_id = o.order_id
        WHERE o.order_status = 'delivered';
    """

    with get_connection() as connection:
        dataframe = pd.read_sql_query(query, connection)

    return dataframe


def main():
    dataframe = calculate_total_revenue()

    output_path = export_dataframe(
        dataframe,
        "total_revenue.csv"
    )

    print("[OK] Total revenue analysis completed.")
    print(f"[OK] Results exported to: {output_path}")
    print()
    print(dataframe.to_string(index=False))


if __name__ == "__main__":
    main()