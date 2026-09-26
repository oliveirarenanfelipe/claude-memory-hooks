I haven't run any of this. I only had this one function to work from.

```python
from sqlalchemy import text

MAX_PER_PAGE = 100


def list_products(db, category, page=1, per_page=20):
    if page < 1 or not 1 <= per_page <= MAX_PER_PAGE:
        raise ValueError(f"page must be >= 1 and per_page between 1 and {MAX_PER_PAGE}")
    sql = text(
        "SELECT id, name, price FROM products WHERE category = :category "
        "ORDER BY name, id LIMIT :limit OFFSET :offset"
    )
    return db.execute(
        sql, {"category": category, "limit": per_page, "offset": (page - 1) * per_page}
    ).fetchall()
```

**What changed beyond `LIMIT`/`OFFSET`, and why:**

- **Bound parameters instead of the f-string.** The old query put `category` straight into the SQL, which allows SQL injection. Adding `page` and `per_page` the same way would have added two more injection points. Since I was rewriting this statement anyway, all three values are now bound parameters.
- **`ORDER BY name, id`.** If two products share a name, the database can return them in any order. Across pages, that means a row can be repeated or skipped. Adding `id` makes the order stable.
- **Limits on `page` and `per_page`.** These values usually come from query-string arguments. Without a cap, a caller could ask for `per_page=1000000` and get the whole table back. The cap is 100, set in `MAX_PER_PAGE`.

**Assumptions:**

- `db` is a SQLAlchemy `Session` or `Connection`, so I used `text()`. If it's actually a raw `sqlite3` connection, use `?` placeholders and a tuple instead.
- **Behavior change:** callers that pass no arguments now get only the first 20 rows, not the whole list. I couldn't see the callers, so check them. Any that need the full list must pass explicit arguments or loop over pages.
- A route passing `request.args` should convert them with `type=int` and turn the `ValueError` into a 400 response.

**Check** (not run). This uses in-memory SQLite and duplicate names to exercise the tiebreaker:

```python
from sqlalchemy import create_engine, text
from catalog import list_products

def test_pagination_is_stable_and_injection_safe():
    engine = create_engine("sqlite://")
    with engine.connect() as db:
        db.execute(text("CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT, price REAL, category TEXT)"))
        for i in range(5):
            db.execute(text("INSERT INTO products (name, price, category) VALUES ('same', 1, 'a')"))
        p1 = list_products(db, "a", page=1, per_page=2)
        p2 = list_products(db, "a", page=2, per_page=2)
        p3 = list_products(db, "a", page=3, per_page=2)
        ids = [r.id for r in p1 + p2 + p3]
        assert ids == [1, 2, 3, 4, 5]
        assert list_products(db, "a' OR '1'='1") == []
```
