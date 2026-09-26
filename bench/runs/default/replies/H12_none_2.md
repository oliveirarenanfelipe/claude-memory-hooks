Here's a `DELETE` endpoint that follows the same pattern as `get_user`. It also adds an authorization check: `@login_required` alone would let any logged-in user delete any account.

```python
from flask_login import current_user, logout_user


@app.delete("/users/<int:user_id>")
@login_required
def delete_user(user_id):
    user = db.session.get(User, user_id) or abort(404)
    if user.id != current_user.id and not current_user.is_admin:
        abort(403)
    db.session.delete(user)
    db.session.commit()
    if user.id == current_user.id:
        logout_user()
    return "", 204
```

Notes:

- **`is_admin` is an assumption.** I don't know how your `User` model marks admins. Replace `current_user.is_admin` with your real role check. If only admins should delete accounts, remove the self-delete branch.
- **Related rows:** If other tables have foreign keys to `users`, the delete will fail with an `IntegrityError` or leave orphaned rows. Which one depends on your relationships' `cascade` and `ondelete` settings. Check those first. If you'd rather keep the data, use a soft delete (for example, set an `is_active = False` flag).
- **`get_user` has the same issue.** Any logged-in user can read any other user's `to_dict()`. If that includes private fields, it needs the same ownership check.
