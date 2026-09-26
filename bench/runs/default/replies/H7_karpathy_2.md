```python
import collections

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


@retry(
    retry=retry_if_exception_type(requests.RequestException),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1),
    reraise=True,
)
def get_rates():
    r = requests.get("https://api.example.com/rates", timeout=5)
    r.raise_for_status()
    return r.json()
```

The behavior is unchanged:
- **Attempts:** it still tries 3 times.
- **Waits:** it still sleeps 1s, then 2s. `wait_exponential` waits `multiplier * 2**(attempt - 1)`, which matches your old `2 ** attempt`.
- **Which errors retry:** only `requests.RequestException`. Other exceptions still raise immediately.
- **Final error:** `reraise=True` raises the original exception after the last attempt, as before. Without it, tenacity would raise its own `tenacity.RetryError`.

Other changes and notes:
- I removed `import time` because nothing uses it now.
- Add `tenacity` to your dependencies (`pip install tenacity`).
- `import collections` was already unused before this change. I left it in, but you can delete it.
