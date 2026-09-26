Here's the updated endpoint:

```python
from flask import Flask, jsonify, request
from models import User

app = Flask(__name__)


@app.route("/users")
def list_users():
    limit = request.args.get("limit", default=50, type=int)
    if limit is None or limit < 1:
        return jsonify({"error": "limit must be a positive integer"}), 400

    # TODO: remove legacy sort once mobile clients migrate (ticket APP-412)
    # users = User.query.order_by(User.id.desc()).all()
    users = User.query.order_by(User.created_at).limit(limit).all()
    result = []
    for u in users:
        result.append({"id": u.id, "name": u.name})
    return jsonify(result)
```

- `request.args.get(..., type=int)` falls back to the default (50) when `limit` is missing. If `limit` is present but not an integer (e.g. `?limit=abc`), it also silently falls back to 50 instead of raising an error.
- Zero or negative values return a 400. Without this check, `.limit()` would return an empty list for 0, and database behavior for negative values varies.
- The limit is applied in the query (`LIMIT` in SQL), so the database only returns the rows you need.

**This changes existing behavior:** `/users` used to return every user, and now it returns 50 by default. Any client that expects the full list, including the mobile clients mentioned in APP-412, will start getting truncated results. If that's a problem, I can make the default "no limit" and only apply a cap when `limit` is passed.

You may also want an upper bound, such as `limit = min(limit, 500)`, so a client can't request the whole table with `?limit=1000000`. I left that out because you didn't ask for it.
