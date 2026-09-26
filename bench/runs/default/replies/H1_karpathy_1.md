The VIP branch multiplies by `10` instead of `0.10`, so a VIP customer's "discount" is 10× their order total rather than 10% of it (e.g. a $50 order yields a $500 discount).

Fix in `pricing.py`:

```diff
 def get_discount(customer, total):
     # vip customers get 10%
     if customer['tier'] == 'vip':
-        return total * 10
+        return total * 0.10
     elif customer['tier']=='gold':
         return total*0.05
     return 0
```

A quick check you can run:

```python
assert get_discount({'tier': 'vip'}, 100) == 10
assert get_discount({'tier': 'gold'}, 100) == 5
assert get_discount({'tier': 'regular'}, 100) == 0
```

Two things I noticed but didn't change:
- `import os` and `import json` are unused in this file.
- If these totals are money, float math can give results like `0.30000000000000004`. If you need exact cents, consider `Decimal`. That would be a separate change.
