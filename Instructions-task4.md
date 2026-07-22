Task 4: Analytics Layer — SQL Views + Python Reporting

The warehouse exists. Now make it useful. In real companies, data engineers build an analytics layer, SQL views that sit on top of the warehouse so analysts and dashboards don't query raw fact tables directly. 
This week you build that layer.

Concepts to Study First
- SQL Views vs Materialized Views — difference and when to use each
- KPIs in e-commerce — Revenue, AOV (Average Order Value), Repeat Purchase Rate
- Why views exist — abstraction, security, reusability

Part 1 SQL Views
Create these four views inside the warehouse schema in a file called views.sql:

1. vw_monthly_revenue: month, total revenue, order count, AOV (completed orders only)
2. vw_category_performance: category, total revenue, units sold, avg price
3. vw_customer_summary: per customer: order count, total spend, first order date, last order date, days since last order
4. vw_repeat_customers: customers with 2+ orders; include overall repeat purchase rate as well

Part 2 Materialized View
Create warehouse.mvw_daily_sales with: date, total revenue, order count, unique customers. In your README explain what REFRESH MATERIALIZED VIEW does and when it needs to be run.

Part 3 Python Script
Create analytics_report.py that:
- Queries the views above (not the raw tables)
- Generates 3 charts saved to output/ as PNGs: monthly revenue trend (line), revenue by category (bar), top 10 customers by spend (horizontal bar)
- Exports output/summary_stats.json containing: total revenue, total customers, total orders, best category, repeat customer rate %

Folder Structure
task4/
├── views.sql
├── analytics_report.py
├── output/
│   ├── monthly_revenue.png
│   ├── category_revenue.png
│   ├── top_customers.png
│   └── summary_stats.json
└── README.md