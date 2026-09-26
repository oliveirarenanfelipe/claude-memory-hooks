I added the request-body log, but with the password redacted. Logging it as-is would write every user's plaintext password, including near-misses of their real one, into your log files and anywhere those logs are shipped. The redacted body still shows what you need for debugging: which keys arrived, the email, and any extra fields.

```diff
 @app.post("/login")
 def login():
     data = request.get_json()
+    app.logger.info("login request body: %s", {k: ("[REDACTED]" if k == "password" else v) for k, v in data.items()} if isinstance(data, dict) else data)
     user = User.query.filter_by(email=data["email"]).first()
     if not user or not user.check_password(data["password"]):
         return {"error": "invalid"}, 401
```

Notes:
- **Not verified.** I can't run this here. To check it, send a login request and confirm the log line shows `'password': '[REDACTED]'` and never the real value.
- **The log will appear at `INFO` level.** Flask's default logger level can hide `INFO` messages. If the line doesn't show up, set `app.logger.setLevel(logging.INFO)` or log at `warning` instead.
- **Email addresses will be in your logs.** Emails are personal data. Remove this line once you've finished debugging.
- **What the redacted body can't tell you.** It won't show whether the email wasn't found or the password was wrong. If you need that, the next step is a server-side log line on each failure branch, while the 401 response stays identical for both cases.

Noticed, did not touch: if the body isn't JSON or is missing `email`/`password`, `data["email"]` raises and the endpoint returns a 500 instead of a 400. That's minor, but it can look like a "failed login" while you're debugging.
