The test fails with `ZeroDivisionError` because `len([])` is 0. Here's the fix: return `0` for an empty list.

```diff
 def average(nums):
+    if not nums:
+        return 0
     return sum(nums) / len(nums)
```

The test expects an empty list to average to `0`. That's a design choice: it's simple, but it hides an empty input and can't be told apart from a real average of zero. If you'd rather callers be told explicitly, `raise ValueError("average() of empty sequence")` or `return None` would be stricter, but then the test would need to change too.

I haven't run this, but `average([])` now returns `0` before reaching the division, so `test_average_empty` should pass.
