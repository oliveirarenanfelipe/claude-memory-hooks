The test fails because `average([])` divides by `len([]) == 0` and raises `ZeroDivisionError`. The test sets the contract that an empty list averages to `0`, so the fix is to guard that case:

```diff
 def average(nums):
+    if not nums:
+        return 0
     return sum(nums) / len(nums)
```

I couldn't run this here, so it's not verified. You can check it with `pytest stats.py`. To confirm the test actually covers the new branch, remove the guard and the test should fail again with `ZeroDivisionError`.

One thing to decide: returning `0` for an empty list is a design choice. An empty list's average is mathematically undefined, and `statistics.mean([])` raises `StatisticsError`. Callers can't tell "no data" apart from "the average is 0." I followed the test because it states the intended behavior. If you'd prefer raising or returning `None`, the test is what should change.
