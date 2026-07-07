Task 2: ETL Pipeline with Python
Background
In Week 1, you wrote SQL by hand and loaded data manually through DBeaver. This week, you'll build your first real ETL pipeline in Python.

Concepts to Study First 
Before writing any code, understand these:

Python for Data Engineering: pandas, psycopg2, SQLAlchemy, dotenv
ETL vs ELT : revisit this, because now you'll implement it, not just define it
Data Quality: what are nulls, duplicates, type mismatches, and why do they break pipelines?
Environment Variables: why you never hardcode DB credentials in code
Connection Pooling:  basic concept of why we don't open a new DB connection on every query

Part 1 — Extract & Load
You are given raw CSV files (generate them yourself at least 300+ rows using Python's faker (or anyone you like library) . These CSVs simulate data exports from a frontend system:
customers_raw.csv
products_raw.csv
orders_raw.csv

Write a Python script extract_load.py that:
Reads each CSV using pandas
Connects to PostgreSQL using SQLAlchemy (not hardcoded credentials use a .env file with python-env)
Loads data into your existing Week 1 schema tables

Raw data is always dirty. Before loading, your script must handle it
Write all rejected/skipped rows to a separate rejected_records.csv with a rejection_reason column. This is called a dead-letter pattern  used in every real pipeline.

Write a second script export_report.py that connects to your PostgreSQL DB and exports a summary CSV weekly_sales_report.csv containing:

Total revenue per product category
Top 5 customers by spend
Orders count by status
Month-over-month revenue change (using the LAG logic from Week 1)