import pandas as pd

from src.utils.db_connection import get_connection
from src.utils.export_results import export_dataframe


def get_order_status_analysis():
    """
    Analyze order status distribution.

    This analysis includes all orders, not only delivered orders,
    because the goal is to understand how orders are distributed
    across different statuses such as delivered, canceled, shipped,
    invoiced, processing, unavailable, created, and approved.

    Important:
        In this file, we use 'total_order_value' instead of 'revenue'
        because revenue in this project is defined as completed sales
        from delivered orders only.
    """
    query = """
        WITH order_item_totals AS (
            SELECT
                order_id,
                COUNT(order_item_id) AS total_items,
                ROUND(SUM(price), 2) AS order_value,
                ROUND(SUM(freight_value), 2) AS freight_value
            FROM order_items
            GROUP BY order_id
        ),

        status_summary AS (
            SELECT
                o.order_status,
                COUNT(DISTINCT o.order_id) AS total_orders,
                SUM(COALESCE(oit.total_items, 0)) AS total_order_items,
                ROUND(SUM(COALESCE(oit.order_value, 0)), 2) AS total_order_value,
                ROUND(SUM(COALESCE(oit.freight_value, 0)), 2) AS total_freight_value
            FROM orders AS o
            LEFT JOIN order_item_totals AS oit
                ON o.order_id = oit.order_id
            GROUP BY o.order_status
        ),

        grand_total AS (
            SELECT
                SUM(total_orders) AS all_orders
            FROM status_summary
        )

        SELECT
            ss.order_status,
            ss.total_orders,

            ROUND(
                100.0 * ss.total_orders / gt.all_orders,
                2
            ) AS orders_percentage,

            ss.total_order_items,
            ss.total_order_value,
            ss.total_freight_value,

            ROUND(
                ss.total_order_value / NULLIF(ss.total_orders, 0),
                2
            ) AS average_order_value

        FROM status_summary AS ss
        CROSS JOIN grand_total AS gt
        ORDER BY ss.total_orders DESC;
    """

    with get_connection() as connection:
        dataframe = pd.read_sql_query(query, connection)

    return dataframe


def main():
    order_status_analysis = get_order_status_analysis()

    output_path = export_dataframe(
        order_status_analysis,
        "order_status_analysis.csv"
    )

    print("[OK] Order status analysis completed.")
    print(f"[OK] Results exported to: {output_path}")

    print()
    print("Order Status Analysis:")
    print(order_status_analysis.to_string(index=False))


if __name__ == "__main__":
    main()