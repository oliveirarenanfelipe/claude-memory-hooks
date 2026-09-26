The speedup comes from running the three calls **concurrently** instead of one after another. Right now the total time is roughly `sales + stock + news`. Run in parallel, it becomes roughly `max(sales, stock, news)`. Async is one way to do that. Here's the async version:

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

This requires `pip install "flask[async]" httpx`. `requests` is blocking, so it can't be awaited; `httpx` is the async-capable replacement.

**Things to know:**

- **Flask isn't an async server.** Under WSGI, Flask runs each async view in its own event loop inside a worker thread. You still get concurrency *within* this request, which is the win here. But it doesn't let a worker handle more requests at once, and there's a small per-request overhead.
- **Simpler option with no new dependencies:** if you'd rather keep `requests` and a sync view, a thread pool gives the same speedup:

  ```python
  from concurrent.futures import ThreadPoolExecutor

  _pool = ThreadPoolExecutor(max_workers=8)

  def _fetch(url):
      return requests.get(url, timeout=10).json()

  @app.get("/dashboard")
  def dashboard():
      sales, stock, news = _pool.map(_fetch, [SALES_URL, STOCK_URL, NEWS_URL])
      return render_template("dash.html", sales=sales, stock=stock, news=news)
  ```

  I'd pick this one for a standard Flask/WSGI deployment. Use the async version if you're already on an ASGI setup or plan to move to one (e.g. Quart).
- **Check where the 3s actually goes.** If one upstream alone takes ~2.5s, parallelizing only saves the other ~0.5s. In that case, caching that response for a short time will help far more. I haven't been able to run or time this, so it's worth logging each call's duration first.
- **Error behavior is unchanged.** Like the original, neither version calls `raise_for_status()`. A non-2xx response with a non-JSON body will still fail at `.json()`. With `gather`, the first exception propagates and the other results are discarded.
