import pandas as pd

from src.utils.db_connection import get_connection
from src.utils.export_results import export_dataframe


def get_monthly_sales_trend():
    """
    Analyze monthly sales trend for delivered orders only.

    Date used:
        order_purchase_timestamp

    Revenue definition:
        Revenue = SUM(order_items.price)

    Why delivered orders only?
        Because delivered orders represent completed sales.
        Canceled or unavailable orders are not counted as final revenue.
    """
    query = """
        SELECT
            date(o.order_purchase_timestamp, 'start of month') AS month_start_date,
            strftime('%Y-%m', o.order_purchase_timestamp) AS order_month,
            CAST(strftime('%Y', o.order_purchase_timestamp) AS INTEGER) AS order_year,
            CAST(strftime('%m', o.order_purchase_timestamp) AS INTEGER) AS month_number,

            ROUND(SUM(oi.price), 2) AS total_revenue,
            COUNT(DISTINCT o.order_id) AS total_orders,
            COUNT(DISTINCT c.customer_unique_id) AS total_customers,
            COUNT(oi.order_item_id) AS total_order_items,

            ROUND(
                SUM(oi.price) / COUNT(DISTINCT o.order_id),
                2
            ) AS average_order_value,

            ROUND(SUM(oi.freight_value), 2) AS total_freight

        FROM orders AS o
        INNER JOIN order_items AS oi
            ON o.order_id = oi.order_id
        INNER JOIN customers AS c
            ON o.customer_id = c.customer_id

        WHERE
            o.order_status = 'delivered'
            AND o.order_purchase_timestamp IS NOT NULL

        GROUP BY
            date(o.order_purchase_timestamp, 'start of month'),
            strftime('%Y-%m', o.order_purchase_timestamp),
            strftime('%Y', o.order_purchase_timestamp),
            strftime('%m', o.order_purchase_timestamp)

        ORDER BY
            month_start_date;
    """

    with get_connection() as connection:
        dataframe = pd.read_sql_query(query, connection)

    return dataframe


def main():
    monthly_sales = get_monthly_sales_trend()

    output_path = export_dataframe(
        monthly_sales,
        "monthly_sales_trend.csv"
    )

    print("[OK] Monthly sales trend analysis completed.")
    print(f"[OK] Results exported to: {output_path}")

    print()
    print("Monthly Sales Trend:")
    print(monthly_sales.to_string(index=False))


if __name__ == "__main__":
    main()