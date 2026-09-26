The slowdown comes from `seen` being a list. Each `key not in seen` check scans the whole list, so the function is O(n²). Changing it to a set makes each lookup O(1) on average, so the whole function becomes O(n):

```python
def unique_emails(emails):
    seen = set()
    out = []
    for e in emails:
        key = e.strip().lower()
        if key not in seen:
            seen.add(key)
            out.append(e)
    return out
```

Behavior stays the same: it still keeps the first occurrence of each email in its original form (untrimmed, original case) and preserves input order. For large inputs, such as tens of thousands of emails, this should go from seconds or minutes down to milliseconds.

One optional tweak: if the emails can contain non-ASCII characters, `casefold()` normalizes case more thoroughly than `lower()`. That changes which entries count as duplicates, though, so I left it as `lower()`.
