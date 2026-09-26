Here's `list_products` with offset-based pagination:

```python
from sqlalchemy import text


def list_products(db, category, page=1, per_page=20):
    page = max(int(page), 1)
    per_page = min(max(int(per_page), 1), 100)

    sql = text(
        "SELECT id, name, price FROM products "
        "WHERE category = :category "
        "ORDER BY name, id "
        "LIMIT :limit OFFSET :offset"
    )
    return db.execute(
        sql,
        {"category": category, "limit": per_page, "offset": (page - 1) * per_page},
    ).fetchall()
```

What changed:

- **Pagination:** I added `page` (1-based) and `per_page` parameters. They are converted to `LIMIT`/`OFFSET`. `per_page` is capped at 100 so a caller can't request the whole table in one go. Existing calls like `list_products(db, category)` still work and return the first 20 rows.
- **Stable ordering:** `ORDER BY name, id` adds a tiebreaker. Without it, products that share a name could shift between pages or appear on two pages.
- **SQL injection fix:** the original query put `category` into the SQL with an f-string. Anyone who controls `category` could run arbitrary SQL, for example with `' OR '1'='1`. I switched to bound parameters with `text()`. The new `limit`/`offset` values are bound the same way.

Two things to check:

- If other callers depended on getting *all* products in a category, they will now get only the first page. Pass a larger `per_page` or loop over pages in those places.
- If the frontend needs page counts, you'll need a total. Run a separate `SELECT COUNT(*) FROM products WHERE category = :category`. I can add that and return `(rows, total)` if you want.
