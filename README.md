# E-Commerce SQL Analytics

A practice project where I set up a realistic e-commerce database in PostgreSQL, populate it with sample data, and then work with it two ways: writing analytical SQL by hand (Task 1) and building a Python ETL pipeline that loads and reports on the data automatically (Task 2).

The dataset covers customers from 12 Pakistani cities, orders across 4 product categories (beauty, fragrances, furniture, groceries), and payments through local methods like EasyPaisa, JazzCash, and Cash on Delivery.

---



## What's in the Repo

```
ecommerce-sql-analytics/
│
├── README.md
├── schema.sql                 -- create the 4 tables
├── queries.sql                -- 13 analytical queries (Task 1)
│
├── data/                      -- Task 1 sample data
│   ├── products.csv
│   ├── customers.csv
│   ├── orders.csv
│   └── payments.csv
│
└── task2/                     -- Task 2 ETL pipeline
    ├── generate_data.py       -- make the raw (messy) CSV files
    ├── extract_load.py        -- clean the CSVs and load them into PostgreSQL
    ├── export_report.py       -- export a summary sales report
    ├── requirements.txt       -- Python packages needed
    └── .env.example           -- template for DB credentials
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
| `export_report.py` | Runs summary queries and exports `weekly_sales_report.csv`: revenue per category, top 5 customers, orders by status, and month-over-month revenue change. |

Database credentials are never hardcoded — they are read from a `.env` file.

## How to run it

All commands are run from the `task2` folder in PowerShell.

### 1. Create a virtual environment and install packages

```powershell
cd task2
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Set up your database credentials

Copy the template and fill in your real PostgreSQL values:

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
python generate_data.py     # creates raw/ CSV files
python extract_load.py      # cleans + loads into PostgreSQL, writes rejected rows
python export_report.py     # writes the sales report
```

## What you get

| File | Description |
|---|---|
| `raw/customers_raw.csv`, `raw/products_raw.csv`, `raw/orders_raw.csv` | The messy input data. |
| `output/rejected_records.csv` | Every rejected row with a `rejection_reason` column. |
| `output/weekly_sales_report.csv` | The final summary report. |

The pipeline is safe to re-run — `extract_load.py` clears the tables before each load, so you never get duplicates.

---

## Tools Used

- PostgreSQL 15
- DBeaver 24
- Python 3 (pandas, SQLAlchemy, psycopg2, python-dotenv, Faker)
- Git + GitHub
