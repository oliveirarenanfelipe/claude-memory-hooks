The test isn't wrong; `apply_discount` is. The docstring says `pct must be between 0 and 100 inclusive`, but the guard uses `pct >= 100`, so `apply_discount(80, 100)` raises `ValueError`. The test's third assertion is catching a real off-by-one bug. If I changed the test to fit the code, the bug would stay hidden, so I fixed the guard instead:

```diff
 def apply_discount(price, pct):
     """Return price after a pct% discount. pct must be between 0 and 100 inclusive."""
-    if pct < 0 or pct >= 100:
+    if pct < 0 or pct > 100:
         raise ValueError("pct out of range")
     return round(price * (1 - pct / 100), 2)
```

After the fix, each assertion should behave like this:
- `apply_discount(100, 10)` → `90.0 == 90` ✓
- `apply_discount(59.99, 0)` → `59.99` ✓
- `apply_discount(80, 100)` → `0.0 == 0` ✓ (this used to raise)
- `apply_discount(50, 101)` → still raises `ValueError` ✓

I can't run anything here, so this is not verified. Please run `pytest pricing.py` locally or push to CI to confirm it goes green.

If a 100% discount is supposed to be rejected, the docstring is what's wrong. In that case, keep `>= 100`, change the docstring to "0 inclusive to 100 exclusive", and change the third assertion to `with pytest.raises(ValueError): apply_discount(80, 100)`. Let me know if that's what you want and I'll switch it.
