Here's the change to include `stock`:

```diff
     rows = get_db().execute(
-        f"SELECT id, name, price FROM products WHERE category = '{category}'"
+        f"SELECT id, name, price, stock FROM products WHERE category = '{category}'"
     ).fetchall()
-    return jsonify([{"id": r[0], "name": r[1], "price": r[2]} for r in rows])
+    return jsonify([{"id": r[0], "name": r[1], "price": r[2], "stock": r[3]} for r in rows])
```

This assumes the column in `products` is named `stock`.

**Separate issue: SQL injection.** The query puts `category` from the URL straight into the SQL string, so a request like `/products?category=' OR '1'='1` would return every product, and worse inputs could do more damage. You can fix it with a parameterized query:

```python
    rows = get_db().execute(
        "SELECT id, name, price, stock FROM products WHERE category = ?",
        (category,),
    ).fetchall()
```

I kept this separate because it's outside what you asked for. I'd recommend applying it, though, and I can fold it into the change if you want.
