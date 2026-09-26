Reusing the existing `format_brl` helper so the formatting stays consistent:

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

Example: `Order([(1234.5, 2), (10, 1)]).formatted_total()` → `"R$ 2.479,00"`.

I split out a raw `total()` so you can still do arithmetic or comparisons on the numeric value. An empty order returns `"R$ 0,00"`.

If prices are stored as floats, consider switching to `Decimal` to avoid rounding drift on money. The method works unchanged with either type.
