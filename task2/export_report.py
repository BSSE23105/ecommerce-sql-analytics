import os

import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

here = os.path.dirname(os.path.abspath(__file__))
out_dir = os.path.join(here, "output")
os.makedirs(out_dir, exist_ok=True)
load_dotenv(os.path.join(here, ".env"))


def connect_db():
    user = os.getenv("DB_USER")
    pw = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME")
    return create_engine(f"postgresql+psycopg2://{user}:{pw}@{host}:{port}/{name}")


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
    db = connect_db()

    revenue = pd.read_sql(revenue_sql, db)
    top_customers = pd.read_sql(top_customers_sql, db)
    by_status = pd.read_sql(status_sql, db)
    mom = pd.read_sql(mom_sql, db)

    report_path = os.path.join(out_dir, "weekly_sales_report.csv")

    # put all four results in one file, each under its own title line
    sections = [("Total Revenue per Category", revenue),
                ("Top 5 Customers by Spend", top_customers),
                ("Orders Count by Status", by_status),
                ("Month-over-Month Revenue Change", mom)]

    with open(report_path, "w", newline="", encoding="utf-8") as f:
        for title, table in sections:
            f.write(f"# {title}\n")
            table.to_csv(f, index=False)
            f.write("\n")

    print("Report saved to", report_path)


if __name__ == "__main__":
    main()
