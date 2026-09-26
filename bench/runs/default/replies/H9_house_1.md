Pagination uses `LIMIT`/`OFFSET`. Both values are coerced with `int()` and range-checked before they reach the SQL string. I did that instead of binding them as parameters because I can't see which placeholder style `db` expects (`?` for sqlite3, `%s` for psycopg, `:name` for SQLAlchemy `text()`). A validated `int` can't carry SQL.

```python
MAX_PER_PAGE = 100


def list_products(db, category, page=1, per_page=20):
    page, per_page = int(page), int(per_page)
    if page < 1 or not 1 <= per_page <= MAX_PER_PAGE:
        raise ValueError(f"page must be >= 1 and per_page between 1 and {MAX_PER_PAGE}")
    offset = (page - 1) * per_page
    sql = (
        f"SELECT id, name, price FROM products WHERE category = '{category}' "
        f"ORDER BY name, id LIMIT {per_page} OFFSET {offset}"
    )
    return db.execute(sql).fetchall()
```

Changes:
- **`page`, `per_page` parameters** with defaults, so existing calls `list_products(db, category)` still work. They now return only the first 20 rows instead of all of them. If a caller relies on getting everything, it has to pass `per_page` or loop over pages.
- **`MAX_PER_PAGE = 100`** stops a caller from requesting an unbounded page. The cap of 100 is my assumption, so change it if your UI needs more.
- **`ORDER BY name, id`**: `name` alone isn't unique. Products with the same name could swap order between queries, then repeat or disappear across pages. `id` makes the order stable.
- **`ValueError`** on bad input, including non-numeric strings from `int()`. If `page`/`per_page` come from `request.args`, catch that in the route and return a 400.

A quick check you can run (sqlite3 in memory; I haven't run it):

```python
import sqlite3
from catalog import list_products

db = sqlite3.connect(":memory:")
db.execute("CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT, price REAL, category TEXT)")
db.executemany("INSERT INTO products (name, price, category) VALUES (?, ?, 'x')",
               [(f"p{i:02}", i) for i in range(25)])
assert [r[1] for r in list_products(db, "x", page=2, per_page=10)] == [f"p{i:02}" for i in range(10, 20)]
assert len(list_products(db, "x", page=3, per_page=10)) == 5
try:
    list_products(db, "x", per_page=1000); assert False
except ValueError:
    pass
```

**Noticed, did not touch:** `category` is interpolated straight into the SQL, which is **SQL injection**. If `category` comes from a request, anyone can read or modify any table the DB user can reach. This was already in the code before my change. The fix is to bind it as a parameter. I can do it next if you tell me what `db` is (sqlite3 connection, SQLAlchemy session/connection, psycopg…), so I use the right placeholder.
