Using `functools.lru_cache` from the standard library, bounded so memory can't grow without limit:

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

Failed requests are not cached, because `raise_for_status()` raises and `lru_cache` only stores successful returns. It is also thread-safe for Flask's threaded workers.

**Assumption:** cached entries never expire. A user's data stays as it was on the first fetch until the process restarts or you call `fetch_user.cache_clear()`. If users change while the app is running, you'll want a TTL instead. The stdlib has no TTL cache; `cachetools.TTLCache` is the usual choice if you can add it as a dependency. Tell me the acceptable staleness and I'll switch to that.

Things to know:
- **Shared mutable result:** every caller gets the same `dict` object. If any code mutates the returned user, for example `user["name"] = ...`, that change leaks into later requests. I can't see the callers, so I haven't checked this. If any of them mutate it, return `copy.deepcopy(...)` from a wrapper.
- **Per process:** each gunicorn/uwsgi worker keeps its own cache. Use Redis or similar if you need one shared cache.
- `fetch_user(1)` and `fetch_user("1")` are cached as separate entries.

Not verified: I can't run anything here. A quick check is to call `fetch_user(1)` twice with `requests.get` mocked and assert the mock was called once.
