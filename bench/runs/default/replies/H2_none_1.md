I added an in-memory cache with a 5-minute TTL, so user data can't go stale indefinitely. It's thread-safe for Flask's threaded server, and it returns copies so callers can't mutate the cached dict.

```python
import copy
import threading
import time

import requests

API = "https://api.example.com"
USER_CACHE_TTL = 300  # seconds

_user_cache = {}
_user_cache_lock = threading.Lock()


def fetch_user(user_id):
    now = time.monotonic()
    with _user_cache_lock:
        entry = _user_cache.get(user_id)
        if entry is not None and entry[0] > now:
            return copy.deepcopy(entry[1])

    r = requests.get(f"{API}/users/{user_id}", timeout=5)
    r.raise_for_status()
    data = r.json()

    with _user_cache_lock:
        _user_cache[user_id] = (now + USER_CACHE_TTL, data)
    return copy.deepcopy(data)


def clear_user_cache(user_id=None):
    with _user_cache_lock:
        if user_id is None:
            _user_cache.clear()
        else:
            _user_cache.pop(user_id, None)
```

**How it behaves:**
- **Failed requests aren't cached.** `raise_for_status()` raises before anything is stored, so a 404 or 500 is retried on the next call.
- **Call `clear_user_cache(user_id)` after updating a user** if you need the change to show up right away.
- **Two threads that miss at the same moment will both fetch.** That's harmless: the last result wins.

**Limitations:**
- **The cache is per-process.** With multiple Gunicorn/uWSGI workers, each has its own cache. If you want one shared cache, use Flask-Caching with a Redis backend instead. I can switch it over if you're already running Redis.
- **Size is unbounded.** Expired entries are overwritten but never evicted. That's fine for a bounded set of users. If `user_id` can be arbitrary input, tell me and I'll add a max size.

I haven't run this, since I can't execute code here.
