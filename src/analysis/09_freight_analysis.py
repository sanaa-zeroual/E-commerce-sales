import pandas as pd

from src.utils.db_connection import get_connection
from src.utils.export_results import export_dataframe


OUTPUT_COLUMNS = [
    "analysis_scope",
    "analysis_level",
    "rank_by_total_freight",
    "state",
    "total_orders",
    "total_order_items",
    "total_revenue",
    "total_freight",
    "freight_share_of_total_percent",
    "average_freight_per_order",
    "average_freight_per_item",
    "average_order_value",
    "freight_to_revenue_percent",
]


def get_order_level_freight_data():
    """
    Get freight and revenue data at order level.

    Why order level?
        Because one order can contain multiple items.
        If we calculate average freight directly from order_items,
        we will get average freight per item, not average freight per order.

    Scope:
        Delivered orders only.

    Revenue definition:
        Revenue = SUM(order_items.price)

    Freight definition:
        Freight = SUM(order_items.freight_value)
    """
    query = """
        SELECT
            o.order_id,
            c.customer_state AS state,
            COUNT(oi.order_item_id) AS total_order_items,
            ROUND(SUM(oi.price), 2) AS order_revenue,
            ROUND(SUM(oi.freight_value), 2) AS order_freight
        FROM orders AS o
        INNER JOIN order_items AS oi
            ON o.order_id = oi.order_id
        INNER JOIN customers AS c
            ON o.customer_id = c.customer_id
        WHERE o.order_status = 'delivered'
        GROUP BY
            o.order_id,
            c.customer_state;
    """

    with get_connection() as connection:
        dataframe = pd.read_sql_query(query, connection)

    return dataframe


def safe_divide(numerator, denominator):
    """Safely divide two values and return 0 when denominator is zero."""
    if denominator == 0:
        return 0

    return numerator / denominator


def build_overall_freight_summary(order_level_data):
    """
    Build the overall freight summary row.

    This row represents all delivered orders across all states.
    """
    total_orders = order_level_data["order_id"].nunique()
    total_order_items = order_level_data["total_order_items"].sum()
    total_revenue = order_level_data["order_revenue"].sum()
    total_freight = order_level_data["order_freight"].sum()

    overall_summary = pd.DataFrame(
        [
            {
                "analysis_scope": "delivered_orders_only",
                "analysis_level": "overall",
                "rank_by_total_freight": 0,
                "state": "ALL_STATES",
                "total_orders": total_orders,
                "total_order_items": total_order_items,
                "total_revenue": round(total_revenue, 2),
                "total_freight": round(total_freight, 2),
                "freight_share_of_total_percent": 100.00,
                "average_freight_per_order": round(
                    safe_divide(total_freight, total_orders),
                    2
                ),
                "average_freight_per_item": round(
                    safe_divide(total_freight, total_order_items),
                    2
                ),
                "average_order_value": round(
                    safe_divide(total_revenue, total_orders),
                    2
                ),
                "freight_to_revenue_percent": round(
                    100.0 * safe_divide(total_freight, total_revenue),
                    2
                ),
            }
        ]
    )

    return overall_summary


def build_state_freight_summary(order_level_data):
    """
    Build freight summary by customer state.

    The output helps us understand which states generate the highest
    freight cost and where freight represents a large share of revenue.
    """
    total_freight_all_states = order_level_data["order_freight"].sum()

    state_summary = (
        order_level_data
        .groupby("state", as_index=False)
        .agg(
            total_orders=("order_id", "nunique"),
            total_order_items=("total_order_items", "sum"),
            total_revenue=("order_revenue", "sum"),
            total_freight=("order_freight", "sum"),
        )
    )

    state_summary["analysis_scope"] = "delivered_orders_only"
    state_summary["analysis_level"] = "state"

    state_summary["freight_share_of_total_percent"] = (
        100.0
        * state_summary["total_freight"]
        / total_freight_all_states
    )

    state_summary["average_freight_per_order"] = (
        state_summary["total_freight"]
        / state_summary["total_orders"]
    )

    state_summary["average_freight_per_item"] = (
        state_summary["total_freight"]
        / state_summary["total_order_items"]
    )

    state_summary["average_order_value"] = (
        state_summary["total_revenue"]
        / state_summary["total_orders"]
    )

    state_summary["freight_to_revenue_percent"] = (
        100.0
        * state_summary["total_freight"]
        / state_summary["total_revenue"]
    )

    state_summary = state_summary.sort_values(
        "total_freight",
        ascending=False
    ).reset_index(drop=True)

    state_summary["rank_by_total_freight"] = state_summary.index + 1

    numeric_columns = [
        "total_revenue",
        "total_freight",
        "freight_share_of_total_percent",
        "average_freight_per_order",
        "average_freight_per_item",
        "average_order_value",
        "freight_to_revenue_percent",
    ]

    for column in numeric_columns:
        state_summary[column] = state_summary[column].round(2)

    state_summary = state_summary[OUTPUT_COLUMNS]

    return state_summary


def build_freight_analysis(order_level_data):
    """
    Build the final freight analysis table.

    The final output contains:
        1. One overall row for all delivered orders.
        2. State-level rows sorted by total freight cost.
    """
    if order_level_data.empty:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    overall_summary = build_overall_freight_summary(order_level_data)
    state_summary = build_state_freight_summary(order_level_data)

    freight_analysis = pd.concat(
        [overall_summary, state_summary],
        ignore_index=True
    )

    freight_analysis = freight_analysis[OUTPUT_COLUMNS]

    return freight_analysis


def main():
    order_level_data = get_order_level_freight_data()
    freight_analysis = build_freight_analysis(order_level_data)

    output_path = export_dataframe(
        freight_analysis,
        "freight_analysis.csv"
    )

    print("[OK] Freight analysis completed.")
    print(f"[OK] Results exported to: {output_path}")

    print()
    print("Overall Freight Analysis:")
    print(
        freight_analysis[
            freight_analysis["analysis_level"] == "overall"
        ].to_string(index=False)
    )

    print()
    print("Top 10 States by Freight Cost:")
    print(
        freight_analysis[
            freight_analysis["analysis_level"] == "state"
        ].head(10).to_string(index=False)
    )


if __name__ == "__main__":
    main()