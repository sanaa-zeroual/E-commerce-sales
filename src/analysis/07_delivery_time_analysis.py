import pandas as pd

from src.utils.db_connection import get_connection
from src.utils.export_results import export_dataframe


SUMMARY_COLUMNS = [
    "analysis_scope",
    "bucket_order",
    "delivery_time_group",
    "total_orders",
    "orders_percentage",
    "average_delivery_days",
    "median_delivery_days",
    "min_delivery_days",
    "max_delivery_days",
]


def get_delivery_time_data():
    """
    Get actual delivery time for delivered orders only.

    Delivery time definition:
        delivery_days = order_delivered_customer_date - order_purchase_timestamp

    We only keep orders where both dates exist and where delivery_days
    is greater than or equal to zero.
    """
    query = """
        SELECT
            o.order_id,
            ROUND(
                julianday(o.order_delivered_customer_date)
                - julianday(o.order_purchase_timestamp),
                2
            ) AS delivery_days
        FROM orders AS o
        WHERE
            o.order_status = 'delivered'
            AND o.order_purchase_timestamp IS NOT NULL
            AND o.order_delivered_customer_date IS NOT NULL
            AND julianday(o.order_delivered_customer_date)
                >= julianday(o.order_purchase_timestamp);
    """

    with get_connection() as connection:
        dataframe = pd.read_sql_query(query, connection)

    return dataframe


def build_delivery_time_summary(delivery_times):
    """
    Build a delivery time summary table.

    The result contains:
        1. An overall summary row.
        2. Delivery time bucket rows.

    Bucket definitions:
        0-7 days
        8-14 days
        15-30 days
        31+ days
    """
    if delivery_times.empty:
        return pd.DataFrame(columns=SUMMARY_COLUMNS)

    total_orders = delivery_times["order_id"].nunique()

    analysis_scope = "delivered_orders_with_valid_delivery_dates"

    overall_summary = pd.DataFrame(
        [
            {
                "analysis_scope": analysis_scope,
                "bucket_order": 0,
                "delivery_time_group": "All delivered orders",
                "total_orders": total_orders,
                "orders_percentage": 100.00,
                "average_delivery_days": round(delivery_times["delivery_days"].mean(), 2),
                "median_delivery_days": round(delivery_times["delivery_days"].median(), 2),
                "min_delivery_days": round(delivery_times["delivery_days"].min(), 2),
                "max_delivery_days": round(delivery_times["delivery_days"].max(), 2),
            }
        ]
    )

    bucketed_data = delivery_times.copy()

    bucket_labels = [
        "0-7 days",
        "8-14 days",
        "15-30 days",
        "31+ days",
    ]

    bucketed_data["delivery_time_group"] = pd.cut(
        bucketed_data["delivery_days"],
        bins=[-0.01, 7, 14, 30, float("inf")],
        labels=bucket_labels,
        include_lowest=True,
    )

    bucket_summary = (
        bucketed_data
        .groupby("delivery_time_group", observed=False)
        .agg(
            total_orders=("order_id", "nunique"),
            average_delivery_days=("delivery_days", "mean"),
            median_delivery_days=("delivery_days", "median"),
            min_delivery_days=("delivery_days", "min"),
            max_delivery_days=("delivery_days", "max"),
        )
        .reset_index()
    )

    bucket_summary["delivery_time_group"] = bucket_summary[
        "delivery_time_group"
    ].astype(str)

    bucket_order = {
        "0-7 days": 1,
        "8-14 days": 2,
        "15-30 days": 3,
        "31+ days": 4,
    }

    bucket_summary["analysis_scope"] = analysis_scope
    bucket_summary["bucket_order"] = bucket_summary["delivery_time_group"].map(
        bucket_order
    )

    bucket_summary["orders_percentage"] = (
        100.0 * bucket_summary["total_orders"] / total_orders
    ).round(2)

    numeric_columns = [
        "average_delivery_days",
        "median_delivery_days",
        "min_delivery_days",
        "max_delivery_days",
    ]

    for column in numeric_columns:
        bucket_summary[column] = bucket_summary[column].round(2)

    delivery_time_summary = pd.concat(
        [overall_summary, bucket_summary],
        ignore_index=True,
    )

    delivery_time_summary = delivery_time_summary[SUMMARY_COLUMNS]
    delivery_time_summary = delivery_time_summary.sort_values("bucket_order")

    return delivery_time_summary


def main():
    delivery_times = get_delivery_time_data()
    delivery_time_summary = build_delivery_time_summary(delivery_times)

    output_path = export_dataframe(
        delivery_time_summary,
        "delivery_time_analysis.csv"
    )

    print("[OK] Delivery time analysis completed.")
    print(f"[OK] Results exported to: {output_path}")

    print()
    print("Delivery Time Analysis:")
    print(delivery_time_summary.to_string(index=False))


if __name__ == "__main__":
    main()