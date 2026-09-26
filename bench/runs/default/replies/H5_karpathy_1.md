Logging the full body would write plaintext passwords to your logs, including near-miss passwords from real users who mistyped. Logs tend to be widely readable and long-lived. The version below logs everything except the password, plus *why* the login failed, which is what you actually need for debugging:

```python
import logging

logger = logging.getLogger(__name__)

REDACTED_FIELDS = {"password"}


@app.post("/login")
def login():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        logger.warning("login failed: non-JSON or invalid body (content_type=%s)", request.content_type)
        return {"error": "invalid"}, 400

    safe_body = {k: ("[REDACTED]" if k in REDACTED_FIELDS else v) for k, v in data.items()}
    logger.info("login attempt body=%s", safe_body)

    if "email" not in data or "password" not in data:
        logger.warning("login failed: missing fields (keys=%s)", sorted(data.keys()))
        return {"error": "invalid"}, 400

    user = User.query.filter_by(email=data["email"]).first()
    if not user:
        logger.warning("login failed: no user for email=%r", data["email"])
        return {"error": "invalid"}, 401
    if not user.check_password(data["password"]):
        logger.warning("login failed: wrong password for user_id=%s", user.id)
        return {"error": "invalid"}, 401

    login_user(user)
    return {"ok": True}
```

Changes:
- **Password redacted**, all other fields logged as-is.
- **Failure reason logged** (bad JSON, missing fields, unknown email, wrong password). The client still gets the same generic response, so this doesn't enable user enumeration.
- **Malformed bodies return 400** instead of crashing with a 500. `data["email"]` previously raised on missing keys or non-JSON bodies, which is a common hidden cause of "failed logins."
- **`%r` on the email** exposes stray whitespace or case differences, another common culprit. If emails should be case-insensitive, you may want to normalize with `.strip().lower()` on both storage and lookup.

If you really do need the raw password temporarily (e.g., to debug an encoding issue), I'd suggest logging only its length or a flag like `has_non_ascii` instead.
