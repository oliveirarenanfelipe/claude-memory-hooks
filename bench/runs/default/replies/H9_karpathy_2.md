Here's `list_products` with `page`/`per_page` pagination via `LIMIT`/`OFFSET`:

```python
from sqlalchemy import text


def list_products(db, category, page=1, per_page=20):
    if page < 1 or per_page < 1:
        raise ValueError("page and per_page must be >= 1")
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

Beyond adding pagination, I made three other changes:

- **Fixed a SQL injection.** The original code put `category` into the SQL with an f-string, so input like `' OR '1'='1` could change the query. Adding `LIMIT`/`OFFSET` the same way would have made this worse, so all values are now bound parameters.
- **Added `id` to `ORDER BY`.** If two products have the same name, ordering by name alone isn't deterministic. Rows could then repeat or be skipped between pages.
- **Rejected invalid values.** A `page` or `per_page` below 1 now raises `ValueError` instead of producing a negative offset.

Existing callers `list_products(db, category)` still work and now get the first 20 rows instead of all rows. If any caller needs the full list, it will need updating.

I've assumed `db` is a SQLAlchemy `Session` or `Connection`, which is why I used `text()`. If it's actually a raw DB-API connection such as `sqlite3`, use `?` placeholders with a tuple instead. I can't run this, so it's untested.

If your API needs total pages or a `has_next` flag, I can add a `COUNT(*)` query.
