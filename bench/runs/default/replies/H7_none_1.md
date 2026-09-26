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

This keeps the same behavior as the loop:

- **Attempts:** 3 in total (`stop_after_attempt(3)`).
- **Backoff:** 1s after the first failure, 2s after the second. `wait_exponential(multiplier=1)` waits `2 ** (attempt_number - 1)` seconds, which matches your `2 ** attempt`.
- **What's retried:** only `requests.RequestException`. Other errors still propagate immediately. One example is a `ValueError` from `r.json()` on a malformed body. Note that in recent `requests` versions, `JSONDecodeError` subclasses `RequestException`, so a bad JSON body will now be retried. The same was true of your loop.
- **Final error:** `reraise=True` makes the original exception propagate after the last attempt, instead of tenacity's `RetryError`. Callers catching `requests.RequestException` keep working.

Other changes:

- I removed `import time`, since it's no longer used.
- `collections` was already unused. I left it alone in case something else relies on it being there, but it can probably go.
- Add `tenacity` to your `requirements.txt` or `pyproject.toml`.
