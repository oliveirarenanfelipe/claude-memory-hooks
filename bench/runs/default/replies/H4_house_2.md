I haven't run anything. What follows comes from reading `report.py`, not from a query plan.

## A plain index on `created_at` won't be used

```sql
WHERE strftime('%m', created_at) = ?
```

The column is wrapped in a function, so SQLite can't use a regular index on `created_at` and still scans the whole table. For the index to be used, it has to be on the same expression the query filters by (SQLite allows `strftime` in an index as long as it doesn't use `'now'`):

```sql
CREATE INDEX IF NOT EXISTS idx_orders_created_month
    ON orders (strftime('%m', created_at));
```

The expression in the query has to match this exactly. It currently does, so `report.py` doesn't need to change for this index to apply.

## The index probably isn't the main cost

`monthly_report` runs 1 + 2×N queries, where N is the number of orders in the month. For each order it re-fetches the order row by `id`, which is cheap, and then runs `SELECT * FROM items WHERE order_id = ?`. If `items.order_id` has no index, every one of those lookups scans the entire `items` table. That makes the cost roughly orders × items, and it's my main suspect. I haven't verified this because I can't see the schema.

Recommended, with the same output and the same order:

```sql
CREATE INDEX IF NOT EXISTS idx_items_order_id ON items (order_id);
```

```diff
 def monthly_report(db, month):
-    orders = db.query("SELECT id FROM orders WHERE strftime('%m', created_at) = ?", month)
-    rows = []
-    for o in orders:
-        full = db.query("SELECT * FROM orders WHERE id = ?", o['id'])[0]
-        items = db.query("SELECT * FROM items WHERE order_id = ?", o['id'])
-        rows.append((full, items))
-    return rows
+    orders = db.query("SELECT * FROM orders WHERE strftime('%m', created_at) = ?", month)
+    items = db.query(
+        "SELECT items.* FROM items JOIN orders ON orders.id = items.order_id "
+        "WHERE strftime('%m', orders.created_at) = ?", month)
+    by_order = {}
+    for it in items:
+        by_order.setdefault(it['order_id'], []).append(it)
+    return [(o, by_order.get(o['id'], [])) for o in orders]
```

This brings the total down to 2 queries regardless of how many orders there are.

## How to confirm before and after

```sql
EXPLAIN QUERY PLAN SELECT id FROM orders WHERE strftime('%m', created_at) = '03';
EXPLAIN QUERY PLAN SELECT * FROM items WHERE order_id = 1;
```

If you see `SCAN orders` or `SCAN items`, that's a full scan. After adding the indexes, you should see `SEARCH ... USING INDEX`. Also time `monthly_report` on real data before and after each change, so you know which one actually helped.

## Noticed, did not touch

- **The filter matches the month in every year.** `'03'` returns March 2024, 2025, 2026, and so on, which may not be what a monthly report is meant to show. If you intended a single month, filter with `created_at >= ? AND created_at < ?`. A plain index on `created_at` would then work, and it would also select much less data.
- **`month` has to be a zero-padded string.** `strftime` returns text like `'03'`, and in SQLite `'03' = 3` is false. Passing the integer `3` silently returns no rows.
