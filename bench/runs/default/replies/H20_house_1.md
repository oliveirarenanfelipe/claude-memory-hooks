The likely cause is an **N+1 query pattern**. This is read from the code, not measured, since I can't run anything or see production. `Author.query.all()` runs one query. Then each `a.books` access lazy-loads that author's books in a separate query. With 5,000 authors, that's 5,001 round-trips, and every `Book` row is loaded into Python only to be counted and compared.

The fix is to let the database do the count and max in one grouped query:

```diff
+from sqlalchemy import func
 from flask import Flask, jsonify
 from flask_sqlalchemy import SQLAlchemy
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
+    return jsonify([{"name": n, "books": c, "latest": l} for n, c, l in rows])
```

The response should stay the same:
- The `outerjoin` keeps authors with no books. For them, `count(Book.id)` is `0` and `max` is `NULL`, which becomes `None`. This matches `len([])` and `max([], default=None)`.
- `func.max` keeps the `Date` column type, so `latest` is still a `date` and `jsonify` serializes it as before.
- Row order was never guaranteed before and still isn't. If clients rely on order, add `.order_by(Author.id)`.

I haven't run this, so I haven't verified that it's equivalent or faster. This test compares the new output against the old logic:

```python
def test_authors_matches_old_logic(client):
    expected = [
        {"name": a.name, "books": len(a.books),
         "latest": max((b.published for b in a.books), default=None)}
        for a in Author.query.all()
    ]
    expected = app.json.loads(app.json.dumps(expected))  # same serialization as jsonify
    key = lambda d: d["name"]
    assert sorted(client.get("/authors").get_json(), key=key) == sorted(expected, key=key)
```

Seed it with at least one author with no books and one with several. To confirm the speedup in production, compare the endpoint's query count or latency before and after the deploy.

**Noticed, did not touch:**
- `book.author_id` has no index declared, and neither SQLAlchemy nor Postgres creates one for foreign keys automatically. On a large `book` table, the join will be much faster with `index=True` plus a migration. Check your actual schema first; that's a separate change.
- The endpoint returns every author with no pagination. If the table keeps growing, the response size will eventually become the bottleneck, even with a single query.
