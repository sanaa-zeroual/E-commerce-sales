import pandas as pd

from src.utils.db_connection import get_connection
from src.utils.export_results import export_dataframe


SUMMARY_COLUMNS = [
    "analysis_scope",
    "section",
    "bucket_order",
    "delivery_status",
    "total_orders",
    "percent_of_all_valid_delivered_orders",
    "percent_of_late_orders",
    "average_days_vs_estimated",
    "median_days_vs_estimated",
    "min_days_vs_estimated",
    "max_days_vs_estimated",
]


def get_delivery_comparison_data():
    """
    Get delivered orders with valid actual and estimated delivery dates.

    Days vs estimated definition:
        days_vs_estimated =
            date(order_delivered_customer_date)
            -
            date(order_estimated_delivery_date)

    Interpretation:
        days_vs_estimated <= 0  -> On time or early
        days_vs_estimated > 0   -> Late

    We compare dates instead of full timestamps because the estimated
    delivery value represents a delivery day, not an exact hour.
    """
    query = """
        SELECT
            o.order_id,
            date(o.order_purchase_timestamp) AS purchase_date,
            date(o.order_delivered_customer_date) AS delivered_date,
            date(o.order_estimated_delivery_date) AS estimated_delivery_date,

            ROUND(
                julianday(date(o.order_delivered_customer_date))
                - julianday(date(o.order_estimated_delivery_date)),
                0
            ) AS days_vs_estimated

        FROM orders AS o

        WHERE
            o.order_status = 'delivered'
            AND o.order_purchase_timestamp IS NOT NULL
            AND o.order_delivered_customer_date IS NOT NULL
            AND o.order_estimated_delivery_date IS NOT NULL
            AND julianday(o.order_delivered_customer_date)
                >= julianday(o.order_purchase_timestamp);
    """

    with get_connection() as connection:
        dataframe = pd.read_sql_query(query, connection)

    return dataframe


def round_or_none(value):
    """Round numeric values and keep missing values as None."""
    if pd.isna(value):
        return None

    return round(float(value), 2)


def create_summary_row(
    data,
    analysis_scope,
    section,
    bucket_order,
    delivery_status,
    total_valid_orders,
    total_late_orders,
    calculate_late_percentage=False,
):
    """
    Create one summary row for a group of orders.

    Percent of all valid delivered orders:
        group orders / all delivered orders with valid delivery dates

    Percent of late orders:
        group orders / all late orders
        This is only used for late delay buckets.
    """
    total_orders = data["order_id"].nunique()

    if total_valid_orders == 0:
        percent_of_all_orders = None
    else:
        percent_of_all_orders = round(
            100.0 * total_orders / total_valid_orders,
            2
        )

    if calculate_late_percentage and total_late_orders > 0:
        percent_of_late_orders = round(
            100.0 * total_orders / total_late_orders,
            2
        )
    else:
        percent_of_late_orders = None

    return {
        "analysis_scope": analysis_scope,
        "section": section,
        "bucket_order": bucket_order,
        "delivery_status": delivery_status,
        "total_orders": total_orders,
        "percent_of_all_valid_delivered_orders": percent_of_all_orders,
        "percent_of_late_orders": percent_of_late_orders,
        "average_days_vs_estimated": round_or_none(
            data["days_vs_estimated"].mean()
        ),
        "median_days_vs_estimated": round_or_none(
            data["days_vs_estimated"].median()
        ),
        "min_days_vs_estimated": round_or_none(
            data["days_vs_estimated"].min()
        ),
        "max_days_vs_estimated": round_or_none(
            data["days_vs_estimated"].max()
        ),
    }


def build_late_orders_summary(delivery_comparison):
    """
    Build the late orders analysis summary.

    The output contains:
        1. Overall summary row.
        2. On time or early vs Late rows.
        3. Late delay bucket rows.

    Late bucket definitions:
        1-7 days late
        8-14 days late
        15-30 days late
        31+ days late
    """
    if delivery_comparison.empty:
        return pd.DataFrame(columns=SUMMARY_COLUMNS)

    analysis_scope = "delivered_orders_with_valid_actual_and_estimated_dates"

    delivery_comparison = delivery_comparison.copy()
    delivery_comparison["days_vs_estimated"] = pd.to_numeric(
        delivery_comparison["days_vs_estimated"],
        errors="coerce"
    )

    delivery_comparison = delivery_comparison.dropna(
        subset=["days_vs_estimated"]
    )

    delivery_comparison["delivery_status"] = delivery_comparison[
        "days_vs_estimated"
    ].apply(
        lambda value: "Late" if value > 0 else "On time or early"
    )

    total_valid_orders = delivery_comparison["order_id"].nunique()

    late_data = delivery_comparison[
        delivery_comparison["days_vs_estimated"] > 0
    ].copy()

    total_late_orders = late_data["order_id"].nunique()

    summary_rows = []

    summary_rows.append(
        create_summary_row(
            data=delivery_comparison,
            analysis_scope=analysis_scope,
            section="overall",
            bucket_order=0,
            delivery_status="All delivered orders",
            total_valid_orders=total_valid_orders,
            total_late_orders=total_late_orders,
        )
    )

    for status, bucket_order in [
        ("On time or early", 1),
        ("Late", 2),
    ]:
        status_data = delivery_comparison[
            delivery_comparison["delivery_status"] == status
        ]

        summary_rows.append(
            create_summary_row(
                data=status_data,
                analysis_scope=analysis_scope,
                section="delivery_punctuality",
                bucket_order=bucket_order,
                delivery_status=status,
                total_valid_orders=total_valid_orders,
                total_late_orders=total_late_orders,
            )
        )

    if not late_data.empty:
        bucket_labels = [
            "1-7 days late",
            "8-14 days late",
            "15-30 days late",
            "31+ days late",
        ]

        late_data["delivery_status"] = pd.cut(
            late_data["days_vs_estimated"],
            bins=[0, 7, 14, 30, float("inf")],
            labels=bucket_labels,
            include_lowest=True,
        )

        bucket_order_map = {
            "1-7 days late": 3,
            "8-14 days late": 4,
            "15-30 days late": 5,
            "31+ days late": 6,
        }

        for bucket_label in bucket_labels:
            bucket_data = late_data[
                late_data["delivery_status"].astype(str) == bucket_label
            ]

            summary_rows.append(
                create_summary_row(
                    data=bucket_data,
                    analysis_scope=analysis_scope,
                    section="late_delay_bucket",
                    bucket_order=bucket_order_map[bucket_label],
                    delivery_status=bucket_label,
                    total_valid_orders=total_valid_orders,
                    total_late_orders=total_late_orders,
                    calculate_late_percentage=True,
                )
            )

    late_orders_summary = pd.DataFrame(summary_rows)
    late_orders_summary = late_orders_summary[SUMMARY_COLUMNS]
    late_orders_summary = late_orders_summary.sort_values("bucket_order")

    return late_orders_summary


def main():
    delivery_comparison = get_delivery_comparison_data()
    late_orders_summary = build_late_orders_summary(delivery_comparison)

    output_path = export_dataframe(
        late_orders_summary,
        "late_orders_analysis.csv"
    )

    print("[OK] Late orders analysis completed.")
    print(f"[OK] Results exported to: {output_path}")

    print()
    print("Late Orders Analysis:")
    print(late_orders_summary.to_string(index=False))


if __name__ == "__main__":
    main()