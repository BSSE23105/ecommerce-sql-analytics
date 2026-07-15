import os
import sys
import argparse
import logging

import pandas as pd
from sqlalchemy import text

# reuse the same database helper we built in task 2 instead of copying the connection code
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "task2"))
from db_connection import connect_db

here = os.path.dirname(os.path.abspath(__file__))


def apply_schema(db):
    # run the warehouse DDL file; every statement is "IF NOT EXISTS" so this is safe to repeat
    with open(os.path.join(here, "warehouse_schema.sql"), "r", encoding="utf-8") as f:
        ddl = f.read()
    with db.begin() as conn:
        conn.exec_driver_sql(ddl)


def build_customer_dim(customers):
    # give every customer a surrogate key (1, 2, 3...) after sorting so the keys stay the same each run
    dim = customers.sort_values("customer_id").reset_index(drop=True)
    dim.insert(0, "customer_key", list(range(1, len(dim) + 1)))
    key_map = dict(zip(dim["customer_id"], dim["customer_key"]))
    return dim, key_map


def build_product_dim(products):
    # same idea as customers: a fresh surrogate key per product
    dim = products.sort_values("product_id").reset_index(drop=True)
    dim.insert(0, "product_key", list(range(1, len(dim) + 1)))
    key_map = dict(zip(dim["product_id"], dim["product_key"]))
    return dim, key_map


def build_date_dim(order_dates):
    # make one calendar row for every day between the first and last order, keyed as YYYYMMDD
    days = pd.date_range(order_dates.min(), order_dates.max(), freq="D")
    dim = pd.DataFrame({
        "date_key": days.strftime("%Y%m%d").astype(int),
        "full_date": days.date,
        "year": days.year,
        "quarter": days.quarter,
        "month": days.month,
        "month_name": days.month_name(),
        "day": days.day,
        "day_of_week": days.dayofweek + 1,
        "day_name": days.day_name(),
        "is_weekend": days.dayofweek >= 5,
    })
    return dim


def build_fact(orders, cust_map, prod_map, price_map):
    # turn each order into a fact row that points at the three dimension keys and carries the measures
    fact = pd.DataFrame({
        "order_id": orders["order_id"],
        "customer_key": orders["customer_id"].map(cust_map),
        "product_key": orders["product_id"].map(prod_map),
        "date_key": pd.to_datetime(orders["order_date"]).dt.strftime("%Y%m%d").astype(int),
        "quantity": orders["quantity"],
        "unit_price": orders["product_id"].map(price_map),
        "status": orders["status"],
    })
    fact["total_amount"] = fact["quantity"] * fact["unit_price"]
    return fact


def confirm_truncate(force):
    # reloading wipes the warehouse tables first, so ask before doing it unless --force was passed
    if force:
        return True
    logging.warning("This will DELETE all rows in the warehouse dim/fact tables and reload them.")
    try:
        answer = input("Type 'yes' to continue: ")
    except EOFError:
        answer = ""
    return answer.strip().lower() == "yes"


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    parser = argparse.ArgumentParser(description="Load the star-schema warehouse from the OLTP tables.")
    parser.add_argument("--force", action="store_true", help="skip the reload confirmation prompt")
    args = parser.parse_args()

    db = connect_db()
    apply_schema(db)

    # read the operational tables that task 2 already loaded
    logging.info("Reading the OLTP tables...")
    customers = pd.read_sql("SELECT * FROM customers", db)
    products = pd.read_sql("SELECT * FROM products", db)
    orders = pd.read_sql("SELECT * FROM orders", db)

    if orders.empty:
        logging.error("No orders found in the OLTP database. Run the task 2 pipeline first.")
        sys.exit(1)

    # build the three dimensions, then the fact using their keys
    dim_customers, cust_map = build_customer_dim(customers)
    dim_products, prod_map = build_product_dim(products)
    dim_date = build_date_dim(pd.to_datetime(orders["order_date"]))
    price_map = dict(zip(products["product_id"], products["price"]))
    fact_orders = build_fact(orders, cust_map, prod_map, price_map)

    # every order must resolve to a real customer, product and date key before we load it
    if fact_orders[["customer_key", "product_key", "date_key"]].isna().any().any():
        logging.error("Some orders could not be matched to a dimension key. Load stopped.")
        sys.exit(1)

    if not confirm_truncate(args.force):
        logging.warning("Cancelled. Nothing was changed in the warehouse.")
        sys.exit(0)

    # clear the warehouse so a reload doesn't pile up duplicates
    with db.begin() as conn:
        conn.execute(text("TRUNCATE warehouse.fact_orders, warehouse.dim_customers, "
                          "warehouse.dim_products, warehouse.dim_date RESTART IDENTITY CASCADE;"))

    # load the dimensions first, then the fact that references them
    dim_customers.to_sql("dim_customers", db, schema="warehouse", if_exists="append", index=False)
    dim_products.to_sql("dim_products", db, schema="warehouse", if_exists="append", index=False)
    dim_date.to_sql("dim_date", db, schema="warehouse", if_exists="append", index=False)
    fact_orders.to_sql("fact_orders", db, schema="warehouse", if_exists="append", index=False)

    logging.info("Warehouse loaded  dim_customers=%d  dim_products=%d  dim_date=%d  fact_orders=%d",
                 len(dim_customers), len(dim_products), len(dim_date), len(fact_orders))


if __name__ == "__main__":
    main()
