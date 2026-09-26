Logging the full body would write plaintext passwords to your logs, including near-misses of real passwords from typos. Logs tend to be widely readable and long-retained, so this is a real credential leak. Here's a version that logs everything useful except the password, and records *why* each login failed:

```python
import logging

logger = logging.getLogger(__name__)

REDACTED_FIELDS = {"password"}


def _redact(data):
    if not isinstance(data, dict):
        return data
    return {k: ("[REDACTED]" if k in REDACTED_FIELDS else v) for k, v in data.items()}


@app.post("/login")
def login():
    data = request.get_json(silent=True)
    logger.info(
        "Login attempt: body=%r content_type=%s remote_addr=%s",
        _redact(data), request.content_type, request.remote_addr,
    )

    if not isinstance(data, dict) or "email" not in data or "password" not in data:
        logger.warning("Login failed: malformed body")
        return {"error": "invalid"}, 400

    user = User.query.filter_by(email=data["email"]).first()
    if not user:
        logger.warning("Login failed: no user for email=%r", data["email"])
        return {"error": "invalid"}, 401
    if not user.check_password(data["password"]):
        logger.warning("Login failed: bad password for user_id=%s", user.id)
        return {"error": "invalid"}, 401

    login_user(user)
    return {"ok": True}
```

What this gives you for debugging:

- **The body minus the password**, so you can spot wrong field names, extra whitespace or casing in the email, or unexpected payload shapes.
- **Content type**: a common cause of "failed" logins is a client not sending `application/json`. Before, `get_json()` would then error out or return `None`, and `data["email"]` would 500. That case now returns a logged 400.
- **The failure reason**: "no such user" vs. "wrong password." These are only in the server logs; the client still gets the same generic `invalid` response, so you don't leak which emails exist.

If you need to check whether the password arrives intact (e.g., encoding or trimming problems), log `len(data["password"])` temporarily rather than the value itself.

Emails in logs are still personal data. If that's a concern under your retention policy, log a hash of the email instead.
