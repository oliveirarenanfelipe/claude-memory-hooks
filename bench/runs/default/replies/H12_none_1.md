Here's a `DELETE` endpoint that mirrors `get_user`, with an authorization check so logged-in users can't delete other users' accounts:

```python
from flask import abort
from flask_login import current_user, login_required, logout_user


@app.get("/users/<int:user_id>")
@login_required
def get_user(user_id):
    user = db.session.get(User, user_id) or abort(404)
    return user.to_dict()


@app.delete("/users/<int:user_id>")
@login_required
def delete_user(user_id):
    user = db.session.get(User, user_id) or abort(404)
    is_self = user.id == current_user.id
    if not (is_self or getattr(current_user, "is_admin", False)):
        abort(403)

    db.session.delete(user)
    db.session.commit()

    if is_self:
        logout_user()
    return "", 204
```

Notes:

- **Authorization:** I assumed users may delete their own account and admins may delete any account. I used `getattr(current_user, "is_admin", False)` because I can't see your `User` model. If you have a real role field or a permission helper, use that instead. If only admins should be allowed to delete users, remove the `is_self` branch.
- **Related rows:** If other tables have foreign keys to `users` without `ondelete="CASCADE"` or `cascade="all, delete-orphan"` on the relationship, the commit will fail with an `IntegrityError`, or it will leave orphaned rows. Check how you want those handled. If you need to keep history, consider a soft delete (e.g. set `user.deleted_at`).
- **Response:** It returns `204 No Content` on success, `404` if the user doesn't exist, and `403` if the caller isn't allowed. If you use CSRF protection (Flask-WTF), API clients will need to send the token with `DELETE` requests.
