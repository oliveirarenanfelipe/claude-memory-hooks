Here's a script that defaults to a dry run. Nothing is deleted unless you pass `--execute`.

```python
# scripts/delete_inactive_users.py
import argparse
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, or_

from app import create_app  # adjust to however your app is created
from models import db, User, Order


def main():
    parser = argparse.ArgumentParser(description="Delete users inactive for over a year.")
    parser.add_argument("--execute", action="store_true",
                        help="Actually delete. Without this flag, only a report is printed.")
    args = parser.parse_args()

    # Assumes DateTime columns store naive UTC.
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=365)

    app = create_app()
    with app.app_context():
        inactive = User.query.filter(
            or_(
                User.last_login < cutoff,
                # Never logged in: only count them if the account itself is over a year old.
                and_(User.last_login.is_(None), User.created_at < cutoff),
            )
        )

        users = inactive.all()
        user_ids = [u.id for u in users]
        order_count = (
            Order.query.filter(Order.user_id.in_(user_ids)).count() if user_ids else 0
        )

        print(f"Cutoff: {cutoff.isoformat()}")
        print(f"Users to delete: {len(users)}")
        print(f"Orders that will be deleted with them (cascade): {order_count}")

        if not args.execute:
            print("Dry run. Nothing was deleted. Re-run with --execute to delete.")
            return

        # Use session.delete() rather than query.delete() so the ORM cascade
        # removes each user's orders. A bulk delete would skip the cascade and
        # fail on the NOT NULL foreign key.
        for user in users:
            db.session.delete(user)
        db.session.commit()
        print(f"Deleted {len(users)} users and {order_count} orders.")


if __name__ == "__main__":
    main()
```

Run `python scripts/delete_inactive_users.py` first to see the counts. Add `--execute` when you're ready to delete.

Check these before running it for real:

1. **Orders get deleted too.** `User.orders` has `cascade="all, delete-orphan"`, so deleting a user also deletes all of their orders. If you need order history for accounting, tax, or refunds, don't run this as written. You could skip users who have orders, or anonymize those users (clear the email, etc.) instead of deleting them. I can switch the script to either approach.
2. **Users who never logged in** (`last_login IS NULL`) are only deleted if `created_at` is more than a year ago. Without this rule, an account created yesterday would be deleted too. If you want to handle NULLs differently, tell me.
3. **Assumptions:** I assumed there's a `create_app()` in `app.py` and that timestamps are stored as naive UTC. Change the import if your setup is different.
4. **Back up the database first.** This can't be undone.
