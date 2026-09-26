Two things in your models change what this script actually does, so I've made a default choice for each. Check them before running it for real:

1. **`last_login` is NULL for users who never logged in.** A plain `last_login < cutoff` filter skips those users entirely. I treat never-logged-in users as inactive if their account is more than a year old (`created_at < cutoff`). This keeps sign-ups from last week safe.
2. **Deleting a user also deletes their orders** because of `cascade="all, delete-orphan"`. If you need orders for accounting, tax, or refunds, you probably want to anonymize these users (for example, clear `email`) instead of deleting them. Say so and I'll switch the script to do that.

The script only prints what it would delete unless you pass `--execute`.

```python
# delete_inactive_users.py
import argparse
from datetime import datetime, timedelta

from sqlalchemy import and_, or_

from app import create_app  # adjust to your app factory / app import
from models import db, User, Order


def inactive_users_query(cutoff):
    return User.query.filter(
        or_(
            User.last_login < cutoff,
            and_(User.last_login.is_(None), User.created_at < cutoff),
        )
    )


def main():
    parser = argparse.ArgumentParser(description="Delete users inactive for over a year.")
    parser.add_argument("--execute", action="store_true", help="Actually delete (default is dry run).")
    parser.add_argument("--days", type=int, default=365)
    args = parser.parse_args()

    cutoff = datetime.utcnow() - timedelta(days=args.days)

    app = create_app()
    with app.app_context():
        query = inactive_users_query(cutoff)
        user_count = query.count()
        order_count = (
            Order.query.filter(Order.user_id.in_(query.with_entities(User.id))).count()
        )

        print(f"Cutoff: {cutoff.isoformat()} (UTC)")
        print(f"Users to delete: {user_count}")
        print(f"Orders that will be cascade-deleted: {order_count}")

        if not args.execute:
            for user in query.limit(20):
                print(f"  would delete id={user.id} email={user.email} last_login={user.last_login}")
            print("Dry run only. Re-run with --execute to delete.")
            return

        # Delete through the ORM (not query.delete()) so the Order cascade runs.
        deleted = 0
        while True:
            batch = inactive_users_query(cutoff).limit(500).all()
            if not batch:
                break
            for user in batch:
                db.session.delete(user)
            db.session.commit()
            deleted += len(batch)
            print(f"Deleted {deleted}/{user_count}")

        print("Done.")


if __name__ == "__main__":
    main()
```

Notes:
- **App import:** I assumed an app factory at `app.create_app`. Change that import to match your project.
- **Timezone:** The cutoff uses naive UTC (`datetime.utcnow()`). If your timestamps are stored in local time or as timezone-aware values, adjust the cutoff to match.
- **Why ORM delete:** A bulk `User.query.filter(...).delete()` would skip the ORM cascade. Your `user_id` foreign key has no `ON DELETE CASCADE`, so the bulk delete would either fail or leave orphaned orders.
- **Backups:** Take a database backup before running with `--execute`. This can't be undone.
