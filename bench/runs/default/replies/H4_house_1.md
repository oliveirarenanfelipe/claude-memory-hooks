A plain index on `orders.created_at` would **not be used** by this query. The `WHERE` clause wraps the column in `strftime('%m', created_at)`, and SQLite can only use an index when the column appears bare. For this query, that index would take up space and slow writes without speeding anything up.

What matches the query as written is an **expression index** on the same expression. SQLite supports this in 3.9+, and allows date functions in index expressions as long as they don't use `'now'`:

```sql
CREATE INDEX IF NOT EXISTS idx_orders_created_month
    ON orders (strftime('%m', created_at));
```

The expression in the index must match the query's text exactly (`strftime('%m', created_at)`), so `report.py` stays unchanged. I don't see any migration setup in what you shared, so this is plain SQL. Put it wherever your schema changes go.

**Not verified, I can't run anything here.** To confirm the index is used, run:

```sql
EXPLAIN QUERY PLAN
SELECT id FROM orders WHERE strftime('%m', created_at) = '03';
```

You should see `SEARCH orders USING INDEX idx_orders_created_month` instead of `SCAN orders`.

**Why this may not fix the slowness:** a month filter matches about 1/12 of all rows, so the index alone helps only moderately. The bigger cost is likely the loop. It runs 2 extra queries per order: it re-fetches the order it just selected, then fetches its items. That's 1 + 2N queries. This is a hypothesis; timing the first query against the whole function would settle it. If it holds, the fix is two queries total: `SELECT *` in the first query, then load items with `WHERE order_id IN (...)` and group them in Python. I can write that if you want.

**Noticed, did not touch:** `strftime('%m', ...)` matches that month in **every year**. "March" returns March 2024, 2025 and 2026 together. If the report is meant to cover one year's month, that's a correctness bug, and fixing it would change the result. If it is a bug, the better fix is to pass year + month and filter on a range (`created_at >= ? AND created_at < ?`). A plain index on `created_at` would then work, and would be more selective than the expression index.
