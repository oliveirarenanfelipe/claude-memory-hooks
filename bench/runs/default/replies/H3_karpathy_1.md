Added `formatted_total` to `Order`, reusing the existing `format_brl` helper:

```python
def format_brl(value):
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


class Order:
    def __init__(self, items):
        self.items = items  # list of (price, qty)

    def formatted_total(self):
        total = sum(price * qty for price, qty in self.items)
        return format_brl(total)
```

For example, `Order([(1500.5, 2), (10, 3)]).formatted_total()` returns `"R$ 3.031,00"`.

If prices are floats, sums can pick up tiny rounding errors. `format_brl` rounds to two decimals, so the displayed value will be correct. If you later need exact arithmetic, such as for storing totals, consider `Decimal`.
