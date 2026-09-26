This `DELETE` endpoint only lets a logged-in user delete **their own** account. An open delete route would let any logged-in user delete anyone, so I didn't write one.

```python
from flask_login import current_user  # add if not already imported

@app.delete("/users/<int:user_id>")
@login_required
def delete_user(user_id):
    if current_user.id != user_id:
        abort(403)
    user = db.session.get(User, user_id) or abort(404)
    db.session.delete(user)
    db.session.commit()
    return "", 204
```

The ownership check runs before the lookup. That way, callers can't use 403 vs 404 responses to find out which user IDs exist.

**Assumptions (not verified, since I can only see this snippet):**
- `current_user.id` is the primary key used in the URL.
- If admins should also be able to delete other users, the `User` model needs a role or flag, and I can't see one. If it has one (e.g. `is_admin`), change the check to `if current_user.id != user_id and not current_user.is_admin:`.
- **Related rows:** if other tables have foreign keys to `users`, this delete will either fail with an integrity error or leave orphaned rows. Which one depends on your `relationship(..., cascade=...)` / `ondelete` settings. Check those before relying on this, because a cascade will permanently delete the user's data too.
- If a user deletes themselves, their session stays active until the next request fails to load them. You may want to call `logout_user()` before returning.

I couldn't run anything, so this is untested. A quick check:
1. Log in as user A.
2. `DELETE /users/<B's id>` should return 403.
3. `DELETE /users/<A's id>` should return 204, and a following `GET` should return 404 or redirect to login.

**Noticed, did not touch:** `get_user` has the same gap. Any logged-in user can read any other user's `to_dict()`, which may expose personal data depending on what that method returns.
