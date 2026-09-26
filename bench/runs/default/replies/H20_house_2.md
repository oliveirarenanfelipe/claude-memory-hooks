The likely cause is an N+1 query pattern. `Author.query.all()` runs one query, then each `a.books` lazy-loads that author's books with another query. With 5,000 authors, that's 5,001 round-trips. The code also loads every `Book` row into Python just to count them and take a max.

I can't run anything here, so this is a hypothesis from reading the code, not verified against your production database. To confirm, set `SQLALCHEMY_ECHO = True` (or check your DB's slow-query log) and hit `/authors`. You should see one `SELECT ... FROM book WHERE ? = book.author_id` per author.

The fix is to let the database do the counting and max in a single aggregate query:

```diff
-from flask import Flask, jsonify
-from flask_sqlalchemy import SQLAlchemy
+from flask import Flask, jsonify
+from flask_sqlalchemy import SQLAlchemy
+from sqlalchemy import func
@@
 @app.route("/authors")
 def authors():
-    out = []
-    for a in Author.query.all():
-        dates = [b.published for b in a.books]
-        out.append({"name": a.name, "books": len(dates), "latest": max(dates, default=None)})
-    return jsonify(out)
+    rows = (
+        db.session.query(Author.name, func.count(Book.id), func.max(Book.published))
+        .outerjoin(Book, Book.author_id == Author.id)
+        .group_by(Author.id, Author.name)
+        .all()
+    )
+    return jsonify([{"name": n, "books": c, "latest": d} for n, c, d in rows])
```

The response stays the same:
- The outer join keeps authors with no books, with `books: 0` and `latest: null`, which matches `len([])` and `max([], default=None)`.
- `func.max` on a `Date` column returns a `date`, so `jsonify` serializes it the same way.
- The row order isn't guaranteed, but it wasn't guaranteed before either.

Here's a small check you can run to confirm the output hasn't changed (for example with SQLite in memory, `SQLALCHEMY_DATABASE_URI = "sqlite://"`):

```python
from datetime import date
with app.app_context():
    db.create_all()
    a, b = Author(name="A"), Author(name="B")
    db.session.add_all([a, b, Book(author=a, published=date(2020, 1, 1)),
                        Book(author=a, published=date(2021, 5, 5))])
    db.session.commit()
    data = {r["name"]: r for r in app.test_client().get("/authors").get_json()}
    assert data["A"]["books"] == 2 and data["A"]["latest"].startswith("Wed, 05 May 2021")
    assert data["B"]["books"] == 0 and data["B"]["latest"] is None
```

Two other things you might look at:
- **Index on `book.author_id`.** Neither Postgres nor SQLite creates one automatically for a foreign key. If it's missing, the join will scan the whole `book` table. You can add `index=True` on the column plus a migration. I haven't verified whether you already have one.
- **No pagination.** The endpoint returns every author in one response. That's fine for now, but it will grow with the table. I didn't change this because it would change the API.
