```python
def load_settings(raw):
    timeout = raw.get("timeout")
    retries = raw.get("retries")
    stripped = (t.strip() for t in raw.get("tags", []))
    return {
        "timeout": 30 if timeout is None else timeout,
        "retries": 3 if retries is None else retries,
        "tags": [t for t in stripped if t != ""],
    }
```

I avoided some shorter forms because they would change behavior:

- **`raw.get("timeout") or 30` would be wrong.** It replaces `0`, `False` and `""` with the default, but the original keeps them. Only `None` falls back.
- **`raw.get("timeout", 30)` would be wrong.** If the key is present with value `None`, the original returns `30` and this form returns `None`.
- **`if t.strip()` (a truthiness test) would be wrong.** It is the same for `str`, but not for other types. For example, `b"  "` passes the original `!= ""` test and would be dropped by a truthiness test. So the explicit comparison stays.
- **The following behavior is unchanged:** a `tags` value of `None` still raises `TypeError`; `strip()` still runs on each tag in order; key order in the result is the same; the `.get` calls happen in the same order.

The only difference is that `strip()` now runs once per tag instead of twice. The result is the same.

I haven't run this. Here's a quick check to paste in next to the old version (renamed `load_settings_old`):

```python
cases = [
    {},
    {"timeout": None, "retries": None},
    {"timeout": 0, "retries": 0, "tags": [" a ", "", "  ", "b"]},
    {"timeout": False, "retries": "", "tags": [b"  ", b"x"]},
]
for c in cases:
    assert load_settings(c) == load_settings_old(c), c
```
