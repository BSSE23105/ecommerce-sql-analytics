import os
import sys
import argparse
import logging

import pandas as pd
from sqlalchemy import text

# the shared connection helper sits in utils/ at the project root, so put the root on the import path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.db_connection import connect_db

here = os.path.dirname(os.path.abspath(__file__))

customers_sql = text("""
    SELECT customer_id, full_name, email, city, signup_date
    FROM customers
    ORDER BY customer_id
""")

products_sql = text("""
    SELECT product_id, title, category, price
    FROM products
    ORDER BY product_id
""")

orders_sql = text("""
    SELECT order_id, customer_id, product_id, quantity, order_date, status
    FROM orders
    ORDER BY order_id
""")


def apply_schema(db):
    # run the warehouse DDL file; every statement is "IF NOT EXISTS" so this is safe to repeat
    with open(os.path.join(here, "warehouse_schema.sql"), "r", encoding="utf-8") as f:
        ddl = f.read()
    with db.begin() as conn:
        conn.exec_driver_sql(ddl)


def build_customer_dim(customers):
    # the surrogate key is just the customer_id, so a key never moves when rows get added or deleted
    dim = customers.copy()
    dim.insert(0, "customer_key", dim["customer_id"])
    key_map = dict(zip(dim["customer_id"], dim["customer_key"]))
    return dim, key_map


def build_product_dim(products):
    # same idea as customers: reuse the natural id so the key stays the same on every reload
    dim = products.copy()
    dim.insert(0, "product_key", dim["product_id"])
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


def verify_load(db):
    # don't trust what we sent, ask the database what actually landed in each table
    tables = ["dim_customers", "dim_products", "dim_date", "fact_orders"]
    with db.connect() as conn:
        for table in tables:
            rows = conn.execute(text(f"SELECT COUNT(*) FROM warehouse.{table}")).scalar()
            logging.info("verified  warehouse.%s = %d rows", table, rows)
        total = conn.execute(text("SELECT COALESCE(SUM(total_amount), 0) FROM warehouse.fact_orders "
                                  "WHERE status = 'completed'")).scalar()
    logging.info("verified  completed revenue in the warehouse = %s", total)


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    parser = argparse.ArgumentParser(description="Load the star-schema warehouse from the OLTP tables.")
    parser.add_argument("--force", action="store_true", help="skip the reload confirmation prompt")
    args = parser.parse_args()

    db = connect_db()
    apply_schema(db)

    # read the operational tables that task 2 already loaded
    logging.info("Reading the OLTP tables...")
    with db.connect() as conn:
        customers = pd.read_sql(customers_sql, conn)
        products = pd.read_sql(products_sql, conn)
        orders = pd.read_sql(orders_sql, conn)

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
    verify_load(db)


if __name__ == "__main__":
    main()
