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

This behaves the same as the old loop:

- **Attempts:** there are still at most 3.
- **Backoff:** `wait_exponential(multiplier=1)` waits `2 ** (attempt - 1)` seconds. That gives 1s after the first failure and 2s after the second, which is the same as `time.sleep(2 ** attempt)` before.
- **What gets retried:** only `requests.RequestException`. That includes `HTTPError` from `raise_for_status()`, as before.
- **Final failure:** `reraise=True` makes the last original exception propagate. Without it, tenacity raises its own `tenacity.RetryError`, which would break any callers that catch `requests.RequestException`.

Notes:
- Add `tenacity` to your `requirements.txt` or `pyproject.toml`.
- I removed `import time` because nothing uses it now. `import collections` was already unused before this change. I left it alone, but you can delete it.
