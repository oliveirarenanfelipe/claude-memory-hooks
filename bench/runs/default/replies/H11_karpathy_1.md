The slowdown comes from `seen` being a list: `key not in seen` scans the whole list every time, so the function is O(n²). Changing it to a set makes each lookup O(1) on average, so the whole thing becomes O(n):

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

The behavior stays the same. It still keeps the first original (un-normalized) email for each key, in input order.

One note unrelated to speed: `.lower()` is fine for typical ASCII emails. If you ever need Unicode-aware case folding, `.casefold()` is the stricter option. I haven't changed it here because that would change behavior.
