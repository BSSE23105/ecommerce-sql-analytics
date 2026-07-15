import os
import sys
import argparse
import logging
from datetime import datetime

import pandas as pd
from sqlalchemy import text

from db_connection import connect_db

here = os.path.dirname(os.path.abspath(__file__))
raw_dir = os.path.join(here, "raw")
out_dir = os.path.join(here, "output")
os.makedirs(out_dir, exist_ok=True)

ok_statuses = ("completed", "pending", "returned", "cancelled")


def drop_row(table, row, problems, bad_rows):
    record = dict(row)
    record["source_table"] = table
    record["rejection_reason"] = "; ".join(problems)
    bad_rows.append(record)


def email_ok(value):
    return isinstance(value, str) and "@" in value and "." in value.split("@")[-1]


def to_date(value):
    try:
        return datetime.strptime(str(value).strip(), "%Y-%m-%d").date()
    except Exception:
        return None


def cell(value):
    return str(value).strip() if pd.notna(value) else ""


def clean_customers(raw, bad_rows):
    kept = []
    seen = set()
    for _, row in raw.iterrows():
        problems = []
        name = cell(row["full_name"])
        email = cell(row["email"])
        city = cell(row["city"])

        if not name:
            problems.append("missing full_name")
        if not email:
            problems.append("missing email")
        elif not email_ok(email):
            problems.append("invalid email format")
        elif email.lower() in seen:
            problems.append("duplicate email")
        if not city:
            problems.append("missing city")

        # signup_date is optional, but if it's there it has to be a real date
        signup = None
        if pd.notna(row["signup_date"]) and str(row["signup_date"]).strip():
            signup = to_date(row["signup_date"])
            if signup is None:
                problems.append("invalid signup_date")

        if problems:
            drop_row("customers", row, problems, bad_rows)
            continue

        seen.add(email.lower())
        kept.append({"customer_id": int(row["customer_id"]), "full_name": name,
                     "email": email, "city": city, "signup_date": signup})
    return pd.DataFrame(kept)


def clean_products(raw, bad_rows):
    kept = []
    for _, row in raw.iterrows():
        problems = []
        title = cell(row["title"])
        category = cell(row["category"])

        # price has to be a real number greater than zero (blanks and "N/A" come in as NaN, so catch those too)
        price = None
        try:
            price = float(row["price"])
            if pd.isna(price):
                problems.append("invalid price")
            elif price <= 0:
                problems.append("price must be positive")
        except (ValueError, TypeError):
            problems.append("invalid price")

        if not title:
            problems.append("missing title")
        if not category:
            problems.append("missing category")

        if problems:
            drop_row("products", row, problems, bad_rows)
            continue

        kept.append({"product_id": int(row["product_id"]), "title": title,
                     "category": category, "price": price})
    return pd.DataFrame(kept)


def clean_orders(raw, cust_ids, prod_ids, bad_rows):
    kept = []
    for _, row in raw.iterrows():
        problems = []

        qty = None
        try:
            qty = int(row["quantity"])
            if qty <= 0:
                problems.append("quantity must be positive")
        except (ValueError, TypeError):
            problems.append("invalid quantity")

        status = cell(row["status"])
        if status not in ok_statuses:
            problems.append("invalid status")

        odate = to_date(row["order_date"])
        if odate is None:
            problems.append("invalid order_date")

        # the customer and product this order points at must actually exist
        buyer = None
        try:
            buyer = int(row["customer_id"])
        except (ValueError, TypeError):
            problems.append("invalid customer_id")
        if buyer is not None and buyer not in cust_ids:
            problems.append("customer_id not found")

        item = None
        try:
            item = int(row["product_id"])
        except (ValueError, TypeError):
            problems.append("invalid product_id")
        if item is not None and item not in prod_ids:
            problems.append("product_id not found")

        if problems:
            drop_row("orders", row, problems, bad_rows)
            continue

        kept.append({"order_id": int(row["order_id"]), "customer_id": buyer,
                     "product_id": item, "quantity": qty, "order_date": odate,
                     "status": status})
    return pd.DataFrame(kept)


def confirm_truncate(force):
    # truncating wipes every row, so make sure the user really means it unless they passed --force
    if force:
        return True
    logging.warning("This will DELETE all rows in payments, orders, products and customers.")
    try:
        answer = input("Type 'yes' to continue: ")
    except EOFError:
        answer = ""
    return answer.strip().lower() == "yes"


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    parser = argparse.ArgumentParser(description="Clean the raw CSVs and load them into PostgreSQL.")
    parser.add_argument("--force", action="store_true", help="skip the truncate confirmation prompt")
    args = parser.parse_args()

    db = connect_db()

    # extract + transform: read each raw file and keep only the rows that pass every check
    bad_rows = []
    logging.info("Reading and cleaning the raw CSV files...")
    customers = clean_customers(pd.read_csv(os.path.join(raw_dir, "customers_raw.csv")), bad_rows)
    products = clean_products(pd.read_csv(os.path.join(raw_dir, "products_raw.csv")), bad_rows)
    orders = clean_orders(pd.read_csv(os.path.join(raw_dir, "orders_raw.csv")),
                          set(customers["customer_id"]), set(products["product_id"]), bad_rows)

    if not confirm_truncate(args.force):
        logging.warning("Cancelled. Nothing was changed in the database.")
        sys.exit(0)

    # clear the tables first so re-running doesn't pile up duplicates
    with db.begin() as conn:
        conn.execute(text("TRUNCATE payments, orders, products, customers RESTART IDENTITY CASCADE;"))

    # load: parents (customers, products) before children (orders) because of the foreign keys
    customers.to_sql("customers", db, if_exists="append", index=False)
    products.to_sql("products", db, if_exists="append", index=False)
    orders.to_sql("orders", db, if_exists="append", index=False)

    # dead-letter file: keep every rejected row with the reason it failed
    if bad_rows:
        pd.DataFrame(bad_rows).to_csv(os.path.join(out_dir, "rejected_records.csv"), index=False)

    logging.info("Loaded  customers=%d  products=%d  orders=%d", len(customers), len(products), len(orders))
    logging.info("Rejected %d rows -> output/rejected_records.csv", len(bad_rows))


if __name__ == "__main__":
    main()
