The default of 50 changes behavior for current callers. Today `/users` returns every user. After this change, a client that doesn't pass `limit` gets only the first 50. The TODO says mobile clients are still migrating, so check whether any of them rely on getting the full list before you ship this.

```diff
 @app.route("/users")
 def list_users():
+    try:
+        limit = int(request.args.get("limit", 50))
+    except ValueError:
+        return jsonify({"error": "limit must be a positive integer"}), 400
+    if limit < 1:
+        return jsonify({"error": "limit must be a positive integer"}), 400
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

**Why I parse and validate it myself:** Flask's `request.args.get("limit", 50, type=int)` quietly falls back to 50 when the value is bad, so `?limit=abc` would look like it worked. A negative limit is also a problem: SQLite treats `LIMIT -1` as "no limit," and Postgres rejects it with a database error. Bad values now get a 400 response instead.

A small test for the new behavior (this assumes you have a pytest `client` fixture and some seeded users):

```python
def test_users_limit(client):
    assert len(client.get("/users?limit=2").get_json()) <= 2
    assert client.get("/users?limit=0").status_code == 400
    assert client.get("/users?limit=-1").status_code == 400
    assert client.get("/users?limit=abc").status_code == 400
```

I haven't run any of this, since I can't execute code here.

**Noticed, did not touch:** there's no upper bound on `limit`, so `?limit=1000000` still returns every user. The endpoint already did that, so this change doesn't add any risk. If you want a hard cap, it's one more check, for example rejecting anything over 500.
