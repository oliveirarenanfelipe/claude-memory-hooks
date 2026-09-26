Here's the index, but it won't speed up this query on its own:

```sql
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);
```

**Why it won't help as written:** `WHERE strftime('%m', created_at) = ?` wraps the column in a function, so SQLite can't use an index on `created_at`. It still scans every row in `orders`.

**The bigger cost is the loop.** For N matching orders, the function runs 2N+1 queries. It re-fetches each order it already selected, then runs one `items` query per order. Unless `items.order_id` is indexed, each of those per-order queries is a full scan of `items`.

Here's a version that does the same work in 2 queries and returns the same `(order, items)` shape:

```python
from collections import defaultdict


def monthly_report(db, month):
    orders = db.query("SELECT * FROM orders WHERE strftime('%m', created_at) = ?", month)
    items = db.query(
        "SELECT items.* FROM items JOIN orders ON orders.id = items.order_id "
        "WHERE strftime('%m', orders.created_at) = ?",
        month,
    )
    items_by_order = defaultdict(list)
    for item in items:
        items_by_order[item['order_id']].append(item)
    return [(o, items_by_order[o['id']]) for o in orders]
```

Add this index too, because the join depends on it:

```sql
CREATE INDEX IF NOT EXISTS idx_items_order_id ON items(order_id);
```

**Possible bug:** `strftime('%m', ...)` matches the month in *every* year, so `'03'` returns March 2024, March 2025, March 2026, and so on. If you want one specific month, pass a year as well and use a range filter. That form can use `idx_orders_created_at`, assuming `created_at` is stored as ISO-8601 text:

```sql
WHERE created_at >= '2026-03-01' AND created_at < '2026-04-01'
```

That changes the function's signature and results, so I haven't made that change. Let me know if the report should cover a single year-month and I'll update it.
