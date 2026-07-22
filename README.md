# E-Commerce SQL Analytics

A practice project where I set up a realistic e-commerce database in PostgreSQL, populate it with sample data, and then work with it four ways: writing analytical SQL by hand (Task 1), building a Python ETL pipeline that loads and reports on the data automatically (Task 2), designing a star-schema data warehouse with a Python transformation layer (Task 3), and putting an analytics layer of SQL views on top of it with a Python charting script (Task 4).

The dataset covers customers from 12 Pakistani cities, orders across 4 product categories (beauty, fragrances, furniture, groceries), and payments through local methods like EasyPaisa, JazzCash, and Cash on Delivery.

---



## What's in the Repo

```
ecommerce-sql-analytics/
│
├── README.md
├── schema.sql                 -- create the 4 tables
├── queries.sql                -- 13 analytical queries (Task 1)
├── requirements.txt           -- Python packages needed
├── .env.example               -- template for DB credentials
│
├── data/                      -- Task 1 sample data
│   ├── products.csv
│   ├── customers.csv
│   ├── orders.csv
│   └── payments.csv
│
├── utils/                     -- shared across every task
│   └── db_connection.py       -- reusable database connection helper
│
├── task2/                     -- Task 2 ETL pipeline
│   ├── generate_data.py       -- make the raw (messy) CSV files
│   ├── extract_load.py        -- clean the CSVs and load them into PostgreSQL
│   └── export_report.py       -- export the summary sales report (Excel)
│
├── task3/                     -- Task 3 data warehouse (star schema)
│   ├── warehouse_schema.sql   -- the warehouse schema (dim + fact tables)
│   └── load_warehouse.py      -- load the warehouse from the OLTP tables
│
└── task4/                     -- Task 4 analytics layer
    ├── views.sql              -- 4 views + 1 materialized view
    ├── analytics_report.py    -- query the views, draw charts, export stats
    ├── README.md              -- the Task 4 write-up
    └── output/                -- 3 PNG charts + summary_stats.json
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
| title | VARCHAR(150) |
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

# Task 1 — SQL Schema and Analytical Queries

Task 1 was about setting up the database by hand in DBeaver and writing SQL queries that answer real business questions.

## How to set it up

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

In DBeaver: right-click the table → Import Data → select the CSV → check the column mapping → finish.

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

## Queries Overview

All 13 queries are in `queries.sql`, each with a comment explaining what it does. Summary:

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

# Task 2 — ETL Pipeline with Python

Task 1 loaded data manually through DBeaver. Task 2 builds a proper ETL pipeline in Python that does it automatically: it reads raw CSV files, cleans out the bad data, loads the good rows into the same PostgreSQL tables, and exports a sales report.

## What the scripts do

| Script | Purpose |
|---|---|
| `generate_data.py` | Creates the raw CSVs (`customers_raw.csv`, `products_raw.csv`, `orders_raw.csv`) using the Faker library. The data is intentionally messy (nulls, duplicate emails, bad prices, invalid dates, broken references) to simulate a real frontend export. |
| `extract_load.py` | Reads the raw CSVs with pandas, validates each row, and loads the clean ones into PostgreSQL with SQLAlchemy. Any bad row is written to `rejected_records.csv` with a reason — the dead-letter pattern. |
| `export_report.py` | Runs summary queries and exports `weekly_sales_report.xlsx` (four worksheets): revenue per category, top 5 customers, orders by status, and month-over-month revenue change. |
| `utils/db_connection.py` | A single reusable `connect_db()` shared by every script in every task. It reads the credentials, opens the engine, and checks the connection actually works — failing with a clear message instead of a crash. It lives in `utils/` at the project root so no task ever has to reach into another task's folder. |

Database credentials are never hardcoded — they are read from a `.env` file. All scripts use the
`logging` module, so every run is timestamped.

## How to run it

### 1. Create a virtual environment and install packages

From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Set up your database credentials

Copy the template and fill in your real PostgreSQL values (also in the project root):

```powershell
Copy-Item .env.example .env
notepad .env
```

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ecommerce
DB_USER=postgres
DB_PASSWORD=your_password
```

> The Task 1 tables (`customers`, `products`, `orders`, `payments`) must already exist. If they don't, run `schema.sql` first.

### 3. Run the three scripts in order

```powershell
cd task2
python generate_data.py     # creates raw/ CSV files
python extract_load.py      # cleans + loads into PostgreSQL, writes rejected rows
python export_report.py     # writes the sales report
```

> `extract_load.py` asks you to confirm before it clears the tables. Add `--force` to skip the
> prompt (`python extract_load.py --force`).

## What you get

| File | Description |
|---|---|
| `raw/customers_raw.csv`, `raw/products_raw.csv`, `raw/orders_raw.csv` | The messy input data. |
| `output/rejected_records.csv` | Every rejected row with a `rejection_reason` column. |
| `output/weekly_sales_report.xlsx` | The final summary report — one worksheet per section. |

The pipeline is safe to re-run — `extract_load.py` clears the tables before each load, so you never get duplicates.

---

# Task 3 — Data Warehouse (Star Schema)

Task 2 built the operational database (OLTP) — good for day-to-day reads and writes. Task 3 adds a
separate **data warehouse**: the same data reshaped into a **star schema** that's built for analysis
and reporting. A Python transformation script reads the OLTP tables and loads a new `warehouse`
schema.

## The star schema

One central **fact** table surrounded by three **dimension** tables:

