Here's the refactor. I kept the explicit `is None` checks on purpose, because the shorter versions change behavior.

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

**Shortcuts I avoided:**

- **`raw.get("timeout") or 30`** would turn a real `0` into `30`. With `retries`, `0` is a plausible value, so this would be a real bug.
- **`raw.get("timeout", 30)`** differs when the key is present but set to `None`. The original returns `30` in that case; this version would return `None`.

**Things that stay exactly the same:**

- The dict keys are still in the order `timeout`, `retries`, `tags`.
- If `raw["tags"]` is explicitly `None`, it still raises `TypeError`, just like before. I didn't add a guard, because that would be a behavior change.
- `if t.strip()` gives the same result as `if t.strip() != ""` for strings. If `tags` could contain non-string objects with an unusual `strip()`, keep the explicit `!= ""` comparison instead.
