I've added an in-process cache with a 5-minute expiry, using only the standard library:

```python
import time

import requests

API = "https://api.example.com"
CACHE_TTL = 300  # seconds

_cache = {}  # user_id -> (expires_at, data)

def fetch_user(user_id):
    entry = _cache.get(user_id)
    if entry and entry[0] > time.monotonic():
        return entry[1]
    r = requests.get(f"{API}/users/{user_id}", timeout=5)
    r.raise_for_status()
    data = r.json()
    _cache[user_id] = (time.monotonic() + CACHE_TTL, data)
    return data
```

**Assumptions:**
- **TTL rather than `functools.lru_cache`.** `lru_cache` is simpler, but user records would stay cached until the process restarts.
- **Per-process.** Each Gunicorn/uWSGI worker keeps its own cache, and the cache resets on restart. If you need one cache across workers, use Redis, for example through Flask-Caching.
- **Failed requests aren't cached.** `raise_for_status()` raises before anything is stored.
- **Callers get the cached dict itself.** If a caller mutates the result, later calls see that change. Return `copy.deepcopy(data)` if that's a risk.
- **Expired entries are replaced, not evicted.** With a very large number of distinct user IDs, memory will keep growing. `cachetools.TTLCache(maxsize=..., ttl=...)` bounds memory if that matters.

If you want a different TTL, shared caching, or a way to invalidate a user after an update, tell me and I'll adjust it.
