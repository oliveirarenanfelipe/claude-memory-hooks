Here's a `DELETE` endpoint that follows the style of `get_user`. It does one thing `get_user` doesn't: an **authorization check**. With only `@login_required`, any logged-in user could delete any other user.

```python
from flask import abort
from flask_login import current_user, login_required, logout_user


@app.delete("/users/<int:user_id>")
@login_required
def delete_user(user_id):
    user = db.session.get(User, user_id) or abort(404)
    if user.id != current_user.id:
        abort(403)
    db.session.delete(user)
    db.session.commit()
    logout_user()
    return "", 204
```

**Assumptions to check:**

- **Who may delete:** I only let users delete their own account, since I can't see any role or admin field on `User`. If you have one (say `current_user.is_admin`), change the check to `if user.id != current_user.id and not current_user.is_admin:`. Then call `logout_user()` only when `user.id == current_user.id`.
- **Related rows:** `db.session.delete(user)` will fail with an integrity error, or leave orphaned rows, if other tables reference `users` without `cascade="all, delete-orphan"` or `ondelete="CASCADE"`. If users own posts, orders, and so on, decide whether those should be deleted with the user or blocked. Soft-deleting (e.g. setting `is_active = False` or `deleted_at`) is the safer choice if you need to keep history.
- **CSRF:** If this app uses cookie sessions from a browser, make sure CSRF protection (e.g. Flask-WTF's `CSRFProtect`) covers this route. Otherwise a malicious page could trigger the delete.
