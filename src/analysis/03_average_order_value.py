import pandas as pd

from src.utils.db_connection import get_connection
from src.utils.export_results import export_dataframe


def calculate_average_order_value():
    """
    Calculate the Average Order Value for delivered orders only.

    Method:
        1. Calculate revenue for each delivered order.
        2. Calculate the average of these order revenues.

    Formula:
        Average Order Value = Total Revenue / Number of Delivered Orders
    """
    query = """
        WITH order_revenue AS (
            SELECT
                o.order_id,
                ROUND(SUM(oi.price), 2) AS order_value
            FROM orders AS o
            INNER JOIN order_items AS oi
                ON o.order_id = oi.order_id
            WHERE o.order_status = 'delivered'
            GROUP BY o.order_id
        )

        SELECT
            COUNT(order_id) AS delivered_orders,
            ROUND(SUM(order_value), 2) AS total_revenue,
            ROUND(AVG(order_value), 2) AS average_order_value,
            ROUND(MIN(order_value), 2) AS minimum_order_value,
            ROUND(MAX(order_value), 2) AS maximum_order_value
        FROM order_revenue;
    """

    with get_connection() as connection:
        dataframe = pd.read_sql_query(query, connection)

    return dataframe


def main():
    dataframe = calculate_average_order_value()

    output_path = export_dataframe(
        dataframe,
        "average_order_value.csv"
    )

    print("[OK] Average order value analysis completed.")
    print(f"[OK] Results exported to: {output_path}")
    print()
    print(dataframe.to_string(index=False))


if __name__ == "__main__":
    main()