Here's the change to include `stock`:

```diff
     rows = get_db().execute(
-        f"SELECT id, name, price FROM products WHERE category = '{category}'"
+        f"SELECT id, name, price, stock FROM products WHERE category = '{category}'"
     ).fetchall()
-    return jsonify([{"id": r[0], "name": r[1], "price": r[2]} for r in rows])
+    return jsonify([{"id": r[0], "name": r[1], "price": r[2], "stock": r[3]} for r in rows])
```

**Security issue in this query:** `category` comes straight from the query string and is interpolated into the SQL, so it's vulnerable to SQL injection. For example, `?category=' OR '1'='1` returns every product, and worse payloads are possible. I left it as-is since you only asked about `stock`, but I'd strongly recommend switching to a parameterized query:

```python
    rows = get_db().execute(
        "SELECT id, name, price, stock FROM products WHERE category = ?",
        (category,),
    ).fetchall()
```

Want me to apply that too?
