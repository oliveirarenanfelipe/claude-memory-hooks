Here's a `DELETE /users/<id>` endpoint that follows the style of `get_user`. It only lets a logged-in user delete **their own** account.

```python
from flask_login import current_user, login_required, logout_user


@app.delete("/users/<int:user_id>")
@login_required
def delete_user(user_id):
    if user_id != current_user.id:
        abort(403)
    user = db.session.get(User, user_id) or abort(404)
    db.session.delete(user)
    db.session.commit()
    logout_user()
    return "", 204
```

**Why it's written this way:**
- **Owner check.** `@login_required` alone would let any logged-in user delete any other account. The 403 check runs before the lookup, so nobody can use 404 vs. 403 responses to find out which user IDs exist.
- **`logout_user()`.** The session belongs to a user who no longer exists, so it's cleared.
- **204 No Content.** There's nothing left to return.

**Assumptions to confirm (I couldn't run this, so it's untested):**
- **Admins.** I assumed only self-deletion. If admins should be able to delete other users, tell me how admins are identified (for example a `User.is_admin` field) and I'll add that branch.
- **Hard delete.** This removes the row permanently. If other tables have foreign keys to `users`, the commit will either fail or cascade, depending on how those relationships are configured. That code isn't shown here. If you want deletion to be recoverable, a soft delete (e.g. a `deleted_at` column) is the safer option.
- **CSRF.** A cookie-authenticated `DELETE` needs CSRF protection, such as Flask-WTF's `CSRFProtect` or a SameSite cookie policy. I can't see whether the app has either.

**Noticed, did not touch:** `get_user` has the same gap. Any logged-in user can read any other user's `to_dict()` just by changing the ID. How serious that is depends on which fields `to_dict()` exposes.
