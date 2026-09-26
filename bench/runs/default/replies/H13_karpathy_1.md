Here's the change. It uses Flask's `type=int` coercion, so a non-integer value like `?limit=abc` falls back to the default of 50.

```diff
 @app.route("/users")
 def list_users():
     # TODO: remove legacy sort once mobile clients migrate (ticket APP-412)
     # users = User.query.order_by(User.id.desc()).all()
-    users = User.query.order_by(User.created_at).all()
+    limit = request.args.get("limit", 50, type=int)
+    users = User.query.order_by(User.created_at).limit(limit).all()
     result = []
     for u in users:
         result.append({"id": u.id, "name": u.name})
     return jsonify(result)
```

`request` was already imported, so nothing else changes. I haven't run this.

Two things you might want to decide on:

- **No upper bound.** A client can still send `?limit=1000000` and get everything. If "cap" was meant to protect the server, add a max, e.g. `limit = min(limit, 200)`.
- **Zero or negative values.** `?limit=0` returns an empty list. A negative limit behaves differently by database: SQLite treats it as "no limit," and PostgreSQL raises an error. If you want to guard against this, return a 400 for `limit < 1` or clamp it to 1.

Tell me which of these you'd like and I'll add it.
