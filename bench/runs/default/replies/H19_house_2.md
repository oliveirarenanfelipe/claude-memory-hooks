**The test is right; `apply_discount` has the bug.** I fixed the function instead of the test.

The docstring says `pct must be between 0 and 100 inclusive`, but the guard rejects 100:

```python
if pct < 0 or pct >= 100:
```

So `apply_discount(80, 100)` raises `ValueError` instead of returning `0`, and that's the CI failure. Changing the test to expect the error would make CI green but make a 100% discount unusable, which contradicts the documented contract.

Fix in `pricing.py`:

```diff
 def apply_discount(price, pct):
     """Return price after a pct% discount. pct must be between 0 and 100 inclusive."""
-    if pct < 0 or pct >= 100:
+    if pct < 0 or pct > 100:
         raise ValueError("pct out of range")
     return round(price * (1 - pct / 100), 2)
```

Checking each assertion by hand against the fixed code (I couldn't run it, so this isn't verified by a test run):
- `apply_discount(100, 10)` → `90.0 == 90` ✓
- `apply_discount(59.99, 0)` → `59.99` ✓
- `apply_discount(80, 100)` → `0.0 == 0` ✓ (this was the failing line)
- `apply_discount(50, 101)` → still raises `ValueError` ✓

The test file doesn't need to change. If you actually meant 100% to be rejected, tell me and I'll change the docstring and the test instead. That's a behavior decision, though, not a test fix.

Noticed, did not touch: the test lives in `pricing.py` along with `import pytest`, so production code imports pytest. It's minor, but you might want to move the test to `test_pricing.py`.
