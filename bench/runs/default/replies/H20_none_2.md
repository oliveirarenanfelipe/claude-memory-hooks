The slowdown is an N+1 query problem. `Author.query.all()` runs one query, and then each `a.books` lazy-loads that author's books in a separate query. With 1,000 authors that's 1,001 round trips, and every `Book` row gets turned into an object just so we can count them and take a max.

The database can do the counting and max in a single query:

```python
from sqlalchemy import func


@app.route("/authors")
def authors():
    rows = (
        db.session.query(
            Author.name,
            func.count(Book.id),
            func.max(Book.published),
        )
        .outerjoin(Book, Book.author_id == Author.id)
        .group_by(Author.id, Author.name)
        .all()
    )
    return jsonify([
        {"name": name, "books": count, "latest": latest}
        for name, count, latest in rows
    ])
```

This keeps the response the same:
- The outer join keeps authors with no books. `count(Book.id)` ignores the NULLs, so they get `0`, and `max` gives `None`, as before.
- `func.max` takes its result type from `Book.published`, so `latest` is still a `date` and `jsonify` formats it the same way.
- The original code didn't specify an order, and neither does this one. If clients depend on an order, add `.order_by(Author.id)`.

**Also add an index on `book.author_id`.** `ForeignKey` doesn't create one, and PostgreSQL and SQLite don't add one for you. Without it, the join has to scan the whole `book` table:

```python
author_id = db.Column(db.Integer, db.ForeignKey("author.id"), index=True)
```

If the table already exists in production, `index=True` won't change it. You'll need a migration, for example Alembic's `op.create_index("ix_book_author_id", "book", ["author_id"])`, or a `CREATE INDEX` run by hand.

I haven't been able to run this, so check the output against the old endpoint on a copy of the data before deploying. If the page is still slow afterwards, the next thing to look at is how many authors it returns. Returning every row in one response will eventually need pagination.
