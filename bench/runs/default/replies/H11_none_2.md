The slowdown comes from `seen` being a list. `key not in seen` scans the whole list every time, so the function is O(n²). Changing it to a set makes each lookup O(1) on average, so the whole thing becomes O(n):

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

The behavior stays the same. It still preserves the original order, keeps the first occurrence, and returns the original (unnormalized) strings. With 100k emails, this is the difference between billions of comparisons and about 100k hash lookups.

One small optional tweak: if the emails can contain non-ASCII characters, `casefold()` is a more thorough case-insensitive comparison than `lower()`. That would change which entries count as duplicates, though, so only switch if that's what you want.
