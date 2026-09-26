The test is correct; the bug is in `apply_discount`. The docstring says `pct` must be between 0 and 100 **inclusive**, but the guard uses `pct >= 100`, so `apply_discount(80, 100)` raises `ValueError` instead of returning `0`. That third assertion is what fails in CI.

Changing the test to expect the error would make the build green but lock in behavior that contradicts the documented contract. Anyone relying on a 100% discount (free item) would still hit the error. I recommend fixing the function instead:

```diff
 def apply_discount(price, pct):
     """Return price after a pct% discount. pct must be between 0 and 100 inclusive."""
-    if pct < 0 or pct >= 100:
+    if pct < 0 or pct > 100:
         raise ValueError("pct out of range")
     return round(price * (1 - pct / 100), 2)
```

With this change, all four checks in `test_apply_discount` should pass:
- `apply_discount(100, 10)` → `90.0`
- `apply_discount(59.99, 0)` → `59.99`
- `apply_discount(80, 100)` → `0.0`
- `apply_discount(50, 101)` → raises `ValueError`

I haven't run this, so please confirm in CI.

If a 100% discount is meant to be disallowed, the docstring is what's wrong. In that case, change it to "0 inclusive to 100 exclusive" and update the test to `with pytest.raises(ValueError): apply_discount(80, 100)`. Let me know if that's the intent and I'll write that version instead.
