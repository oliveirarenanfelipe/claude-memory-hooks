I used the standard library's `functools.lru_cache` with a bounded size. The cache is kept on a private helper, and each caller gets its own copy of the result. That matters because `r.json()` returns a mutable dict. Without the copy, one caller mutating the result would change what every later caller sees.

```python
import copy
from functools import lru_cache

import requests

API = "https://api.example.com"

@lru_cache(maxsize=1024)
def _fetch_user_cached(user_id):
    r = requests.get(f"{API}/users/{user_id}", timeout=5)
    r.raise_for_status()
    return r.json()

def fetch_user(user_id):
    return copy.deepcopy(_fetch_user_cached(user_id))
```

A check to add, e.g. `test_users.py`:

```python
from unittest import mock
import users

def test_fetch_user_is_cached_and_isolated():
    users._fetch_user_cached.cache_clear()
    resp = mock.Mock()
    resp.json.return_value = {"id": 1, "name": "a"}
    with mock.patch("users.requests.get", return_value=resp) as get:
        first = users.fetch_user(1)
        first["name"] = "mutated"
        second = users.fetch_user(1)
    assert get.call_count == 1
    assert second["name"] == "a"
```

I couldn't run this, so the test is not verified.

**Behaviour to be aware of:**
- **No expiry.** Entries stay until they're evicted or the process restarts, so if a user changes upstream, this process keeps serving the old data. If that's not acceptable, tell me the freshness you need and I'll switch to a TTL cache (e.g. `cachetools.TTLCache` if it's installed, or a small timestamped dict).
- **Errors aren't cached.** If `raise_for_status()` raises, nothing is stored, and the next call retries.
- **Keys are type-sensitive.** `fetch_user(1)` and `fetch_user("1")` are separate cache entries.
- **Per process.** Each Flask/gunicorn worker has its own cache. To share one across workers you'd need Redis or similar.
- **Clearing it:** call `users._fetch_user_cached.cache_clear()`, for example in tests or after you know a user changed.

**Assumption:** in-process caching is fine for this app. If you meant a shared cache or HTTP-level caching, say so and I'll adjust.
