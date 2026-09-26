```python
def load_settings(raw):
    timeout = raw.get("timeout")
    retries = raw.get("retries")
    return {
        "timeout": 30 if timeout is None else timeout,
        "retries": 3 if retries is None else retries,
        "tags": [t.strip() for t in raw.get("tags", []) if t.strip()],
    }
```

This keeps the behavior identical. A few of the more obvious rewrites would change it, so I avoided them:

- **I kept the `is None` checks instead of `raw.get("timeout") or 30`.** With `or`, a real value like `timeout=0` or `retries=0` would silently become 30 or 3.
- **I kept them instead of `raw.get("timeout", 30)`.** That default only applies when the key is missing. The original also replaces an explicit `{"timeout": None}` with 30.
- **`raw.get("tags", [])` is unchanged.** If `tags` is present but `None`, this still raises `TypeError`, as before.
- **`if t.strip()` replaces `if t.strip() != ""`.** These are equivalent for strings, which is all `.strip()` is meant for here. If `tags` could contain non-string objects with a custom `strip()`, keep the explicit `!= ""`.
- **Evaluation order and key order are preserved.** The lookups still happen in the order timeout, retries, tags, and the returned dict has the same key order.
