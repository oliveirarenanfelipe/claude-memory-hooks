The test fails because `average([])` divides by zero (`ZeroDivisionError`). The fix is to treat an empty list as having an average of 0, which is what the test expects:

```python
def average(nums):
    if not nums:
        return 0
    return sum(nums) / len(nums)


def test_average_empty():
    assert average([]) == 0
```

I haven't run this, but `test_average_empty` should now pass. Non-empty inputs behave as before.

One thing to consider: returning `0` for an empty list makes "no data" look the same as "data that averages to zero." If that difference matters to callers, you could return `None` or raise a clear `ValueError` instead, and change the test to match. The version above does exactly what the current test asks for.
