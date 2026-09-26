This permanently deletes rows, and **it also deletes each user's orders** because of `cascade="all, delete-orphan"` on `User.orders`. If you need that order history for accounting, refunds, or tax, check before running it for real. So the script **defaults to a dry run** and only deletes when you pass `--execute`.

```python
# scripts/delete_inactive_users.py
"""Delete users who haven't logged in for over a year.

Dry run by default. Pass --execute to actually delete.
NOTE: deleting a user also deletes their orders (cascade on User.orders).
"""
import argparse
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, func, or_

from app import create_app  # adjust to your app factory / app object
from models import Order, User, db


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=365)
    parser.add_argument("--execute", action="store_true", help="actually delete (default: dry run)")
    args = parser.parse_args()

    # Assumes timestamps are stored as naive UTC.
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=args.days)

    inactive = or_(
        User.last_login < cutoff,
        # Never logged in: judge by account age so brand-new signups are kept.
        and_(User.last_login.is_(None), User.created_at < cutoff),
    )

    app = create_app()
    with app.app_context():
        users = User.query.filter(inactive).all()
        order_count = (
            db.session.query(func.count(Order.id))
            .filter(Order.user_id.in_([u.id for u in users]))
            .scalar()
        ) if users else 0

        print(f"Cutoff: {cutoff.isoformat()} UTC")
        print(f"Users to delete: {len(users)}")
        print(f"Orders deleted with them (cascade): {order_count}")

        if not args.execute:
            print("Dry run, nothing deleted. Re-run with --execute to delete.")
            return

        # ORM delete per object so the Order cascade runs; a bulk
        # query.delete() would skip it and fail on the NOT NULL user_id FK.
        for user in users:
            db.session.delete(user)
        db.session.commit()  # single transaction: all or nothing
        print(f"Deleted {len(users)} users and {order_count} orders.")


if __name__ == "__main__":
    main()
```

Usage:

```
python scripts/delete_inactive_users.py            # dry run, shows counts
python scripts/delete_inactive_users.py --execute  # deletes
```

Assumptions I made, so you can correct them:
- **Never-logged-in users** (`last_login IS NULL`) count as inactive if their account is more than a year old. Without that rule they would never match. Without the `created_at` check, yesterday's signups would be deleted.
- `from app import create_app` is a guess, because I haven't seen your app entry point. Point it at your factory or `app` object.
- Timestamps are naive UTC.

I haven't run this. I've only reviewed it against `models.py`. Take a database backup before the first `--execute`, and read the dry-run counts first. If the order count isn't 0, decide whether to keep those orders. One option is to skip users who have orders, or anonymize them instead of deleting.
