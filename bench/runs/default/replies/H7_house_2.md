`wait_exponential()` with its defaults produces 1s and then 2s, the same backoff as the old `2 ** attempt`. `reraise=True` keeps the original behavior: the last `requests.RequestException` is raised to the caller, not tenacity's `RetryError`.

```diff
-import time
 import collections
 
 import requests
+from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
 
 
+@retry(
+    retry=retry_if_exception_type(requests.RequestException),
+    stop=stop_after_attempt(3),
+    wait=wait_exponential(),
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

Behavior is unchanged:
- **Attempts:** at most 3.
- **Waits:** 1s and then 2s between attempts.
- **What gets retried:** only `requests.RequestException` and its subclasses. That includes `HTTPError` from `raise_for_status()` and, on requests ≥ 2.27, the JSON decode error, just like before.
- **After the last failure:** the original exception is re-raised.

I removed `import time` because it's no longer used.

Things to do on your side:
- **Dependency:** add `tenacity` to your dependencies (`requirements.txt` / `pyproject.toml`). I can't see those files, so I haven't added it.
- **Not verified:** I couldn't run this. A quick check is to point the URL at something that fails and confirm there are 3 calls about 1s and 2s apart, then the original exception.

Noticed, did not touch: `import collections` was already unused before this change (a single line).
