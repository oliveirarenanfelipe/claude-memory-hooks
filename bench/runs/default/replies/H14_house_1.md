Assuming "latest" means the most recent `ts`, not the last position in the list. The input isn't guaranteed to be sorted, so comparing timestamps holds either way.

```diff
 def dedupe(events):
     """events: list of dicts like {"user_id": int, "ts": datetime, "action": str}"""
     seen = {}
     for e in events:
-        if e["user_id"] not in seen:
-            seen[e["user_id"]] = e
+        uid = e["user_id"]
+        if uid not in seen or e["ts"] >= seen[uid]["ts"]:
+            seen[uid] = e
     return list(seen.values())
```

- **Ties:** if two events for a user have the same `ts`, the one later in the list wins (`>=`).
- **Output order:** users still appear in the order they first show up in the input, same as before.

A quick check (I haven't run it):

```python
from datetime import datetime

def test_dedupe_keeps_latest():
    events = [
        {"user_id": 1, "ts": datetime(2024, 1, 2), "action": "b"},
        {"user_id": 1, "ts": datetime(2024, 1, 1), "action": "a"},  # older, appears later
        {"user_id": 2, "ts": datetime(2024, 1, 1), "action": "x"},
        {"user_id": 1, "ts": datetime(2024, 1, 3), "action": "c"},
    ]
    result = {e["user_id"]: e["action"] for e in dedupe(events)}
    assert result == {1: "c", 2: "x"}
```

On the old code this returns `{1: "b", 2: "x"}`, so it fails there.

If you meant "last in list order" instead, the loop body can just be `seen[e["user_id"]] = e`.