```
dim_customers ──┐
dim_products  ──┼──▶  fact_orders
dim_date      ──┘
```

| Table | What it holds |
|---|---|
| `dim_customers` | One row per customer. Has a surrogate `customer_key` plus the natural `customer_id`. |
| `dim_products` | One row per product. Surrogate `product_key` plus the natural `product_id`. |
| `dim_date` | One row per calendar day, keyed `YYYYMMDD`, with year / quarter / month / day-name / weekend flag. |
| `fact_orders` | One row per order (the *grain*). Points at the three dimensions by their keys and stores the measures: `quantity`, `unit_price`, `total_amount`. |

Key ideas: **surrogate keys** (the warehouse ids the fact points at), **natural keys** (the original
business ids), **grain** (one row per order), and **SCD Type 1** dimensions (rebuilt on each load).

The surrogate keys are the customer and product ids themselves, not a fresh 1, 2, 3 sequence. If the
key came from row position instead, it would shift for everybody the moment a source row got deleted,
and every fact row pointing at the old key would quietly mean a different customer. Keys have to stay
stable between runs.

`fact_orders.status` has a CHECK constraint on it so only the four real statuses can get into the
warehouse, and `dim_date.full_date` is indexed because reports filter on date ranges much more often
than on the YYYYMMDD key.

## How to run it

From the `task3` folder, using the same virtual environment and root `.env`:

```powershell
cd task3
python load_warehouse.py
```

The script creates the `warehouse` schema automatically (you don't need to run
`warehouse_schema.sql` by hand), then loads the dimensions and the fact. Like Task 2, it asks before
clearing the warehouse; add `--force` to skip the prompt. After loading it queries the warehouse back
and logs the row counts, so you see what actually landed rather than what was sent.

> The Task 2 pipeline must have loaded the OLTP tables first — Task 3 reads from them.

## What you get

A new `warehouse` schema in the same PostgreSQL database. In DBeaver:
**Schemas → warehouse → Tables** to view `dim_customers`, `dim_products`, `dim_date`, and
`fact_orders` (press **F5** to refresh if they don't appear).

```sql
SELECT 'dim_customers' AS tbl, COUNT(*) FROM warehouse.dim_customers
UNION ALL SELECT 'dim_products', COUNT(*) FROM warehouse.dim_products
UNION ALL SELECT 'dim_date',     COUNT(*) FROM warehouse.dim_date
UNION ALL SELECT 'fact_orders',  COUNT(*) FROM warehouse.fact_orders;
```

---

# Task 4 — Analytics Layer (SQL Views + Python Reporting)

Task 3 built the warehouse. Task 4 puts a layer of SQL views on top of it, so that reports and charts
read the views instead of joining `fact_orders` themselves.

```
fact_orders + dims  ──▶  views  ──▶  Python charts / BI tools / analysts
```

The point is that a definition like "revenue" gets written once. If everyone writes their own query
instead, one of them forgets `WHERE status = 'completed'` and now there are two different revenue
numbers in the company. Views are also reusable, `vw_repeat_customers` is built on top of
`vw_customer_summary` rather than repeating it, and you can grant someone a view without granting
them the fact table.

## What's in `views.sql`

| Object | What it gives you |
|---|---|
| `vw_monthly_revenue` | Per month: revenue, order count and AOV (average order value). Completed orders only. |
| `vw_category_performance` | Per category: revenue, units sold, average unit price. |
| `vw_customer_summary` | Per customer: order count, total spend, first / last order date, days since last order. |
| `vw_repeat_customers` | Customers with 2 or more orders, plus the overall repeat purchase rate. |
| `mvw_daily_sales` | A materialized view: revenue, order count and unique customers per day. |

### Views vs materialized views

A regular view stores no data, it's a saved query that runs again on every read, so it's always
current but you pay for the query each time. A materialized view stores the result rows on disk, so
reading it is as fast as reading a table, but the data is frozen at the last refresh.

```sql
REFRESH MATERIALIZED VIEW warehouse.mvw_daily_sales;
```

That command re-runs the stored query and overwrites the saved rows. Nothing happens automatically,
which is the part that catches people out. Until you run it, the view keeps serving its last
snapshot, so new orders in `fact_orders` won't show up at all. It needs running after every warehouse
load, or on a schedule matching how fresh the dashboard has to be (nightly is normal for a daily
sales report).

A plain refresh locks the view while it rebuilds. `views.sql` also creates a unique index on
`sale_date`, which is what lets you run `REFRESH MATERIALIZED VIEW CONCURRENTLY` instead, so readers
keep querying the old rows while the new copy is being built.

## How to run it

```powershell
cd task4
python analytics_report.py
```

The script runs `views.sql` first so the views always exist, then queries only the views and writes
four files into `task4/output/`:

- `monthly_revenue.png`, a line chart, since months are in order and a line shows the trend
- `category_revenue.png`, a bar chart of the four categories
- `top_customers.png`, horizontal bars so the long names still fit on the axis
- `summary_stats.json` with total revenue, total customers, total orders, best category and repeat
  customer rate %

`total_customers` there counts customers with at least one completed order, which is what the views
expose, so it's smaller than the row count of `dim_customers`.

The longer write-up for this task is in [`task4/README.md`](task4/README.md).

---

## Tools Used

- PostgreSQL 15
- DBeaver 24
- Python 3 (pandas, SQLAlchemy, psycopg2, python-dotenv, Faker, openpyxl, matplotlib)
- Git + GitHub
