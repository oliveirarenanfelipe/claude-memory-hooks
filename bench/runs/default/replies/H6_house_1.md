The test fails because `average([])` divides by zero (`ZeroDivisionError`). The test says an empty list should average to `0`, so handle that case:

```diff
 def average(nums):
+    if not nums:
+        return 0
     return sum(nums) / len(nums)
```

Non-empty lists behave exactly as before.

**Not verified:** I can't run anything here. `pytest stats.py` should now show `test_average_empty` passing. To confirm the test covers the fix, remove the two added lines and check that it fails again with `ZeroDivisionError`.

**One design point:** returning `0` for an empty list follows the test, but it hides the difference between "no data" and "the numbers average to zero." If callers need to tell those apart, returning `None` or raising `ValueError` would be clearer. That would mean changing the test, so I kept the behavior the test asks for.
