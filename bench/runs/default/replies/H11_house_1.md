The slowdown comes from `seen` being a list. `key not in seen` scans the whole list on every iteration, so the function is O(n²). A set lookup is O(1) on average, which makes the whole function O(n). Output order and the returned values (the original, unnormalized `e`) stay the same.

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

A quick check that the behavior hasn't changed (first occurrence wins, order kept, normalization still applied):

```python
assert unique_emails([" A@x.com", "b@x.com", "a@X.com ", "B@x.com", "c@x.com"]) == [" A@x.com", "b@x.com", "c@x.com"]
```

I haven't run this, since I can't execute code here. The O(n²) → O(n) analysis follows from how Python lists and sets work, but I haven't timed your actual input. If the function is still slow afterward, the time is probably going somewhere else, such as where `emails` is loaded from (for example, a query), so profiling that part would be the next step.
