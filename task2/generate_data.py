import os
import csv
import random
from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)

here = os.path.dirname(os.path.abspath(__file__))
raw_dir = os.path.join(here, "raw")
os.makedirs(raw_dir, exist_ok=True)

cities = ["Karachi", "Lahore", "Islamabad", "Rawalpindi", "Faisalabad", "Multan",
          "Peshawar", "Quetta", "Sialkot", "Sargodha", "Hyderabad", "Gujranwala"]
categories = ["beauty", "fragrances", "furniture", "groceries"]
statuses = ["completed", "pending", "returned", "cancelled"]


def chance(p):
    return random.random() < p


# build 300 customers, messing up a few on purpose
cust_rows = []
emails_seen = []
for cid in range(1, 301):
    name = fake.name()
    email = fake.email()
    city = random.choice(cities)
    signup = fake.date_between(start_date="-1y", end_date="today").isoformat()

    if chance(0.05): name = ""
    if chance(0.05): email = ""
    elif chance(0.05): email = email.replace("@", "")
    elif emails_seen and chance(0.05): email = random.choice(emails_seen)
    if chance(0.05): city = ""
    if chance(0.05): signup = "not-a-date"

    if email:
        emails_seen.append(email)
    cust_rows.append([cid, name, email, city, signup])

with open(os.path.join(raw_dir, "customers_raw.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["customer_id", "full_name", "email", "city", "signup_date"])
    w.writerows(cust_rows)


# 50 products, with a few broken prices thrown in
prod_rows = []
for pid in range(1, 51):
    title = fake.catch_phrase()
    category = random.choice(categories)
    price = round(random.uniform(5, 500), 2)

    if chance(0.05): title = ""
    if chance(0.05): category = ""
    roll = random.random()
    if roll < 0.04: price = "N/A"
    elif roll < 0.07: price = -abs(price)
    elif roll < 0.09: price = 0

    prod_rows.append([pid, title, category, price])

with open(os.path.join(raw_dir, "products_raw.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["product_id", "title", "category", "price"])
    w.writerows(prod_rows)


# 400 orders, some pointing at customers/products that don't exist
order_rows = []
for oid in range(1, 401):
    buyer = random.randint(1, 300)
    item = random.randint(1, 50)
    qty = random.randint(1, 5)
    odate = fake.date_between(start_date="-180d", end_date="today").isoformat()
    status = random.choice(statuses)

    if chance(0.04): buyer = 99999
    if chance(0.04): item = 88888
    roll = random.random()
    if roll < 0.03: qty = 0
    elif roll < 0.05: qty = -2
    elif roll < 0.07: qty = "two"
    if chance(0.05): status = "shipped"
    if chance(0.03): odate = "2025-13-40"

    order_rows.append([oid, buyer, item, qty, odate, status])

with open(os.path.join(raw_dir, "orders_raw.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["order_id", "customer_id", "product_id", "quantity", "order_date", "status"])
    w.writerows(order_rows)


print("Done. Raw files are in:", raw_dir)
print(f"customers={len(cust_rows)}  products={len(prod_rows)}  orders={len(order_rows)}")
