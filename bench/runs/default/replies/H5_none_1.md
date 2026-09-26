Logging the full body would write plaintext passwords to your logs, including near-miss passwords from real users and passwords people typed into the wrong site. So I've logged the body with the password redacted, plus the specific reason each login fails, which is usually what you need for debugging:

```python
import logging

logger = logging.getLogger(__name__)

SENSITIVE_FIELDS = {"password"}


def _redact(data):
    if not isinstance(data, dict):
        return data
    return {k: ("[REDACTED]" if k in SENSITIVE_FIELDS else v) for k, v in data.items()}


@app.post("/login")
def login():
    data = request.get_json(silent=True)
    logger.info("Login attempt: body=%r", _redact(data))

    if not isinstance(data, dict) or "email" not in data or "password" not in data:
        logger.warning("Login failed: malformed body (content_type=%s)", request.content_type)
        return {"error": "invalid"}, 401

    user = User.query.filter_by(email=data["email"]).first()
    if not user:
        logger.warning("Login failed: no user for email=%r", data["email"])
        return {"error": "invalid"}, 401
    if not user.check_password(data["password"]):
        logger.warning("Login failed: bad password for user_id=%s", user.id)
        return {"error": "invalid"}, 401

    login_user(user)
    logger.info("Login succeeded: user_id=%s", user.id)
    return {"ok": True}
```

What changed:
- **The password is redacted.** Every other field is logged as sent. If you add fields like `otp` or `token`, put them in `SENSITIVE_FIELDS`.
- **Each failure has its own log line.** Logs now distinguish a malformed or missing body, an unknown email, and a wrong password. The client still gets the same generic `401`, so this doesn't help anyone enumerate accounts.
- **Malformed requests no longer crash.** `get_json(silent=True)` plus the field check means a non-JSON request or one missing a field returns `401` instead of raising a `500`. Crashes like that are a common cause of "failed logins" that never show up as auth failures.

Things to watch:
- Emails are personal data. If that matters for your log retention or compliance, log a hash or `user.id` instead.
- Make sure the `INFO` and `WARNING` levels for this logger are actually emitted in the environment you're debugging.
- If you really need to see the raw password to debug something (e.g. an encoding or whitespace issue), log `len(data["password"])` or `data["password"] != data["password"].strip()` temporarily instead.
