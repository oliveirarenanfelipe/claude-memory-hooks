The test fails because `average([])` divides by `len([]) == 0`, raising `ZeroDivisionError`. The test expects an empty list to average to `0`, so add a guard:

```diff
 def average(nums):
+    if not nums:
+        return 0
     return sum(nums) / len(nums)
```

One thing to be aware of: returning `0` for an empty input makes "no data" look the same as "data that averages to zero." If callers need to tell those apart, returning `None` or raising a `ValueError` might be better, but that would mean changing the test. I've followed the test as written.

I can't run the test here. `pytest stats.py` should now pass.
