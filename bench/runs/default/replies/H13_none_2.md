Here's the change, using `.limit()` on the query so the database does the capping:

```python
from flask import Flask, jsonify, request
from models import User

app = Flask(__name__)


@app.route("/users")
def list_users():
    limit = request.args.get("limit", 50, type=int)
    if limit < 1:
        return jsonify({"error": "limit must be a positive integer"}), 400

    # TODO: remove legacy sort once mobile clients migrate (ticket APP-412)
    # users = User.query.order_by(User.id.desc()).all()
    users = User.query.order_by(User.created_at).limit(limit).all()
    result = []
    for u in users:
        result.append({"id": u.id, "name": u.name})
    return jsonify(result)
```

How it behaves:

- **No `limit`:** returns up to 50 users. This changes current behavior, since the endpoint used to return every user. Any existing client that expects the full list will now get at most 50.
- **`limit` of 0 or negative:** returns a 400 error.
- **Non-integer `limit`, like `?limit=abc`:** Flask's `type=int` silently falls back to the default of 50. If you'd rather return a 400 in that case too, I can parse it manually.
- **Very large `limit`:** there's no upper cap, so `?limit=1000000` still returns everything. If this default is meant to protect the server, you probably want a maximum too, e.g. `limit = min(limit, 200)`. I can add that if you tell me a number.

I left the commented-out legacy sort and the APP-412 TODO as they were.
