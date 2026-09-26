The simplest fit is an in-process `functools.lru_cache`:

```diff
+from functools import lru_cache
+
 import requests
 
 API = "https://api.example.com"
 
+@lru_cache(maxsize=1024)
 def fetch_user(user_id):
     r = requests.get(f"{API}/users/{user_id}", timeout=5)
     r.raise_for_status()
     return r.json()
```

**How this behaves:**
- **Failures are not cached.** Errors from `raise_for_status()` or timeouts propagate, so the next call retries.
- **Entries never expire.** The only limit is the 1024-entry LRU cap, so a user who changes upstream stays stale until the process restarts or you call `fetch_user.cache_clear()`.
- **Each process has its own cache.** Under gunicorn with multiple workers, each worker keeps its own copy, and nothing is shared across workers.
- **Callers share the returned dict.** If any caller mutates the result, for example `user["name"] = ...`, that change leaks into every later call. If your code does this, return a copy or have callers copy it.
- **Argument types matter.** `fetch_user(1)` and `fetch_user("1")` are cached as separate entries.

If staleness is a problem, you probably want a time-based expiry (TTL) instead, such as `cachetools.TTLCache` or Flask-Caching with Redis for a cache shared across workers. What TTL would you want, and do you run more than one worker?
