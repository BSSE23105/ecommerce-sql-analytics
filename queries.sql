-- Query1: Revenue by Product Category
select p.category, COUNT(o.order_id) AS total_orders, SUM(o.quantity * p.price) AS total_revenue
FROM orders o
JOIN products p ON o.product_id = p.product_id
WHERE o.status = 'completed'
GROUP BY p.category
ORDER BY total_revenue DESC;


-- Query2: Top 5 Customers by Spending
select c.full_name, c.city, COUNT(o.order_id) AS orders_placed, SUM(pay.amount) AS total_spent
FROM customers c
JOIN orders o     ON c.customer_id = o.customer_id
JOIN payments pay ON o.order_id    = pay.order_id
WHERE o.status = 'completed'
GROUP BY c.customer_id, c.full_name, c.city
ORDER BY total_spent DESC
LIMIT 5;


-- Query3: Monthly Revenue Trend
select TO_CHAR(DATE_TRUNC('month', pay.payment_date), 'Mon YYYY') AS month, COUNT(pay.payment_id) AS payments_received, SUM(pay.amount) AS monthly_revenue
FROM payments pay
JOIN orders o ON   pay.order_id = o.order_id
GROUP BY DATE_TRUNC('month', pay.payment_date)
ORDER BY DATE_TRUNC('month', pay.payment_date);


-- Query4: Most Popular Products
select p.title, p.category, p.price, SUM(o.quantity) AS units_sold, COUNT(o.order_id) AS times_ordered
FROM products p
JOIN orders o ON p.product_id = o.product_id
WHERE o.status != 'returned'
GROUP BY p.product_id, p.title, p.category, p.price
ORDER BY units_sold DESC
LIMIT 10;


-- Query5: Rank Customers by Spending Within Each City
WITH customer_spending AS (
    select c.customer_id, c.full_name, c.city, SUM(pay.amount) AS total_spent
    FROM customers c
    JOIN orders o     ON c.customer_id = o.customer_id
    JOIN payments pay ON o.order_id    = pay.order_id
    GROUP BY c.customer_id, c.full_name, c.city
)
select city, full_name, total_spent, RANK() OVER (PARTITION BY city ORDER BY total_spent DESC) AS rank_in_city
FROM customer_spending
ORDER BY city, rank_in_city;


-- Query6: Running Total of Revenue
select pay.payment_date, pay.amount, SUM(pay.amount) OVER (
        ORDER BY pay.payment_date, pay.payment_id
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_total
FROM payments pay
ORDER BY pay.payment_date, pay.payment_id;


-- Query7: Compare Each Payment to the Previous One
select pay.payment_id, pay.payment_date, pay.amount,
    LAG(pay.amount)  OVER (ORDER BY pay.payment_date, pay.payment_id) AS previous_payment,
    pay.amount - LAG(pay.amount) OVER (ORDER BY pay.payment_date, pay.payment_id) AS difference
FROM payments pay
ORDER BY pay.payment_date, pay.payment_id;


-- Query8: Compare Each Payment to the Next One
select pay.payment_id, pay.payment_date, pay.amount,
    LEAD(pay.amount) OVER (ORDER BY pay.payment_date, pay.payment_id) AS next_payment,
    LEAD(pay.amount) OVER (ORDER BY pay.payment_date, pay.payment_id) - pay.amount AS upcoming_change
FROM payments pay
ORDER BY pay.payment_date, pay.payment_id;


-- Query9: Put each customer's orders in time order and give them numbers
select c.full_name, o.order_id, o.order_date, o.status,
    ROW_NUMBER() OVER (
        PARTITION BY o.customer_id
        ORDER BY o.order_date
    ) AS order_number
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
ORDER BY c.full_name, order_number;


--  Query10: Label Orders as Small / Medium / Large
select o.order_id, c.full_name, p.title AS product, pay.amount,
    CASE
        WHEN pay.amount < 1000  THEN 'Small'
        WHEN pay.amount < 5000  THEN 'Medium'
        ELSE                         'Large'
    END AS order_size
FROM orders o
JOIN customers c  ON o.customer_id  = c.customer_id
JOIN products p   ON o.product_id   = p.product_id
JOIN payments pay ON o.order_id     = pay.order_id
ORDER BY pay.amount DESC;


-- Query11: Customers Who Never Completed an Order
WITH completed_orders AS (
    select DISTINCT customer_id
    FROM orders
    WHERE status = 'completed'
)
select c.full_name, c.email, c.city
FROM customers c
WHERE c.customer_id NOT IN (select customer_id FROM completed_orders)
ORDER BY c.full_name;


-- Query12: Most Used Payment Method Per City
WITH city_payment_counts AS (
    select c.city, pay.method, COUNT(*) AS usage_count,
        RANK() OVER (PARTITION BY c.city ORDER BY COUNT(*) DESC) AS rnk
    FROM payments pay
    JOIN orders o    ON pay.order_id    = o.order_id
    JOIN customers c ON o.customer_id   = c.customer_id
    GROUP BY c.city, pay.method
)
select city, method  AS preferred_payment_method, usage_count
FROM city_payment_counts
WHERE rnk = 1
ORDER BY city;


-- Query13: Return Rate Per Product with Risk Flag
select p.title, COUNT(o.order_id) AS total_orders,
    SUM(CASE WHEN o.status = 'returned' THEN 1 ELSE 0 END) AS returns,
    ROUND(SUM(CASE WHEN o.status = 'returned' THEN 1 ELSE 0 END) * 100.0 / COUNT(o.order_id), 2) AS return_rate_pct,
    CASE
        WHEN SUM(CASE WHEN o.status = 'returned' THEN 1 ELSE 0 END) * 100.0 / COUNT(o.order_id) > 20
        THEN 'High Return Risk'
        ELSE 'Normal'
    END AS return_flag
FROM products p
JOIN orders o ON p.product_id = o.product_id
GROUP BY p.product_id, p.title
ORDER BY return_rate_pct DESC;
