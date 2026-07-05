# E-Commerce SQL Analytics

This is a practice project inwhich I set up a realistic e-commerce database in PostgreSQL, populate it with sample data, and then write analytical queries that actually tell you something useful about the business.

The dataset covers customers from 12 Pakistani cities, orders across 4 product categories (beauty, fragrances, furniture, groceries), and payments through local methods like EasyPaisa, JazzCash, and Cash on Delivery.

---

## What's in the Repo

```
ecommerce-sql-analytics/
│
├── README.md                  
├── schema.sql                 -- create the tables from scratch
├── queries.sql     -- 13 queries covering all major SQL concepts
│
└── data/
    ├── products.csv           -- 18 products across 4 categories
    ├── customers.csv          -- 40 customers from across Pakistan
    ├── orders.csv             -- 159 orders with statuses
    └── payments.csv           -- 107 payments across 5 payment methods
```

---

## Database Schema

Four tables with foreign key relationships:

```
products  ──┐
            ├──▶  orders  ──▶  payments
customers ──┘
```

### products
| Column | Type |
|---|---|
| product_id | SERIAL PRIMARY KEY |
| title | VARCHAR(100) |
| category | VARCHAR(50) |
| price | NUMERIC(10,2) |

### customers
| Column | Type |
|---|---|
| customer_id | SERIAL PRIMARY KEY |
| full_name | VARCHAR(100) |
| email | VARCHAR(100) |
| city | VARCHAR(50) |
| signup_date | DATE |

### orders
| Column | Type |
|---|---|
| order_id | SERIAL PRIMARY KEY |
| customer_id | INT → customers |
| product_id | INT → products |
| quantity | INT |
| order_date | DATE |
| status | VARCHAR(20) |

> Status values: `completed`, `pending`, `returned`, `cancelled`

### payments
| Column | Type |
|---|---|
| payment_id | SERIAL PRIMARY KEY |
| order_id | INT → orders |
| payment_date | DATE |
| amount | NUMERIC(10,2) |
| method | VARCHAR(20) |

> Payment methods: `EasyPaisa`, `JazzCash`, `Card`, `Cash on Delivery`, `Bank Transfer`

---

## How to Set This Up

### 1. Run schema.sql first

Open DBeaver, connect to your PostgreSQL database, open `schema.sql` and run it. This creates all 4 tables with the right constraints.


### 2. Import the CSVs in this order

The order matters because of foreign keys — you can't import orders before products and customers exist.

```
1. products.csv
2. customers.csv
3. orders.csv
4. payments.csv
```

In DBeaver: right-click the table → Import Data → select the CSV → make sure column mapping looks correct → finish.

> The CSVs don't have ID columns. Leave those unmapped in the wizard — PostgreSQL generates them automatically starting from 1.

### 3. Verify everything imported correctly

```sql
SELECT 'products'  AS tbl, COUNT(*) FROM products
UNION ALL
SELECT 'customers', COUNT(*) FROM customers
UNION ALL
SELECT 'orders',    COUNT(*) FROM orders
UNION ALL
SELECT 'payments',  COUNT(*) FROM payments;
```

You should see: **18 / 40 / 159 / 107**

---

## Queries Overview

All 13 queries are in `queries.sql`, each with a comment explaining what it does and why. Here's the summary:

| # | What it answers | Concepts |
|---|---|---|
| 1 | Which product category makes the most revenue? | JOIN, GROUP BY, SUM |
| 2 | Who are the top 5 customers by total spending? | JOIN across 3 tables |
| 3 | How does revenue trend month by month? | DATE_TRUNC, GROUP BY |
| 4 | Which products sell the most units? | JOIN, SUM, filter |
| 5 | Who spends the most in each city? | CTE, RANK(), PARTITION BY |
| 6 | What does cumulative revenue look like over time? | SUM() window function |
| 7 | How does each payment compare to the one before it? | LAG() |
| 8 | How does each payment compare to the one after it? | LEAD() |
| 9 | What number order is this for each customer? | ROW_NUMBER(), PARTITION BY |
| 10 | Are orders small, medium, or large by payment amount? | CASE WHEN, 4-table JOIN |
| 11 | Which customers never completed a single order? | CTE, NOT IN |
| 12 | What payment method does each city prefer? | CTE, RANK(), PARTITION BY |
| 13 | Which products have a high return rate? | CASE WHEN inside SUM, ROUND |

---

## Tools Used

- PostgreSQL 15
- DBeaver 24
- Git + GitHub
