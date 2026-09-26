The slowness is an **N+1 query problem**. `Author.query.all()` runs one query, and then each `a.books` access lazy-loads that author's books with another query. With 1,000 authors, that's 1,001 round trips to the database. It also loads every `Book` row into Python just to count them and take a max.

The database can do all of this in one aggregate query:

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
    out = [{"name": name, "books": count, "latest": latest} for name, count, latest in rows]
    return jsonify(out)
```

This keeps the same behavior:
- **Authors with no books still appear.** The `outerjoin` includes them, `count(Book.id)` counts only non-NULL rows so they get `0`, and `max` gives `None`, matching `max(dates, default=None)`.
- **`latest` is still a `date`.** SQLAlchemy types `func.max` from its argument, so `jsonify` serializes it the same way as before.
- **Row order.** The original had no `ORDER BY`, and neither does this one. If clients depend on a stable order, add `.order_by(Author.id)`.

**Also add an index on `book.author_id`.** Neither SQLAlchemy nor PostgreSQL automatically indexes foreign key columns, and without one the join scans the whole `book` table:

```python
author_id = db.Column(db.Integer, db.ForeignKey("author.id"), index=True)
```

That model change doesn't touch an existing production table. You need a migration (e.g. `CREATE INDEX ix_book_author_id ON book (author_id);`, or an Alembic/Flask-Migrate revision).

I can't run this here, so I haven't tested it. Before deploying, compare the old and new endpoint output on a copy of your data, including an author with zero books. If the page is still slow after this, the remaining cost is probably the size of the response itself, and pagination would be the next step.
