import os
import sys
import json
import logging

import pandas as pd
import matplotlib
matplotlib.use("Agg")  # save straight to a file, don't try to pop a window open
import matplotlib.pyplot as plt
from sqlalchemy import text

# the shared connection helper sits in utils/ at the project root, so put the root on the import path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.db_connection import connect_db

here = os.path.dirname(os.path.abspath(__file__))
out_dir = os.path.join(here, "output")
os.makedirs(out_dir, exist_ok=True)

# every query below reads a view, never a fact or dim table - that's the whole point of the analytics layer
monthly_sql = text("""
    SELECT month, total_revenue, order_count, avg_order_value
    FROM warehouse.vw_monthly_revenue
""")

category_sql = text("""
    SELECT category, total_revenue, units_sold, avg_price
    FROM warehouse.vw_category_performance
""")

customer_sql = text("""
    SELECT customer_id, full_name, city, order_count, total_spend, days_since_last_order
    FROM warehouse.vw_customer_summary
""")

repeat_sql = text("""
    SELECT customer_id, order_count, total_spend, repeat_purchase_rate_pct
    FROM warehouse.vw_repeat_customers
""")


def apply_views(db):
    # run views.sql so the analytics layer exists before we query it (safe to repeat)
    with open(os.path.join(here, "views.sql"), "r", encoding="utf-8") as f:
        ddl = f.read()
    with db.begin() as conn:
        conn.exec_driver_sql(ddl)


def chart_monthly_revenue(monthly):
    # a line chart, because months are a sequence and we care about the shape of the trend
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(monthly["month"], monthly["total_revenue"], marker="o", color="steelblue")
    ax.set_title("Monthly Revenue Trend (completed orders)")
    ax.set_xlabel("Month")
    ax.set_ylabel("Revenue")
    ax.grid(axis="y", alpha=0.3)
    fig.autofmt_xdate(rotation=45)
    fig.tight_layout()

    path = os.path.join(out_dir, "monthly_revenue.png")
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path


def chart_category_revenue(categories):
    # vertical bars: only a handful of categories and we're comparing them against each other
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(categories["category"], categories["total_revenue"], color="teal")
    ax.set_title("Revenue by Category")
    ax.set_xlabel("Category")
    ax.set_ylabel("Revenue")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()

    path = os.path.join(out_dir, "category_revenue.png")
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path


def chart_top_customers(customers):
    # horizontal bars so the long customer names stay readable
    top = customers.nlargest(10, "total_spend").iloc[::-1]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(top["full_name"], top["total_spend"], color="chocolate")
    ax.set_title("Top 10 Customers by Spend")
    ax.set_xlabel("Total spend")
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()

    path = os.path.join(out_dir, "top_customers.png")
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path


def build_stats(monthly, categories, customers, repeats):
    # the repeat rate is the same value on every row of the view, so read it once (0 if nobody repeated)
    repeat_rate = float(repeats["repeat_purchase_rate_pct"].iloc[0]) if not repeats.empty else 0.0

    return {
        "total_revenue": round(float(monthly["total_revenue"].sum()), 2),
        "total_customers": len(customers),
        "total_orders": int(monthly["order_count"].sum()),
        "best_category": categories.loc[categories["total_revenue"].idxmax(), "category"],
        "repeat_customer_rate_pct": repeat_rate,
    }


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    # matplotlib chats a lot at INFO level, we only want to hear from it when something is wrong
    logging.getLogger("matplotlib").setLevel(logging.WARNING)

    db = connect_db()
    apply_views(db)

    logging.info("Querying the analytics views...")
    with db.connect() as conn:
        monthly = pd.read_sql(monthly_sql, conn)
        categories = pd.read_sql(category_sql, conn)
        customers = pd.read_sql(customer_sql, conn)
        repeats = pd.read_sql(repeat_sql, conn)

    if monthly.empty:
        logging.error("The views returned nothing. Load the warehouse first (task3/load_warehouse.py).")
        sys.exit(1)

    charts = [chart_monthly_revenue(monthly),
              chart_category_revenue(categories),
              chart_top_customers(customers)]
    for path in charts:
        logging.info("Chart saved to %s", path)

    stats = build_stats(monthly, categories, customers, repeats)
    stats_path = os.path.join(out_dir, "summary_stats.json")
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    logging.info("Summary stats saved to %s", stats_path)
    logging.info("revenue=%s  customers=%s  orders=%s  best_category=%s  repeat_rate=%s%%",
                 stats["total_revenue"], stats["total_customers"], stats["total_orders"],
                 stats["best_category"], stats["repeat_customer_rate_pct"])


if __name__ == "__main__":
    main()
