The VIP branch multiplies by `10` instead of `0.10`, so a VIP order of 200 gets a discount of 2000 instead of 20. The comment and the gold branch (`0.05`) both show the intended form is a fraction.

```diff
--- a/pricing.py
+++ b/pricing.py
@@ def get_discount(customer, total):
     # vip customers get 10%
     if customer['tier'] == 'vip':
-        return total * 10
+        return total * 0.10
     elif customer['tier']=='gold':
         return total*0.05
     return 0
```

A small test that fails before the fix and passes after it:

```python
from pricing import get_discount

def test_vip_discount_is_ten_percent():
    assert get_discount({'tier': 'vip'}, 200) == 20
```

I couldn't run anything here, so neither the fix nor the test has been run. To confirm the test covers the bug, run it once against the old line (it should fail with `2000 != 20`), then against the fix.

**Worth checking:** if `total` is ever a `Decimal`, as with a SQLAlchemy `Numeric` column, `total * 0.10` raises `TypeError`. The gold branch already has this problem, so the fix doesn't make it worse, but it's worth knowing.

**Noticed, didn't change:** `import os` and `import json` aren't used in `pricing.py`. They're harmless.
