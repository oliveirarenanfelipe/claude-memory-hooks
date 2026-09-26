Here's the endpoint, placed after `get_user` in `users_api.py`:

```python
@app.delete("/users/<int:user_id>")
@login_required
def delete_user(user_id):
    user = db.session.get(User, user_id) or abort(404)
    if current_user.id != user.id and not current_user.is_admin:
        abort(403)
    db.session.delete(user)
    db.session.commit()
    return "", 204
```

And update the imports:

```python
from flask_login import current_user, login_required
```

**Assumptions to check:**

- **Who may delete.** `@login_required` alone would let any logged-in user delete any account, so I limited it to the user themself or an admin. This assumes `User` has an `is_admin` attribute. If your role check looks different, or only admins should delete accounts, change that line.
- **Related rows.** `db.session.delete` only cascades to relationships configured with `cascade="all, delete-orphan"`. If other tables have foreign keys to `users` without cascades, the commit will fail with an `IntegrityError` or leave orphaned rows, depending on the database. Let me know if you'd rather soft-delete (for example, an `is_active` or `deleted_at` flag).
- **Self-deletion.** After users delete their own account, their session cookie still points to a missing user. Flask-Login's `user_loader` will return `None`, so they're effectively logged out on the next request. You could also call `logout_user()` before returning.

**Something I noticed but didn't change:** `get_user` has the same gap. Any logged-in user can read any other user's `to_dict()` output. That may be intentional, but it's worth checking what `to_dict()` exposes.
