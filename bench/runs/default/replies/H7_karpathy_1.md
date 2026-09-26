Here's `rates.py` using tenacity. It keeps the same behavior: 3 attempts, waits of 1s then 2s, retries only on `requests.RequestException`, and re-raises the original exception on the last failure.

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
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1),
    retry=retry_if_exception_type(requests.RequestException),
    reraise=True,
)
def get_rates():
    r = requests.get("https://api.example.com/rates", timeout=5)
    r.raise_for_status()
    return r.json()
```

Notes:
- **`reraise=True` matters.** Without it, tenacity raises `tenacity.RetryError` after the last attempt instead of the original `RequestException`. That would break any callers catching `requests.RequestException`.
- **The wait times match the old loop.** `wait_exponential(multiplier=1)` sleeps `1 * 2**(attempt_number - 1)`, which gives 1s after the first failure and 2s after the second, the same as `time.sleep(2 ** attempt)`.
- **I removed `import time`**, since nothing uses it now.
- **`import collections` was already unused before this change.** I left it in, but you can remove it.
- **You need to install the new dependency:** `pip install tenacity`. Also add it to your `requirements.txt` or `pyproject.toml`, since I couldn't see one here.
