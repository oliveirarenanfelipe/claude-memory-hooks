I've reused the existing `format_brl` helper so the formatting stays consistent with the rest of the module:

```python
def format_brl(value):
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


class Order:
    def __init__(self, items):
        self.items = items  # list of (price, qty)

    def total(self):
        return sum(price * qty for price, qty in self.items)

    def formatted_total(self):
        return format_brl(self.total())
```

For example, `Order([(1234.5, 2), (10, 1)]).formatted_total()` returns `"R$ 2.479,00"`.

I split out `total()` so the raw number is also available for comparisons and calculations. If prices are floats, rounding errors can pile up across many items. If this is real money, consider storing prices as `Decimal` (or as integer cents). `format_brl` already works with `Decimal`.
