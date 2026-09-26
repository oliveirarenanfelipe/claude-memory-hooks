```python
def load_settings(raw):
    timeout = raw.get("timeout")
    retries = raw.get("retries")
    return {
        "timeout": 30 if timeout is None else timeout,
        "retries": 3 if retries is None else retries,
        "tags": [s for t in raw.get("tags", []) if (s := t.strip())],
    }
```

**Behavior is preserved in these cases:**

- **`is None` checks are kept on purpose.** The shorter `raw.get("timeout") or 30` would also replace `0`, `False` and `""` with the default. That would change behavior: `timeout=0` would become `30`.
- **Dict key order and lookup order** (`timeout`, `retries`, `tags`) are unchanged.
- **`"tags": None` still raises `TypeError`**, just like the original loop. I didn't add a guard for it, because that would change behavior.
- **Each tag is stripped once** instead of twice. This has no effect for strings.

**One assumption to check:** I replaced `t.strip() != ""` with a truthiness check. The two are equivalent for `str` tags. If a tag could ever be something else, they differ. For example, with `bytes`, `b"".strip() != ""` is `True`, so the original *keeps* empty byte strings. If non-`str` tags are possible and you need that exact behavior, use `if (s := t.strip()) != ""` instead.

The walrus operator (`:=`) requires Python 3.8 or later.
