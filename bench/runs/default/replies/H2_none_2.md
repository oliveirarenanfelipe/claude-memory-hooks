Here's an in-process TTL cache. I used a TTL instead of plain `functools.lru_cache` because user data changes, and `lru_cache` would keep serving stale results until the process restarts.

```python
import copy
import threading
import time

import requests

API = "https://api.example.com"

CACHE_TTL = 300  # seconds
CACHE_MAX_SIZE = 1024

_cache = {}  # user_id -> (expires_at, data)
_cache_lock = threading.Lock()


def fetch_user(user_id):
    now = time.monotonic()
    with _cache_lock:
        entry = _cache.get(user_id)
        if entry and entry[0] > now:
            return copy.deepcopy(entry[1])

    r = requests.get(f"{API}/users/{user_id}", timeout=5)
    r.raise_for_status()
    data = r.json()

    with _cache_lock:
        if len(_cache) >= CACHE_MAX_SIZE:
            # Drop expired entries first, then the oldest if still full
            for key in [k for k, (exp, _) in _cache.items() if exp <= now]:
                del _cache[key]
            if len(_cache) >= CACHE_MAX_SIZE:
                del _cache[next(iter(_cache))]
        _cache[user_id] = (now + CACHE_TTL, data)

    return copy.deepcopy(data)


def invalidate_user(user_id=None):
    """Drop one cached user, or the whole cache if user_id is None."""
    with _cache_lock:
        if user_id is None:
            _cache.clear()
        else:
            _cache.pop(user_id, None)
```

How it behaves:
- **Errors aren't cached.** If `raise_for_status()` raises, nothing is stored, so the next call retries.
- **Thread-safe.** Flask's threaded server can call this concurrently. The lock isn't held during the HTTP request, so two simultaneous misses for the same user may both fetch. That's harmless.
- **It returns copies.** A caller mutating the returned dict won't corrupt the cache.
- **`invalidate_user`** lets you evict a user after you update them through the API.

Limitation: the cache lives in each process. Under gunicorn or uWSGI with several workers, each worker has its own cache, and invalidation only affects the worker that runs it. If you need a shared cache or cross-worker invalidation, use Flask-Caching with a Redis backend. I can switch it over if that fits your deployment.

Adjust `CACHE_TTL` to how stale you can tolerate user data being.
