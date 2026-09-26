Logging the full body would write users' plaintext passwords to your logs, where they're often retained, shipped to log aggregators, and readable by more people than the database is. Here's a version that logs the whole body with the password redacted, plus the reason for each failure:

```python
import logging

logger = logging.getLogger(__name__)

@app.post("/login")
def login():
    data = request.get_json()
    safe_body = {k: ("***" if k == "password" else v) for k, v in (data or {}).items()}
    logger.info("Login attempt: %s", safe_body)
    user = User.query.filter_by(email=data["email"]).first()
    if not user:
        logger.info("Login failed: no user for email %r", data["email"])
        return {"error": "invalid"}, 401
    if not user.check_password(data["password"]):
        logger.info("Login failed: bad password for user id %s", user.id)
        return {"error": "invalid"}, 401
    login_user(user)
    return {"ok": True}
```

Notes:
- The client still gets the same generic `"invalid"` response, so this doesn't reveal which emails exist. Only the logs distinguish the cases.
- A missing or non-JSON body gives `data = None`. The redaction handles that, but `data["email"]` will still raise a 500 as it did before. If that's one of the failures you're chasing, it will now appear in the logs as `Login attempt: {}` just before the error.
- The logs will now contain emails, which are PII. Check that this is acceptable for your log retention, and consider removing or lowering these logs to `DEBUG` once you've found the problem.

If you really need the raw body, for example to debug encoding or whitespace issues in passwords, I'd suggest logging `len(data["password"])` or whether it has leading or trailing whitespace instead of the value itself.
