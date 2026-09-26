The VIP branch multiplies by `10` instead of `0.10`, so a VIP customer with a $50 order gets a $500 "discount" (1000% instead of 10%).

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

The gold tier (`0.05` = 5%) is already correct.

Unrelated to this bug: `os` and `json` are imported but unused in this file. You can remove them if nothing else in the module uses them.
