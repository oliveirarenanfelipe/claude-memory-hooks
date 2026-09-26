Two things in your model affect this script, so I've made it a dry run by default:

1. **`last_login` is NULL for users who never logged in.** A plain `last_login < cutoff` filter skips them, since NULL comparisons are never true. I treat a never-logged-in user as inactive if their account is more than a year old (`created_at < cutoff`).
2. **Deleting a user also deletes their orders.** This comes from `cascade="all, delete-orphan"`. If you need order history for accounting, refunds or tax records, you probably shouldn't hard-delete these users. Anonymizing them may be better (see the end). Also, the cascade only runs when you delete through `session.delete()`. A bulk `User.query.filter(...).delete()` bypasses it, and would either fail on the foreign key or leave orphaned orders. The script deletes one user at a time for this reason.

```python
# scripts/delete_inactive_users.py
"""
Delete users who haven't logged in for over a year.

Dry run (default):  python scripts/delete_inactive_users.py
Actually delete:    python scripts/delete_inactive_users.py --confirm
"""
import argparse
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, func, or_

from app import app  # adjust to your app / app factory, e.g. create_app()
from models import Order, User, db

BATCH_SIZE = 500


def inactive_users_query(cutoff):
    return User.query.filter(
        or_(
            User.last_login < cutoff,
            # Never logged in: judge by account age instead
            and_(User.last_login.is_(None), User.created_at < cutoff),
        )
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", action="store_true", help="actually delete")
    parser.add_argument("--days", type=int, default=365)
    args = parser.parse_args()

    # Assumes timestamps are stored as naive UTC
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=args.days)

    with app.app_context():
        query = inactive_users_query(cutoff)
        user_count = query.count()
        order_count = (
            db.session.query(func.count(Order.id))
            .filter(Order.user_id.in_(query.with_entities(User.id)))
            .scalar()
        )

        print(f"Cutoff: {cutoff:%Y-%m-%d %H:%M} UTC")
        print(f"Users to delete:  {user_count}")
        print(f"Orders to delete (cascade): {order_count}")

        if not args.confirm:
            for user in query.limit(20):
                print(f"  {user.id}\t{user.email}\tlast_login={user.last_login}")
            print("\nDry run - nothing deleted. Re-run with --confirm to delete.")
            return

        deleted = 0
        while True:
            batch = query.limit(BATCH_SIZE).all()
            if not batch:
                break
            for user in batch:
                db.session.delete(user)  # ORM delete so the orders cascade runs
            db.session.commit()
            deleted += len(batch)
            print(f"Deleted {deleted}/{user_count}")

        print("Done.")


if __name__ == "__main__":
    main()
```

Notes:
- **Back up the database before running with `--confirm`.** There's no undo.
- Each batch is committed on its own, so if the script is interrupted, earlier batches stay deleted. Re-running it just continues where it stopped.
- Change the `from app import app` line to match your project. If you use a factory, write `app = create_app()`.

If you do need to keep the orders, replace the delete with anonymization: set `email = None` (or `f"deleted-{user.id}@invalid"`) and clear any other personal fields. The orders then stay attached to a user row with no personal data. I can write that version if you want it.
