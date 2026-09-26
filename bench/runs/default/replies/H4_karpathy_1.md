An index on `orders.created_at` won't help this query as written, so I haven't just added it. There are two problems in `report.py`:

1. **The filter can't use the index.** `WHERE strftime('%m', created_at) = ?` runs a function on the column, so SQLite still scans the whole table. An index on `created_at` is only used for direct comparisons such as `created_at >= ? AND created_at < ?`.
2. **N+1 queries.** For every matching order, the loop runs two more queries: one to re-fetch the same order, one to get its items. With 5,000 orders that's 10,001 round trips. This is probably most of your slowness.

There's also a likely bug: filtering only on the month means `month='03'` returns March orders from **every year**. Is that intended, or should the report cover one specific month and year?

### Fix that keeps the current behavior

This version uses 2 queries instead of 1 + 2N:

```python
def monthly_report(db, month):
    orders = db.query("SELECT * FROM orders WHERE strftime('%m', created_at) = ?", month)
    items = db.query(
        "SELECT items.* FROM items JOIN orders ON orders.id = items.order_id "
        "WHERE strftime('%m', orders.created_at) = ?",
        month,
    )
    items_by_order = {}
    for item in items:
        items_by_order.setdefault(item['order_id'], []).append(item)
    return [(o, items_by_order.get(o['id'], [])) for o in orders]
```

These indexes match these queries:

```sql
CREATE INDEX idx_items_order_id ON items(order_id);
-- Expression index matching the current filter (SQLite 3.20+):
CREATE INDEX idx_orders_created_month ON orders(strftime('%m', created_at));
```

The `items(order_id)` index matters most. The month index helps less, because a month-only filter still matches about 1/12 of all orders across all years.

### What I'd recommend if the report should cover one month of one year

Pass the year and filter on a date range. Then the plain index you asked for works:

```python
def monthly_report(db, year, month):
    start = f"{year:04d}-{month:02d}-01"
    end = f"{year + (month == 12):04d}-{month % 12 + 1:02d}-01"
    orders = db.query(
        "SELECT * FROM orders WHERE created_at >= ? AND created_at < ?", start, end
    )
    items = db.query(
        "SELECT items.* FROM items JOIN orders ON orders.id = items.order_id "
        "WHERE orders.created_at >= ? AND orders.created_at < ?",
        start, end,
    )
    items_by_order = {}
    for item in items:
        items_by_order.setdefault(item['order_id'], []).append(item)
    return [(o, items_by_order.get(o['id'], [])) for o in orders]
```

```sql
CREATE INDEX idx_orders_created_at ON orders(created_at);
CREATE INDEX idx_items_order_id ON items(order_id);
```

This version changes the signature, so every caller has to pass the year. It also assumes `created_at` is stored as ISO text (`YYYY-MM-DD ...`). If it's stored as a Unix timestamp, the bounds need to be numbers instead.

I haven't run any of this. Which behavior do you want: all years, or one specific year? And how is `created_at` stored?
