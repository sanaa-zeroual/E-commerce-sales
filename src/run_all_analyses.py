import importlib
import time


ANALYSIS_MODULES = [
    {
        "number": "01",
        "name": "Total Revenue",
        "module": "src.analysis.01_total_revenue",
    },
    {
        "number": "02",
        "name": "Total Orders",
        "module": "src.analysis.02_total_orders",
    },
    {
        "number": "03",
        "name": "Average Order Value",
        "module": "src.analysis.03_average_order_value",
    },
    {
        "number": "04",
        "name": "Top States and Cities Sales",
        "module": "src.analysis.04_top_states_cities_sales",
    },
    {
        "number": "05",
        "name": "Monthly Sales Trend",
        "module": "src.analysis.05_monthly_sales_trend",
    },
    {
        "number": "06",
        "name": "Order Status Analysis",
        "module": "src.analysis.06_order_status_analysis",
    },
    {
        "number": "07",
        "name": "Delivery Time Analysis",
        "module": "src.analysis.07_delivery_time_analysis",
    },
    {
        "number": "08",
        "name": "Late Orders Analysis",
        "module": "src.analysis.08_late_orders_analysis",
    },
    {
        "number": "09",
        "name": "Freight Analysis",
        "module": "src.analysis.09_freight_analysis",
    },
    {
        "number": "10",
        "name": "Geographic Sales Performance",
        "module": "src.analysis.10_geographic_sales_performance",
    },
]


def run_analysis(analysis):
    """
    Import one analysis module and execute its main() function.
    """
    print("=" * 80)
    print(f"[START] {analysis['number']} - {analysis['name']}")
    print("=" * 80)

    module = importlib.import_module(analysis["module"])

    if not hasattr(module, "main"):
        raise AttributeError(
            f"The module {analysis['module']} does not contain a main() function."
        )

    start_time = time.time()
    module.main()
    end_time = time.time()

    duration = round(end_time - start_time, 2)

    print()
    print(f"[DONE] {analysis['number']} - {analysis['name']}")
    print(f"[TIME] {duration} seconds")
    print()


def main():
    """
    Run all analysis scripts in order.

    Important:
        This file does not create or reload the SQLite database.
        Run the database pipeline first if needed:

            python -m src.database.load_csv_to_sqlite
            python -m src.database.check_database
    """
    print("Running all ecommerce analysis scripts...")
    print()

    total_start_time = time.time()

    for analysis in ANALYSIS_MODULES:
        run_analysis(analysis)

    total_end_time = time.time()
    total_duration = round(total_end_time - total_start_time, 2)

    print("=" * 80)
    print("[OK] All analyses completed successfully.")
    print(f"[TOTAL TIME] {total_duration} seconds")
    print("=" * 80)


if __name__ == "__main__":
    main()