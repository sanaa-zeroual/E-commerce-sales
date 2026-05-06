import pandas as pd

from src.utils.db_connection import get_connection
from src.utils.export_results import export_dataframe


def get_geographic_sales_performance():
    """
    Analyze sales performance by customer state and city.

    Scope:
        Delivered orders only.

    Metrics:
        - Total revenue
        - Total orders
        - Total customers
        - Total order items
        - Average order value
        - Total freight
        - Average freight per order
        - Average delivery days
        - Late orders
        - Late delivery rate

    This file creates a geographic performance table that will be useful
    later in Power BI for maps, state ranking, and city ranking visuals.
    """
    query = """
        WITH order_level_data AS (
            SELECT
                o.order_id,
                c.customer_unique_id,
                c.customer_state AS state,
                c.customer_city AS city,

                ROUND(SUM(oi.price), 2) AS order_revenue,
                ROUND(SUM(oi.freight_value), 2) AS order_freight,
                COUNT(oi.order_item_id) AS total_order_items,

                ROUND(
                    julianday(o.order_delivered_customer_date)
                    - julianday(o.order_purchase_timestamp),
                    2
                ) AS delivery_days,

                CASE
                    WHEN date(o.order_delivered_customer_date)
                        > date(o.order_estimated_delivery_date)
                    THEN 1
                    ELSE 0
                END AS is_late

            FROM orders AS o
            INNER JOIN order_items AS oi
                ON o.order_id = oi.order_id
            INNER JOIN customers AS c
                ON o.customer_id = c.customer_id

            WHERE
                o.order_status = 'delivered'
                AND o.order_purchase_timestamp IS NOT NULL
                AND o.order_delivered_customer_date IS NOT NULL
                AND o.order_estimated_delivery_date IS NOT NULL
                AND julianday(o.order_delivered_customer_date)
                    >= julianday(o.order_purchase_timestamp)

            GROUP BY
                o.order_id,
                c.customer_unique_id,
                c.customer_state,
                c.customer_city,
                o.order_purchase_timestamp,
                o.order_delivered_customer_date,
                o.order_estimated_delivery_date
        )

        SELECT
            state,
            city,

            COUNT(DISTINCT order_id) AS total_orders,
            COUNT(DISTINCT customer_unique_id) AS total_customers,
            SUM(total_order_items) AS total_order_items,

            ROUND(SUM(order_revenue), 2) AS total_revenue,
            ROUND(SUM(order_freight), 2) AS total_freight,

            ROUND(
                SUM(order_revenue) / COUNT(DISTINCT order_id),
                2
            ) AS average_order_value,

            ROUND(
                SUM(order_freight) / COUNT(DISTINCT order_id),
                2
            ) AS average_freight_per_order,

            ROUND(
                AVG(delivery_days),
                2
            ) AS average_delivery_days,

            SUM(is_late) AS late_orders,

            ROUND(
                100.0 * SUM(is_late) / COUNT(DISTINCT order_id),
                2
            ) AS late_delivery_rate_percent

        FROM order_level_data

        GROUP BY
            state,
            city

        ORDER BY
            total_revenue DESC;
    """

    with get_connection() as connection:
        dataframe = pd.read_sql_query(query, connection)

    return dataframe


def main():
    geographic_sales = get_geographic_sales_performance()

    output_path = export_dataframe(
        geographic_sales,
        "geographic_sales_performance.csv"
    )

    print("[OK] Geographic sales performance analysis completed.")
    print(f"[OK] Results exported to: {output_path}")

    print()
    print("Top 20 Geographic Sales Performance Rows:")
    print(geographic_sales.head(20).to_string(index=False))

    print()
    print(f"Total rows exported: {len(geographic_sales):,}")


if __name__ == "__main__":
    main()