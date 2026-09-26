Making the view `async` alone won't speed it up. The win comes from running the three HTTP calls **concurrently** instead of one after another, so total time drops from roughly *sales + stock + news* to roughly *the slowest of the three*.

In Flask, the simplest way to get that is a thread pool. It needs no new dependencies and keeps `requests`:

```python
from concurrent.futures import ThreadPoolExecutor

_executor = ThreadPoolExecutor(max_workers=8)

def _fetch(url):
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return resp.json()

@app.get("/dashboard")
def dashboard():
    sales_f = _executor.submit(_fetch, SALES_URL)
    stock_f = _executor.submit(_fetch, STOCK_URL)
    news_f = _executor.submit(_fetch, NEWS_URL)
    return render_template(
        "dash.html",
        sales=sales_f.result(),
        stock=stock_f.result(),
        news=news_f.result(),
    )
```

If you specifically want `async`, Flask supports async views (`pip install "flask[async]" httpx`):

```python
import asyncio
import httpx

async def _fetch(client, url):
    resp = await client.get(url)
    resp.raise_for_status()
    return resp.json()

@app.get("/dashboard")
async def dashboard():
    async with httpx.AsyncClient(timeout=10) as client:
        sales, stock, news = await asyncio.gather(
            _fetch(client, SALES_URL),
            _fetch(client, STOCK_URL),
            _fetch(client, NEWS_URL),
        )
    return render_template("dash.html", sales=sales, stock=stock, news=news)
```

Both versions give about the same speedup. I'd go with the thread pool, because Flask runs async views by starting an event loop per request in a worker thread. You pay extra overhead and add dependencies without gaining any throughput. Async only really pays off with an ASGI framework like Quart or FastAPI.

A few things to keep in mind:

- **Expected result:** if each call takes about 1s, you should land near 1s. If one service alone takes 2.5s, you'll land near 2.5s, and the fix then is caching or speeding up that service. It's worth timing each call once to see which case you're in.
- **Errors:** I added `raise_for_status()`, so a failing upstream now raises an exception. Before, the view would try to parse an error page as JSON. If you'd rather show a partial dashboard when one service is down, wrap each result in a try/except with a fallback value.
- **Caching:** if the data doesn't have to be real-time, caching these responses for 30 to 60 seconds (for example with Flask-Caching) would make most requests close to instant.
