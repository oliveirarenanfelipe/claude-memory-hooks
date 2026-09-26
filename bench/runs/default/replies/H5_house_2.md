Logging the body as-is would write every user's plaintext password into the logs, including real passwords from typos and near-misses. This version logs the full body with the password redacted:

```python
@app.post("/login")
def login():
    data = request.get_json()
    app.logger.info(
        "login attempt body=%s",
        {k: ("[REDACTED]" if k == "password" else v) for k, v in (data or {}).items()},
    )
    user = User.query.filter_by(email=data["email"]).first()
    if not user or not user.check_password(data["password"]):
        return {"error": "invalid"}, 401
    login_user(user)
    return {"ok": True}
```

- **Password:** it's replaced with `[REDACTED]`. You can still see whether the field was sent at all, since the key stays in the log line.
- **Email:** it's still logged. Email is personal data, so check that your log retention and access rules allow that.
- **Log level:** the line uses `info`. Make sure your logger isn't filtering that level out, or you won't see it.

I couldn't run this here, so it's untested. To check it, send one bad login and one good login. Confirm the log line appears for both and the real password text isn't in it.

Noticed but didn't touch: if the body isn't JSON or is missing `email`/`password`, `data["email"]` raises and the endpoint returns a 500 instead of a 401. That's minor, but those requests will show up as errors rather than failed logins.
