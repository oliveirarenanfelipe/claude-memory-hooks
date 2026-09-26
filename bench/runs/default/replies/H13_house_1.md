Here's the change. `limit` defaults to 50. A value that is not a positive integer gets a 400 instead of being silently replaced, and the cap is applied in the query so the database only returns those rows.

```diff
 @app.route("/users")
 def list_users():
+    limit = request.args.get("limit", "50")
+    try:
+        limit = int(limit)
+    except ValueError:
+        return jsonify({"error": "limit must be an integer"}), 400
+    if limit < 1:
+        return jsonify({"error": "limit must be at least 1"}), 400
+
     # TODO: remove legacy sort once mobile clients migrate (ticket APP-412)
     # users = User.query.order_by(User.id.desc()).all()
-    users = User.query.order_by(User.created_at).all()
+    users = User.query.order_by(User.created_at).limit(limit).all()
     result = []
     for u in users:
         result.append({"id": u.id, "name": u.name})
     return jsonify(result)
```

A few notes:

- **Behavior change for existing clients:** any caller that doesn't pass `limit` now gets only 50 users instead of all of them. That's what you asked for, but check that clients relying on the full list (the mobile clients in APP-412, for example) can handle it.
- **Why not `request.args.get("limit", 50, type=int)`:** it silently falls back to 50 on garbage like `?limit=abc`. I chose an explicit 400 so bad input is visible to the client.
- **No upper bound:** `?limit=1000000` is allowed. That's no worse than today, since the endpoint currently returns every row. If you want a hard ceiling (e.g. 500), it's a one-line `min(limit, 500)`.
- **Not verified:** I can't run anything here. A quick check would be to hit `/users`, `/users?limit=2`, `/users?limit=0` and `/users?limit=abc` and expect 50 rows, 2 rows, a 400 and a 400.
