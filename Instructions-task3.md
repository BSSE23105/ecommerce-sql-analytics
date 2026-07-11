Required Before Task 3

Please complete the following improvements before starting the next task

Create a reusable db_connection.py module.
Add proper database connection error handling.
Make the TRUNCATE operation safe.
Remove the global bad_rows variable.
Replace print() statements with the logging module.
Export reports as separate CSV files (or an Excel workbook).
Pin dependency versions in requirements.txt.
Improve the email corruption logic.

Task 3, Data Warehouse Design & Transformation Layer

Now that you have completed SQL fundamentals and built an ETL pipeline, the next step is to move towards Data Warehousing, 

Objective

Design and implement a basic Star Schema and build a transformation pipeline that loads data from the operational database (OLTP) into a warehouse schema.

Concepts to Learn

Before starting the implementation, study and understand the following topics:

OLTP vs Data Warehouse
Star Schema
Fact Tables
Dimension Tables
Grain of a Fact Table
Surrogate Keys
Natural Keys
Slowly Changing Dimensions (Type 1)
ETL vs ELT
Data Transformation Layer
Deliverables

Create a new PostgreSQL schema named
warehouse

Inside this schema, create the following tables
dim_customers
dim_products
dim_date
fact_orders
Python Transformation Script

Develop a Python script that will:

Read data from the OLTP tables.
Clean and transform the data if required.
Generate surrogate keys where necessary.
Populate all dimension tables.
Populate the fact table using the corresponding dimension keys.
Maintain referential integrity throughout the loading process.
Expected Outcome

By the end of Task 3, you should be able to:

Design a Data Warehouse using a Star Schema.
Understand the difference between operational databases and analytical databases.
Build a transformation layer between OLTP and the Data Warehouse.
Create reusable ETL code for warehouse loading.
Prepare data for reporting and business intelligence tools.