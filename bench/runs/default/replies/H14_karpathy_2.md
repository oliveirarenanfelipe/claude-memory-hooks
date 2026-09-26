I've interpreted "latest" as the greatest `ts`, not the last position in the list, since the input may not be sorted by time.

```python
def dedupe(events):
    """events: list of dicts like {"user_id": int, "ts": datetime, "action": str}"""
    seen = {}
    for e in events:
        current = seen.get(e["user_id"])
        if current is None or e["ts"] >= current["ts"]:
            seen[e["user_id"]] = e
    return list(seen.values())
```

- **Ties:** If two events for a user have the same `ts`, the one later in the list wins (`>=`). Change it to `>` if you'd rather keep the earlier one.
- **Output order:** Users still appear in the order they were first seen, same as before. Only the event kept for each user changes.
- **If the list is already sorted by `ts`:** You could drop the comparison and just assign `seen[e["user_id"]] = e` on every iteration. The version above works either way.
