Here's the change. It uses Flask's `type=int` conversion, so a non-numeric value like `?limit=abc` falls back to 50 instead of raising an error.

```diff
 @app.route("/users")
 def list_users():
+    limit = request.args.get("limit", 50, type=int)
     # TODO: remove legacy sort once mobile clients migrate (ticket APP-412)
     # users = User.query.order_by(User.id.desc()).all()
-    users = User.query.order_by(User.created_at).all()
+    users = User.query.order_by(User.created_at).limit(limit).all()
     result = []
     for u in users:
         result.append({"id": u.id, "name": u.name})
     return jsonify(result)
```

Some things to decide:

- **Existing clients will see a change.** `/users` used to return every user. It will now return at most 50. Any client that relies on getting the full list will silently receive fewer results. If that's a problem, the default could be "no limit" when the parameter is absent.
- **No upper bound.** A client can still send `?limit=1000000`. If the goal is to protect the server, not just to let clients ask for fewer users, you should clamp it, for example with `min(limit, 200)`.
- **Zero and negative values aren't validated.** `?limit=0` returns an empty list. A negative value behaves differently by database: SQLite treats it as unlimited, and PostgreSQL raises an error, which becomes a 500. I can add a check that returns a 400 for values below 1 if you'd like.

I didn't change the commented-out legacy sort (APP-412).
