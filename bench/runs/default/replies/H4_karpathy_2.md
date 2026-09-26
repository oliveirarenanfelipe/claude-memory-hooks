An index on `orders.created_at` won't speed up this query, because the `WHERE` clause wraps the column in a function:

```sql
WHERE strftime('%m', created_at) = ?
```

SQLite can't use a plain index on `created_at` for that expression, so it still scans the whole table. That filter also isn't the main cost. The function runs **1 + 2N queries** for N orders: one query per order to re-fetch the row it already found, and one per order for its items. If `items.order_id` isn't indexed, each of those item lookups is also a full scan of `items`.

## What I'd change

**1. Remove the N+1 queries** (`report.py`). This makes two queries total and returns the same `(order_row, items)` tuples:

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

**2. Add the index the item lookup needs:**

```sql
CREATE INDEX IF NOT EXISTS ix_items_order_id ON items(order_id);
```

**3. The `created_at` index you asked for.** Here it is, but it only helps if the filter becomes a range on the raw column (see the question below):

```sql
CREATE INDEX IF NOT EXISTS ix_orders_created_at ON orders(created_at);
```

## One thing to confirm

`strftime('%m', created_at) = ?` matches that month in **every year**, so "March" returns March 2024, 2025, 2026, and so on. Is that intended?

- **If you meant one specific month** (probably what a monthly report wants), I'd switch the filter to `created_at >= ? AND created_at < ?` (e.g. `'2026-03-01'` to `'2026-04-01'`). That uses the `created_at` index directly. It does change the function's signature and behavior, so I haven't done it without checking.
- **If all-years is intended**, the `created_at` index won't help. Changes 1 and 2 are the real fix.

I couldn't run anything here, so this is untested. I also don't see a migration setup, so the `CREATE INDEX` statements need to go wherever your schema lives.
