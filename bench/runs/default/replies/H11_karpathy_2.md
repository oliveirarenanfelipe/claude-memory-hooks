The slowdown comes from `seen` being a list. Each `key not in seen` check scans the whole list, so the function is O(n²). Changing it to a set makes each lookup O(1) on average, so the whole function becomes O(n):

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

The behavior stays the same. Order is kept, the first occurrence wins, and the original (unnormalized) string is returned.

I haven't run this. For large inputs, like tens of thousands of emails or more, you should see a big speedup.
