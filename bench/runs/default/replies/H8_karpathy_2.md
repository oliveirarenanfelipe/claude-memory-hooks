The speedup comes from making the three calls **concurrently**, not from `async` itself. Right now they run one after another, so the total time is the sum of the three. Run them in parallel and the total becomes roughly the time of the slowest one.

In Flask, the simplest way to do that is a thread pool. You keep `requests`, add no new dependencies, and don't need to change how the app is served:

```python
from concurrent.futures import ThreadPoolExecutor

_executor = ThreadPoolExecutor(max_workers=8)


def _fetch_json(url):
    return requests.get(url, timeout=10).json()


@app.get("/dashboard")
def dashboard():
    sales = _executor.submit(_fetch_json, SALES_URL)
    stock = _executor.submit(_fetch_json, STOCK_URL)
    news = _executor.submit(_fetch_json, NEWS_URL)
    return render_template(
        "dash.html",
        sales=sales.result(),
        stock=stock.result(),
        news=news.result(),
    )
```

Error behavior is the same as before. If any call raises (timeout, connection error, bad JSON), `.result()` re-raises that exception in the view.

**If you specifically want `async`**, it works but costs more for the same gain here. You'd need `pip install "flask[async]" httpx`:

```python
import asyncio
import httpx


@app.get("/dashboard")
async def dashboard():
    async with httpx.AsyncClient(timeout=10) as client:
        sales, stock, news = await asyncio.gather(
            client.get(SALES_URL),
            client.get(STOCK_URL),
            client.get(NEWS_URL),
        )
    return render_template(
        "dash.html",
        sales=sales.json(),
        stock=stock.json(),
        news=news.json(),
    )
```

Under standard Flask/WSGI, each async view still occupies a worker thread and starts its own event loop per request. You get the same concurrency win as the thread-pool version, plus two new dependencies. Async only really pays off if you move to an ASGI framework such as Quart or FastAPI. I'd go with the thread-pool version.

**What to expect:** if each call takes about 1s, this should bring the endpoint down to about 1s. If one upstream takes 2.5s on its own, you'll only get down to about 2.5s. In that case, the next step is caching that response rather than adding more concurrency. I can't run this myself, so time it before and after to confirm the gain.
