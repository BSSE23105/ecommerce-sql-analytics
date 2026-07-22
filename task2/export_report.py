import os
import sys
import logging

import pandas as pd

# the shared connection helper sits in utils/ at the project root, so put the root on the import path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.db_connection import connect_db

here = os.path.dirname(os.path.abspath(__file__))
out_dir = os.path.join(here, "output")
os.makedirs(out_dir, exist_ok=True)


revenue_sql = """
SELECT p.category,
       SUM(o.quantity * p.price) AS total_revenue
FROM orders o
JOIN products p ON o.product_id = p.product_id
WHERE o.status = 'completed'
GROUP BY p.category
ORDER BY total_revenue DESC;
"""

top_customers_sql = """
SELECT c.customer_id,
       c.full_name,
       c.city,
       SUM(o.quantity * p.price) AS total_spend
FROM customers c
JOIN orders o   ON c.customer_id = o.customer_id
JOIN products p ON o.product_id  = p.product_id
WHERE o.status = 'completed'
GROUP BY c.customer_id, c.full_name, c.city
ORDER BY total_spend DESC
LIMIT 5;
"""

status_sql = """
SELECT status,
       COUNT(*) AS orders_count
FROM orders
GROUP BY status
ORDER BY orders_count DESC;
"""

# month totals plus each month compared to the one before it (LAG)
mom_sql = """
WITH monthly AS (
    SELECT DATE_TRUNC('month', o.order_date) AS month,
           SUM(o.quantity * p.price)         AS revenue
    FROM orders o
    JOIN products p ON o.product_id = p.product_id
    WHERE o.status = 'completed'
    GROUP BY DATE_TRUNC('month', o.order_date)
)
SELECT TO_CHAR(month, 'YYYY-MM')                       AS month,
       revenue,
       LAG(revenue) OVER (ORDER BY month)              AS prev_month_revenue,
       revenue - LAG(revenue) OVER (ORDER BY month)    AS mom_change,
       ROUND(
           (revenue - LAG(revenue) OVER (ORDER BY month)) * 100.0
           / NULLIF(LAG(revenue) OVER (ORDER BY month), 0), 2
       )                                               AS mom_change_pct
FROM monthly
ORDER BY month;
"""


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    db = connect_db()

    # run the four summary queries against the loaded data
    logging.info("Running the report queries...")
    revenue = pd.read_sql(revenue_sql, db)
    top_customers = pd.read_sql(top_customers_sql, db)
    by_status = pd.read_sql(status_sql, db)
    mom = pd.read_sql(mom_sql, db)

    # write each result to its own worksheet so every table keeps its own headers
    report_path = os.path.join(out_dir, "weekly_sales_report.xlsx")
    sheets = [("Revenue by Category", revenue),
              ("Top Customers", top_customers),
              ("Orders by Status", by_status),
              ("MoM Revenue", mom)]

    with pd.ExcelWriter(report_path, engine="openpyxl") as xl:
        for sheet_name, table in sheets:
            table.to_excel(xl, sheet_name=sheet_name, index=False)

    logging.info("Report saved to %s", report_path)


if __name__ == "__main__":
    main()
