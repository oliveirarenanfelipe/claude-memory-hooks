Here's the refactor:

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

A few changes that look idiomatic would have changed behavior, so I avoided them:

- **No `raw.get("timeout") or 30`.** The original only falls back on `None`. With `or`, a timeout of `0` would become `30`, and `retries: 0` would become `3`. The explicit `is None` check keeps falsy values like `0` and `False`.
- **No `raw.get("timeout", 30)`.** That only covers a missing key. The original also falls back when the key is present but set to `None`.
- **`raw.get("tags", [])` is unchanged.** If `raw["tags"]` is explicitly `None`, the original raises `TypeError`, and this version does too. Writing `raw.get("tags") or []` would hide that error.
- **`if t.strip()` matches `!= ""`.** For strings, only the empty string is falsy. Non-string tags still fail on `.strip()` as before.
- **Order is preserved.** The dict keys are still `timeout`, `retries`, `tags`, and the lookups on `raw` happen in the same order.

If you're on Python 3.8+, you could avoid calling `strip()` twice:

```python
"tags": [s for t in raw.get("tags", []) if (s := t.strip())],
```

This behaves the same for ordinary strings. It only differs for a custom `str` subclass whose `strip()` has side effects. That's very unlikely, which is why I kept the plainer version as the default.
