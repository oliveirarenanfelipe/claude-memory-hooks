The test is correct. The bug is in `apply_discount`. The docstring says `pct` must be between 0 and 100 **inclusive**, but the guard rejects 100:

```python
if pct < 0 or pct >= 100:   # 100 raises ValueError
```

So `apply_discount(80, 100)` raises, and the test fails. Changing the test to match would lock in behavior that contradicts the documented contract. The one-character fix belongs in the function:

```diff
 def apply_discount(price, pct):
     """Return price after a pct% discount. pct must be between 0 and 100 inclusive."""
-    if pct < 0 or pct >= 100:
+    if pct < 0 or pct > 100:
         raise ValueError("pct out of range")
     return round(price * (1 - pct / 100), 2)
```

With this change, all four assertions should pass. I can't run it here, but `round(80 * 0.0, 2) == 0` holds, and 101 still raises.

If a 100% discount really should be disallowed, the code is right and the docstring is wrong. In that case, update the docstring to say "0 ≤ pct < 100" and change the test line to:

```python
    with pytest.raises(ValueError):
        apply_discount(80, 100)
```

Let me know if that's what you intended. Otherwise I'd go with the diff above.
