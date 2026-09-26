The VIP branch multiplies by `10` instead of `0.10`, so VIPs get a "discount" of 10× their order total instead of 10% of it.

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

For example, a $50 VIP order now returns a discount of `5.0` instead of `500`.

If these totals are money, consider using `Decimal` instead of floats to avoid rounding errors.
