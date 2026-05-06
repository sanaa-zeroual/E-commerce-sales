import pandas as pd

from src.utils.db_connection import get_connection
from src.utils.export_results import export_dataframe


def calculate_total_orders():
    """
    Calculate the main order count KPIs.

    This analysis focuses on the total number of orders and a few
    important status-based order counts.

    The detailed order status breakdown will be handled later in:
        06_order_status_analysis.py
    """
    query = """
        SELECT
            COUNT(DISTINCT order_id) AS total_orders,

            COUNT(
                DISTINCT CASE
                    WHEN order_status = 'delivered'
                    THEN order_id
                END
            ) AS delivered_orders,

            COUNT(
                DISTINCT CASE
                    WHEN order_status = 'canceled'
                    THEN order_id
                END
            ) AS canceled_orders,

            COUNT(
                DISTINCT CASE
                    WHEN order_status = 'shipped'
                    THEN order_id
                END
            ) AS shipped_orders,

            COUNT(
                DISTINCT CASE
                    WHEN order_status NOT IN ('delivered', 'canceled', 'shipped')
                    THEN order_id
                END
            ) AS other_orders,

            ROUND(
                100.0 * COUNT(
                    DISTINCT CASE
                        WHEN order_status = 'delivered'
                        THEN order_id
                    END
                ) / COUNT(DISTINCT order_id),
                2
            ) AS delivery_rate_percent,

            ROUND(
                100.0 * COUNT(
                    DISTINCT CASE
                        WHEN order_status = 'canceled'
                        THEN order_id
                    END
                ) / COUNT(DISTINCT order_id),
                2
            ) AS cancellation_rate_percent

        FROM orders;
    """

    with get_connection() as connection:
        dataframe = pd.read_sql_query(query, connection)

    return dataframe


def main():
    dataframe = calculate_total_orders()

    output_path = export_dataframe(
        dataframe,
        "total_orders.csv"
    )

    print("[OK] Total orders analysis completed.")
    print(f"[OK] Results exported to: {output_path}")
    print()
    print(dataframe.to_string(index=False))


if __name__ == "__main__":
    main()