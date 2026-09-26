Two things in your model change what "delete" means here, so I handled them explicitly:

1. **`last_login` can be NULL** (never logged in). A plain `last_login < cutoff` skips those users, because NULL comparisons are never true. The script treats a never-logged-in user as inactive if their account was **created** more than a year ago. That way someone who signed up yesterday isn't deleted.
2. **`orders` has `cascade="all, delete-orphan"`**, so deleting a user also deletes their orders. That is usually financial or audit data you want to keep. By default the script **skips users who have orders**. Pass `--include-users-with-orders` if you really want those gone too.

The script also does a **dry run by default** and only deletes when you pass `--confirm`.

```python
# scripts/delete_inactive_users.py
"""
Delete users who haven't logged in for over a year.

Usage:
    python scripts/delete_inactive_users.py                  # dry run, shows what would be deleted
    python scripts/delete_inactive_users.py --confirm        # actually delete
    python scripts/delete_inactive_users.py --confirm --include-users-with-orders
"""
import argparse
from datetime import datetime, timedelta

from sqlalchemy import and_, or_

from app import create_app  # adjust to however your app is created
from models import Order, User, db

BATCH_SIZE = 500


def inactive_users_query(cutoff, include_users_with_orders):
    query = User.query.filter(
        or_(
            User.last_login < cutoff,
            and_(User.last_login.is_(None), User.created_at < cutoff),
        )
    )
    if not include_users_with_orders:
        query = query.filter(~User.orders.any())
    return query


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", action="store_true", help="Actually delete (default is dry run)")
    parser.add_argument("--days", type=int, default=365, help="Inactivity threshold in days")
    parser.add_argument(
        "--include-users-with-orders",
        action="store_true",
        help="Also delete users who have orders (their orders are deleted via cascade)",
    )
    args = parser.parse_args()

    # Use datetime.now(timezone.utc) instead if your DateTime columns store aware UTC values.
    cutoff = datetime.utcnow() - timedelta(days=args.days)

    app = create_app()
    with app.app_context():
        query = inactive_users_query(cutoff, args.include_users_with_orders)
        total = query.count()
        order_count = (
            Order.query.filter(Order.user_id.in_(query.with_entities(User.id))).count()
            if args.include_users_with_orders
            else 0
        )

        print(f"Cutoff: {cutoff.isoformat()}")
        print(f"Users matched: {total}")
        if args.include_users_with_orders:
            print(f"Orders that will be cascade-deleted: {order_count}")

        if not args.confirm:
            for user in query.limit(20):
                print(f"  would delete: id={user.id} email={user.email} last_login={user.last_login}")
            if total > 20:
                print(f"  ... and {total - 20} more")
            print("Dry run only. Re-run with --confirm to delete.")
            return

        deleted = 0
        while True:
            # Re-query each batch; deleted rows drop out of the result set.
            batch = query.order_by(User.id).limit(BATCH_SIZE).all()
            if not batch:
                break
            for user in batch:
                # ORM delete (not query.delete()) so the orders cascade is honored.
                db.session.delete(user)
            db.session.commit()
            deleted += len(batch)
            print(f"Deleted {deleted}/{total}")

        print(f"Done. Deleted {deleted} users.")


if __name__ == "__main__":
    main()
```

Notes:
- I deliberately avoided `query.delete()` (a bulk delete). It bypasses the ORM cascade, so it would either fail on the `orders.user_id` foreign key or leave orphaned orders, depending on your database.
- Each batch commits separately, so an interruption leaves a partial but consistent result. Re-running the script picks up where it left off.
- Adjust `from app import create_app` to match your project's app setup.
- Take a database backup before the first `--confirm` run. This can't be undone.

If you'd rather keep inactive accounts' history, consider anonymizing them instead of deleting: null out `email` and set a `deleted_at` flag. I can sketch that version if you want.
