Assumption: "latest" means the highest `ts`, not the last position in the list, since the input isn't guaranteed to be sorted. If two events for the same user share a `ts`, the one that appears later in the list wins.

```diff
 def dedupe(events):
     """events: list of dicts like {"user_id": int, "ts": datetime, "action": str}"""
     seen = {}
     for e in events:
-        if e["user_id"] not in seen:
+        prev = seen.get(e["user_id"])
+        if prev is None or e["ts"] >= prev["ts"]:
             seen[e["user_id"]] = e
     return list(seen.values())
```

The output order stays the same as before: users appear in the order they first showed up. Replacing a value in a dict doesn't change its key's position.

Quick check. I haven't run it, because I can't execute code here.

```python
from datetime import datetime as dt

evs = [
    {"user_id": 1, "ts": dt(2024, 1, 2), "action": "b"},
    {"user_id": 2, "ts": dt(2024, 1, 1), "action": "x"},
    {"user_id": 1, "ts": dt(2024, 1, 1), "action": "a"},  # older, appears later
    {"user_id": 1, "ts": dt(2024, 1, 3), "action": "c"},
]
assert [e["action"] for e in dedupe(evs)] == ["c", "x"]
```

The third event is older but comes later in the list, so it's the case that shows the difference from "last seen wins." If you actually meant "last in the list" (for example, if the input is always sorted by `ts`), the loop simplifies to `seen[e["user_id"]] = e` with no condition.
