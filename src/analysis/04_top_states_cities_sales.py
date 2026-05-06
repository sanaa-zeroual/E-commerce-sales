import pandas as pd

from src.utils.db_connection import get_connection
from src.utils.export_results import export_dataframe


def get_top_states_by_sales(limit=10):
    """
    Get the top states by revenue for delivered orders only.

    Revenue definition:
        Revenue = SUM(order_items.price)

    The result is sorted from highest revenue to lowest revenue.
    """
    query = f"""
        SELECT
            c.customer_state AS state,
            ROUND(SUM(oi.price), 2) AS total_revenue,
            COUNT(DISTINCT o.order_id) AS total_orders,
            COUNT(DISTINCT c.customer_unique_id) AS total_customers,
            COUNT(oi.order_item_id) AS total_order_items,
            ROUND(
                SUM(oi.price) / COUNT(DISTINCT o.order_id),
                2
            ) AS average_order_value
        FROM order_items AS oi
        INNER JOIN orders AS o
            ON oi.order_id = o.order_id
        INNER JOIN customers AS c
            ON o.customer_id = c.customer_id
        WHERE o.order_status = 'delivered'
        GROUP BY c.customer_state
        ORDER BY total_revenue DESC
        LIMIT {limit};
    """

    with get_connection() as connection:
        dataframe = pd.read_sql_query(query, connection)

    return dataframe


def get_top_cities_by_sales(limit=10):
    """
    Get the top cities by revenue for delivered orders only.

    We group by both city and state because different states may contain
    cities with the same name.
    """
    query = f"""
        SELECT
            c.customer_city AS city,
            c.customer_state AS state,
            ROUND(SUM(oi.price), 2) AS total_revenue,
            COUNT(DISTINCT o.order_id) AS total_orders,
            COUNT(DISTINCT c.customer_unique_id) AS total_customers,
            COUNT(oi.order_item_id) AS total_order_items,
            ROUND(
                SUM(oi.price) / COUNT(DISTINCT o.order_id),
                2
            ) AS average_order_value
        FROM order_items AS oi
        INNER JOIN orders AS o
            ON oi.order_id = o.order_id
        INNER JOIN customers AS c
            ON o.customer_id = c.customer_id
        WHERE o.order_status = 'delivered'
        GROUP BY
            c.customer_city,
            c.customer_state
        ORDER BY total_revenue DESC
        LIMIT {limit};
    """

    with get_connection() as connection:
        dataframe = pd.read_sql_query(query, connection)

    return dataframe


def main():
    top_states = get_top_states_by_sales(limit=10)
    top_cities = get_top_cities_by_sales(limit=10)

    states_output_path = export_dataframe(
        top_states,
        "top_states_sales.csv"
    )

    cities_output_path = export_dataframe(
        top_cities,
        "top_cities_sales.csv"
    )

    print("[OK] Top states and cities sales analysis completed.")
    print(f"[OK] States results exported to: {states_output_path}")
    print(f"[OK] Cities results exported to: {cities_output_path}")

    print()
    print("Top 10 States by Revenue:")
    print(top_states.to_string(index=False))

    print()
    print("Top 10 Cities by Revenue:")
    print(top_cities.to_string(index=False))


if __name__ == "__main__":
    main()