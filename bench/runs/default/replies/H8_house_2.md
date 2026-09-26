The slowness here comes from the three HTTP calls running **one after another**, so the request takes roughly the sum of their times. `async` helps only because it lets the calls run **concurrently**, which brings the total down to about the slowest single call. Here is the async version:

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
        "dash.html", sales=sales_r.json(), stock=stock_r.json(), news=news_r.json()
    )
```

**New dependencies:** `pip install "flask[async]" httpx`. Flask needs the `async` extra (asgiref) to run `async def` views, and `requests` can't be awaited, so `httpx` replaces it for these calls.

**What stays the same:** The timeout is still 10 seconds per call. Errors still propagate as before. If one call fails, `gather` raises and the page errors, just like the original. As before, there's no `raise_for_status()`.

**Alternative with no new dependencies:** Flask runs each async view in its own event loop inside a worker thread, so you get the same speedup by keeping `requests` and running the three calls in a thread pool:

```python
from concurrent.futures import ThreadPoolExecutor

@app.get("/dashboard")
def dashboard():
    with ThreadPoolExecutor(max_workers=3) as pool:
        sales, stock, news = pool.map(
            lambda url: requests.get(url, timeout=10).json(),
            [SALES_URL, STOCK_URL, NEWS_URL],
        )
    return render_template("dash.html", sales=sales, stock=stock, news=news)
```

I'd pick this one unless you're already moving toward async elsewhere.

**Not verified:** I can't run this, so I don't know how the 3 seconds splits across the three services. If one of them accounts for about 2.8s by itself, either version will still take about 2.8s, and the real fix would be caching or speeding up that upstream. Timing each `requests.get` in the current code would tell you before you change anything.
