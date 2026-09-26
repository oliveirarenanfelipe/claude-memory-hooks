Deleting users is irreversible, and because of `cascade="all, delete-orphan"` it **also deletes all of their orders**. So the script defaults to a dry run that shows what would go, and only deletes when you pass `--execute`.

```python
# delete_inactive_users.py
"""Delete users who haven't logged in for over a year.

Dry run by default. Pass --execute to actually delete.
Users who never logged in (last_login IS NULL) count as inactive
only if their account is older than the cutoff.
"""
import argparse
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, func, or_

from app import create_app  # adjust to however your app is created
from models import Order, User, db


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="actually delete (default: dry run)")
    parser.add_argument("--days", type=int, default=365)
    args = parser.parse_args()

    # Columns are naive DateTime; assumes they're stored in UTC.
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=args.days)

    inactive = or_(
        User.last_login < cutoff,
        and_(User.last_login.is_(None), User.created_at < cutoff),
    )

    app = create_app()
    with app.app_context():
        users = User.query.filter(inactive).all()
        order_count = (
            db.session.query(func.count(Order.id))
            .join(User)
            .filter(inactive)
            .scalar()
        )

        print(f"Cutoff: {cutoff:%Y-%m-%d %H:%M} UTC")
        print(f"{len(users)} users match, with {order_count} orders that would be cascade-deleted.")
        for u in users:
            print(f"  id={u.id} email={u.email} last_login={u.last_login} created_at={u.created_at}")

        if not args.execute:
            print("Dry run: nothing deleted. Re-run with --execute to delete.")
            return

        # session.delete (not a bulk query.delete) so the ORM cascade to orders runs.
        for u in users:
            db.session.delete(u)
        db.session.commit()
        print(f"Deleted {len(users)} users and {order_count} orders.")


if __name__ == "__main__":
    main()
```

Usage:
```
python delete_inactive_users.py            # preview
python delete_inactive_users.py --execute  # delete
```

A few things to decide before running it for real:

- **Orders get deleted with the users.** If orders are financial or accounting records you have to keep, don't hard-delete. Either skip users who have orders (add `~User.orders.any()` to the filter) or anonymize them instead, for example by setting `email = None`.
- **Never-logged-in users:** I treated `last_login IS NULL` as inactive only if `created_at` is more than a year old. That way someone who signed up yesterday isn't deleted.
- **`from app import create_app`** is a guess. I haven't seen how your app is created, so point that import at your real factory or app object.
- **Back up the database first.** There's no undo. Everything is committed in one transaction, so a failure partway through rolls back cleanly, but a successful run is permanent.

Not verified: I haven't run this against your database. Do a dry run first and check the list before using `--execute`.
