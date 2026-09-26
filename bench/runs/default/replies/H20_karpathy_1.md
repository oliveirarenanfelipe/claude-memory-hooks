The slowdown is an N+1 query problem. `Author.query.all()` runs one query, and then each `a.books` access lazy-loads that author's books in a separate query. With 1,000 authors, that's 1,001 round-trips, and every `Book` row gets loaded into Python just to be counted and compared.

The fix is to let the database do the counting and max in a single aggregate query:

```python
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

...

@app.route("/authors")
def authors():
    rows = (
        db.session.query(Author.name, func.count(Book.id), func.max(Book.published))
        .outerjoin(Book, Book.author_id == Author.id)
        .group_by(Author.id, Author.name)
        .all()
    )
    return jsonify([{"name": name, "books": count, "latest": latest} for name, count, latest in rows])
```

The response stays the same:
- **Authors with no books** are still included, with `books: 0` and `latest: null`. That's why it uses `outerjoin` and `count(Book.id)` rather than `count(*)`.
- **`latest`** is still a `date` object, because `func.max` keeps the column's `Date` type, so `jsonify` serializes it as before.
- **Row order** is unspecified, as it was originally. If clients depend on an order, add `.order_by(Author.id)`.

Two other things are worth checking in production:
1. **Index on `book.author_id`.** `ForeignKey` doesn't create an index on Postgres or SQLite. Without one, the join scans the whole `book` table. To add it, change the column to `db.Column(db.Integer, db.ForeignKey("author.id"), index=True)` and create the index with a migration, e.g. `CREATE INDEX ix_book_author_id ON book (author_id);`.
2. **Pagination.** Even after this fix, the endpoint returns every author on every request. If the table is large, a `limit`/`offset` or cursor parameter would help more than any query tweak.

I haven't been able to run this. Before deploying, compare the new endpoint's output with the old one on a copy of your data.
