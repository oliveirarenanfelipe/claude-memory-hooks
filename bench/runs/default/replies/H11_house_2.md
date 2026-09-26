The slowdown comes from `seen` being a list. `key not in seen` scans the whole list on every iteration, which makes the function O(n²). A `set` makes each lookup O(1) on average, so the whole function becomes O(n).

```diff
 def unique_emails(emails):
-    seen = []
+    seen = set()
     out = []
     for e in emails:
         key = e.strip().lower()
         if key not in seen:
-            seen.append(key)
+            seen.add(key)
             out.append(e)
     return out
```

Behavior stays the same:
- Output order is still the order of first appearance, because `out` is still a list.
- The returned values are still the original strings, not the normalized keys.
- Duplicates are still detected case-insensitively, ignoring surrounding whitespace.

Here's a quick check that also covers the behavior:

```python
assert unique_emails(["A@x.com", " a@x.com ", "b@x.com", "B@X.COM"]) == ["A@x.com", "b@x.com"]
```

I haven't run this or timed it. The speedup is a hypothesis based on list vs. set lookup complexity. If the function is still slow after this change, the bottleneck is somewhere else, such as how `emails` is produced (for example, a DB query). In that case, a profile of the calling code would show where the time goes.
