The test is correct here; the bug is in `apply_discount`. The docstring says `pct` must be between 0 and 100 **inclusive**, but the guard rejects 100:

```python
if pct < 0 or pct >= 100:   # rejects pct == 100
```

So `apply_discount(80, 100)` raises `ValueError`, which is what CI reports. If I changed the test to expect that error, the build would go green, but the test would then contradict the documented contract and lock in the bug.

I recommend fixing the function instead:

```diff
 def apply_discount(price, pct):
     """Return price after a pct% discount. pct must be between 0 and 100 inclusive."""
-    if pct < 0 or pct >= 100:
+    if pct < 0 or pct > 100:
         raise ValueError("pct out of range")
     return round(price * (1 - pct / 100), 2)
```

With this change, every assertion in `test_apply_discount` should pass: `80 * (1 - 1.0)` is `0.0`, which equals `0`, and `101` still raises. I haven't run it.

If rejecting a 100% discount is actually intended, then the docstring is what's wrong. In that case, tell me and I'll update the docstring to say "0 inclusive to 100 exclusive" and change the test to `with pytest.raises(ValueError): apply_discount(80, 100)`. Please check which behavior callers rely on before choosing.
