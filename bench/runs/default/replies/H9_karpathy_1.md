Here's `list_products` with `page`/`per_page` pagination:

```python
from sqlalchemy import text


def list_products(db, category, page=1, per_page=20):
    if page < 1 or per_page < 1:
        raise ValueError("page and per_page must be positive")
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

Beyond the pagination itself, I made two other changes:

- **Fixed a SQL injection.** The original code put `category` straight into the SQL string with an f-string. If `category` comes from request input, someone could run arbitrary SQL. I had to rewrite the query anyway to add `LIMIT`/`OFFSET`, so it now uses bound parameters.
- **Added `id` as a tiebreaker in `ORDER BY`.** If two products have the same name, sorting by `name` alone has no fixed order. That can make rows repeat or disappear between pages.

Existing callers still work because `page=1, per_page=20` are the defaults. That does mean they now get at most 20 rows instead of all of them. If some caller needs the full list, give it a larger `per_page` or tell me and I'll make pagination opt-in.

I've assumed `db` is a SQLAlchemy `Session` or `Connection`, which is why the query uses `text()`. If it's actually a raw DB-API connection such as `sqlite3`, drop `text()` and use that driver's placeholder style (e.g. `?` or `%s`).
