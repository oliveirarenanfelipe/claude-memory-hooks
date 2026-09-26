`average([])` raises `ZeroDivisionError` because `len([])` is 0. Return 0 for an empty list:

```diff
 def average(nums):
+    if not nums:
+        return 0
     return sum(nums) / len(nums)
```

This makes `test_average_empty` pass (I can't run it here, so please confirm with `pytest stats.py`).

One thing to note: returning 0 means callers can't tell "no data" apart from "the numbers average to 0." That's what the test asks for, so I followed it. If you'd rather make empty input explicit, you could return `None` or raise a `ValueError` and change the test to match. Just say if you want that.
