Here's `get_rates` rewritten with tenacity. It keeps the current behaviour: 3 attempts, waits of 1s then 2s, retries only on `requests.RequestException`, and re-raises the original exception after the last failure.

```diff
-import time
 import collections
 
 import requests
+from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
 
 
+@retry(
+    stop=stop_after_attempt(3),
+    wait=wait_exponential(multiplier=1),
+    retry=retry_if_exception_type(requests.RequestException),
+    reraise=True,
+)
 def get_rates():
-    for attempt in range(3):
-        try:
-            r = requests.get("https://api.example.com/rates", timeout=5)
-            r.raise_for_status()
-            return r.json()
-        except requests.RequestException:
-            if attempt == 2:
-                raise
-            time.sleep(2 ** attempt)
+    r = requests.get("https://api.example.com/rates", timeout=5)
+    r.raise_for_status()
+    return r.json()
```

How the settings match the old loop:
- **`wait_exponential(multiplier=1)`** waits `1 * 2**(attempt_number - 1)` seconds. That gives 1s after the first failure and 2s after the second, the same as `time.sleep(2 ** attempt)` did.
- **`reraise=True`** makes callers still get the original `requests` exception. Without it, tenacity raises `tenacity.RetryError` instead, which would break any `except requests.RequestException` in callers.
- **`retry_if_exception_type(...)`** keeps the old scope. Other exceptions fail immediately. That includes a `ValueError` from `r.json()` on older `requests` versions, which the old loop also didn't catch.
- I removed `import time` because nothing uses it now.

You need to add `tenacity` to your dependencies (e.g. `requirements.txt`). I can't see whether it's already installed.

I haven't run this. To check it, you could mock `requests.get` to raise `requests.ConnectionError` twice and then return a response. Assert it's called 3 times and the result comes back. A second test can raise on every call and assert that `ConnectionError`, not `RetryError`, reaches the caller. To avoid the real 3s of sleeping in tests, patch the wait with `get_rates.retry.wait = tenacity.wait_none()`, or just the sleep with `get_rates.retry.sleep = lambda s: None`.

Noticed, did not touch: `import collections` was already unused before this change. It's a one-line cleanup if you want it.
