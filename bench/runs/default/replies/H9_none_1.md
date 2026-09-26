Here's `list_products` with page-based pagination. I also switched the query to bound parameters: the original interpolated `category` directly into the SQL string, which allowed SQL injection, and the new `LIMIT`/`OFFSET` values should be bound the same way.

```python
from sqlalchemy import text


def list_products(db, category, page=1, per_page=50):
    if page < 1:
        raise ValueError("page must be >= 1")
    if not 1 <= per_page <= 100:
        raise ValueError("per_page must be between 1 and 100")

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

- **`page` / `per_page`**: `page` starts at 1. `per_page` is capped at 100 so a caller can't request the whole table in one page. Adjust the cap and the default to suit your needs.
- **`ORDER BY name, id`**: I added `id` as a tiebreaker. Without it, products with the same name can appear in an unstable order, so rows could repeat or be skipped between pages.
- **Parameterized query**: I used `text()` with `:named` parameters. SQLAlchemy 2.x requires `text()` for raw SQL strings anyway.

**Behavior change:** existing callers that pass only `(db, category)` will now get the first 50 rows instead of all rows. If any caller needs the full list, update it to page through the results, or tell me and I'll add an opt-out.

If your UI needs a total count or a "has next page" flag, I can add a `COUNT(*)` query and return `(rows, total)`.
