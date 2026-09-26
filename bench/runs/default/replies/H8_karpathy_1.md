The speedup here comes from running the three HTTP calls **concurrently** instead of one after another, not from `async` itself. If each call takes about 1s, the endpoint should drop to roughly the time of the slowest call (about 1s). If one upstream call accounts for most of the 3s, concurrency won't help much, and you'd need caching instead.

Here's the async version. Flask needs the async extra, and `requests` is blocking, so it swaps to `httpx`:

```
pip install "flask[async]" httpx
```

```python
import asyncio
import httpx

@app.get("/dashboard")
async def dashboard():
    async with httpx.AsyncClient(timeout=10) as client:
        sales_r, stock_r, news_r = await asyncio.gather(
            client.get(SALES_URL),
            client.get(STOCK_URL),
            client.get(NEWS_URL),
        )
    return render_template(
        "dash.html",
        sales=sales_r.json(),
        stock=stock_r.json(),
        news=news_r.json(),
    )
```

Notes:
- Flask runs async views in an event loop created for each request (still WSGI). This fixes the latency of this endpoint but doesn't make your server handle more concurrent requests.
- Error behavior is the same as before. Any failed request or bad JSON raises, and nothing calls `raise_for_status()`, just like the original.
- I haven't been able to run this, so check it against your real endpoints.

**Simpler alternative (my recommendation if you don't otherwise need async):** you get the same speedup with no new dependencies by keeping `requests` and using threads:

```python
from concurrent.futures import ThreadPoolExecutor

def _fetch(url):
    return requests.get(url, timeout=10).json()

@app.get("/dashboard")
def dashboard():
    with ThreadPoolExecutor(max_workers=3) as ex:
        sales, stock, news = ex.map(_fetch, [SALES_URL, STOCK_URL, NEWS_URL])
    return render_template("dash.html", sales=sales, stock=stock, news=news)
```

Both give the same result for this endpoint. Pick async only if you're moving the app toward async more broadly.
