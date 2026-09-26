The slowdown is an **N+1 query**: `Author.query.all()` runs one query, then each `a.books` lazy-loads that author's books in a separate query. With 1,000 authors that's 1,001 round-trips, and every `Book` row is loaded into Python just to count it and take a max.

The fix is to have the database do the aggregation in a single query:

```python
from sqlalchemy import func


@app.route("/authors")
def authors():
    rows = (
        db.session.query(
            Author.name,
            func.count(Book.id).label("books"),
            func.max(Book.published).label("latest"),
        )
        .outerjoin(Book, Book.author_id == Author.id)
        .group_by(Author.id, Author.name)
        .all()
    )
    return jsonify([{"name": r.name, "books": r.books, "latest": r.latest} for r in rows])
```

The response should be the same as before:
- The `outerjoin` keeps authors with no books. `count(Book.id)` gives them `0` and `max` gives `None`, which matches `len([])` and `max([], default=None)`.
- `func.max` takes its return type from `Book.published`, so `latest` is still a `date` and `jsonify` serializes it the same way.
- As before, the row order is whatever the database returns. Add `.order_by(Author.id)` if clients depend on a stable order.

**Add an index on `book.author_id`.** SQLAlchemy doesn't create one for a `ForeignKey`, and neither do Postgres or SQLite. Without it, the join has to scan the whole `book` table:

```python
author_id = db.Column(db.Integer, db.ForeignKey("author.id"), index=True)
```

On an existing production database this needs a migration (e.g. `flask db migrate` with Flask-Migrate) or a manual `CREATE INDEX ix_book_author_id ON book (author_id);`. On Postgres, use `CREATE INDEX CONCURRENTLY` so the table isn't locked while the index builds.

**If it's still slow** after this, the likely cause is the response size, since the endpoint returns every author on every request. Paginating with `.limit()`/`.offset()` or keyset pagination on `Author.id` would fix that, but it changes the API contract, so I haven't done it here.

I couldn't run this. Before deploying, compare the old and new JSON output on a copy of your data.
