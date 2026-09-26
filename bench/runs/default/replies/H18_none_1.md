Here's the updated route with `stock` added to both the query and the JSON output:

```python
@app.route("/products")
def products():
    category = request.args.get("category", "")
    rows = get_db().execute(
        "SELECT id, name, price, stock FROM products WHERE category = ?",
        (category,),
    ).fetchall()
    return jsonify(
        [{"id": r[0], "name": r[1], "price": r[2], "stock": r[3]} for r in rows]
    )
```

**I also changed how `category` goes into the query.** The original f-string inserted `category` straight into the SQL, which allowed SQL injection. For example, `?category=' OR '1'='1` would return every product, and worse inputs are possible. Since I was editing that line anyway, I switched it to a `?` placeholder so SQLite treats the value as data, not SQL. The endpoint behaves the same for normal input.
