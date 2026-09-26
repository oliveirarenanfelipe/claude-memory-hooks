The likely cause is that the three requests run **one after another**, so the total time is the sum of the three. This is a hypothesis, since I can't run or profile anything. Running them concurrently would make the total roughly equal to the slowest single call.

You don't need `async` for that. An `async def` view in Flask needs `flask[async]` plus an async HTTP client like `httpx` or `aiohttp`. Flask also still runs each async view inside a worker thread with its own event loop, so you'd add dependencies and complexity for the same result. A thread pool with the `requests` library you already use gives the concurrency with a smaller change:

```python
from concurrent.futures import ThreadPoolExecutor

@app.get("/dashboard")
def dashboard():
    urls = (SALES_URL, STOCK_URL, NEWS_URL)
    with ThreadPoolExecutor(max_workers=len(urls)) as pool:
        sales, stock, news = pool.map(
            lambda url: requests.get(url, timeout=10).json(), urls
        )
    return render_template("dash.html", sales=sales, stock=stock, news=news)
```

Behavior stays the same:
- The results come back in the same order.
- The timeout per call is still 10s.
- If any call raises, `pool.map` re-raises that exception here, as the current code does.

**Check it before trusting it.** Time each call on its own, for example by wrapping each `requests.get` with `time.perf_counter()`:
- If each call takes about 1s, this should bring the endpoint to about 1s.
- If one call takes about 2.8s by itself, the endpoint will stay near 2.8s. The fix then belongs to that upstream service, or to caching its response, not to concurrency.

If you still want a real `async` version, for example because you're moving to Quart or FastAPI, tell me and I'll write it with `httpx.AsyncClient` and `asyncio.gather`.
