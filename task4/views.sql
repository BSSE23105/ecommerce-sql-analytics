-- Task 4: the analytics layer. These views sit on top of the task 3 star schema so reports and
-- dashboards never have to touch fact_orders directly.

-- View1: Monthly Revenue and AOV (completed orders only)
-- AOV is just revenue / number of orders, which works here because the grain is one row per order.
CREATE OR REPLACE VIEW warehouse.vw_monthly_revenue AS
SELECT TO_CHAR(d.full_date, 'YYYY-MM') AS month,
       SUM(f.total_amount) AS total_revenue,
       COUNT(*) AS order_count,
       ROUND(AVG(f.total_amount), 2) AS avg_order_value
FROM warehouse.fact_orders f
JOIN warehouse.dim_date d ON f.date_key = d.date_key
WHERE f.status = 'completed'
GROUP BY TO_CHAR(d.full_date, 'YYYY-MM')
ORDER BY month;


-- View2: Category Performance
-- averages the unit_price stored on the order, not today's price in dim_products
CREATE OR REPLACE VIEW warehouse.vw_category_performance AS
SELECT p.category,
       SUM(f.total_amount) AS total_revenue,
       SUM(f.quantity) AS units_sold,
       ROUND(AVG(f.unit_price), 2) AS avg_price
FROM warehouse.fact_orders f
JOIN warehouse.dim_products p ON f.product_key = p.product_key
WHERE f.status = 'completed'
GROUP BY p.category
ORDER BY total_revenue DESC;


-- View3: Customer Summary
-- one row per customer with their whole ordering history summed up
CREATE OR REPLACE VIEW warehouse.vw_customer_summary AS
SELECT c.customer_id,
       c.full_name,
       c.city,
       COUNT(*) AS order_count,
       SUM(f.total_amount) AS total_spend,
       MIN(d.full_date) AS first_order_date,
       MAX(d.full_date) AS last_order_date,
       CURRENT_DATE - MAX(d.full_date) AS days_since_last_order
FROM warehouse.fact_orders f
JOIN warehouse.dim_customers c ON f.customer_key = c.customer_key
JOIN warehouse.dim_date d ON f.date_key = d.date_key
WHERE f.status = 'completed'
GROUP BY c.customer_id, c.full_name, c.city
ORDER BY total_spend DESC;


-- View4: Repeat Customers (2 or more orders)
-- the repeat rate is a whole-table number so it lands the same on every row. 100.0 keeps the
-- division numeric, otherwise integer division would turn 4/38 into 0.
CREATE OR REPLACE VIEW warehouse.vw_repeat_customers AS
SELECT s.customer_id,
       s.full_name,
       s.city,
       s.order_count,
       s.total_spend,
       ROUND(
           100.0 * (SELECT COUNT(*) FROM warehouse.vw_customer_summary WHERE order_count >= 2)
           / NULLIF((SELECT COUNT(*) FROM warehouse.vw_customer_summary), 0), 2
       ) AS repeat_purchase_rate_pct
FROM warehouse.vw_customer_summary s
WHERE s.order_count >= 2
ORDER BY s.total_spend DESC;


-- View5: Daily Sales, materialized (the rows are stored, not recalculated on every read)
-- has to be dropped first because CREATE OR REPLACE doesn't work on materialized views
DROP MATERIALIZED VIEW IF EXISTS warehouse.mvw_daily_sales;
CREATE MATERIALIZED VIEW warehouse.mvw_daily_sales AS
SELECT d.full_date AS sale_date,
       SUM(f.total_amount) AS total_revenue,
       COUNT(*) AS order_count,
       COUNT(DISTINCT f.customer_key) AS unique_customers
FROM warehouse.fact_orders f
JOIN warehouse.dim_date d ON f.date_key = d.date_key
WHERE f.status = 'completed'
GROUP BY d.full_date
ORDER BY sale_date;

-- a unique index is what lets the refresh run CONCURRENTLY, so readers aren't locked out
CREATE UNIQUE INDEX IF NOT EXISTS idx_mvw_daily_sales_date ON warehouse.mvw_daily_sales (sale_date);
