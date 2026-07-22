# Task 4 — Analytics Layer (SQL Views + Python Reporting)

Task 3 built the warehouse. This task puts a set of SQL views on top of it, so reports and charts
never query `fact_orders` directly.

The reason for working this way is that if ten people each write their own revenue query, you end up
with ten slightly different numbers. One of them forgets `WHERE status = 'completed'`, another one
uses the current product price instead of the price that was stored on the order. Writing the
definition once, in a view, stops that. Views are also reusable (`vw_repeat_customers` is built on
top of `vw_customer_summary` instead of repeating its logic) and you can give an analyst access to a
view without giving them the fact table underneath it.

## The four views

They all live in `views.sql` and get created inside the `warehouse` schema.

`vw_monthly_revenue` has revenue, order count and AOV per month, completed orders only. AOV is
average order value, revenue divided by the number of orders. It's useful because it tells you
whether growth came from more orders or from bigger ones.

`vw_category_performance` has revenue, units sold and average price per category. It averages the
`unit_price` sitting on the fact row rather than the current price in `dim_products`, since a
warehouse is supposed to report what was true when the order happened.

`vw_customer_summary` is one row per customer, with order count, total spend, first and last order
date, and days since their last order.

`vw_repeat_customers` is only the customers with 2 or more orders, plus the overall repeat purchase
rate. The rate is a whole-table number so it comes out identical on every row.

Two small things in that last calculation are worth knowing:

```sql
ROUND(100.0 * (SELECT COUNT(*) ... WHERE order_count >= 2)
      / NULLIF((SELECT COUNT(*) ...), 0), 2)
```

Writing `100.0` instead of `100` forces numeric division. With plain integers PostgreSQL does integer
division and 4/38 comes out as 0. And `NULLIF(x, 0)` keeps it from blowing up with a divide-by-zero
if the warehouse is ever empty.

## The materialized view

`mvw_daily_sales` holds date, total revenue, order count and unique customers per day.

A normal view stores no data at all, it's just a saved query that runs again on every SELECT. That
makes it always current, but you pay for the query each time you read it. A materialized view stores
the actual result rows on disk, so reading it is as quick as reading a table, but the data is frozen
at whenever it was last refreshed. The trade-off is freshness against speed.

### What REFRESH MATERIALIZED VIEW does

```sql
REFRESH MATERIALIZED VIEW warehouse.mvw_daily_sales;
```

It re-runs the stored query and overwrites the saved rows. Nothing refreshes on its own, and that's
the part people get caught by. You can load 500 new orders into `fact_orders` and the materialized
view will still be showing yesterday's totals until somebody runs that command.

So it needs running after every warehouse load, or on a schedule that matches how fresh the numbers
actually have to be. Nightly is fine for a daily sales report, hourly if the business is watching it
more closely than that.

A plain refresh takes an exclusive lock, so nobody can read the view while it rebuilds. Adding
CONCURRENTLY avoids that by building the new copy next to the old one. It only works if the view has
a unique index, which is why `views.sql` creates one on `sale_date`:

```sql
REFRESH MATERIALIZED VIEW CONCURRENTLY warehouse.mvw_daily_sales;
```

## analytics_report.py

The script connects with the shared helper from `utils/`, runs `views.sql` first so the views are
guaranteed to be there, and then queries only the views. Everything it writes goes into `output/`:

- `monthly_revenue.png` is a line chart, because months are in order and a line shows the shape of
  the trend
- `category_revenue.png` is a bar chart, just a few categories compared side by side
- `top_customers.png` uses horizontal bars, so the long customer names still fit on the axis
- `summary_stats.json` has total revenue, total customers, total orders, best category and repeat
  rate %

One note on the JSON: `total_customers` counts customers with at least one completed order, because
that's what `vw_customer_summary` contains. It's a smaller number than the row count of
`dim_customers`.

## Running it

```powershell
cd task4
python analytics_report.py
```

The warehouse has to be loaded first, so run `task3/load_warehouse.py` before this one. If you'd
rather create the views by hand instead, open `views.sql` in DBeaver and run it, the script does
exactly the same thing.
