Here's the change to `send_welcome`:

```diff
 def send_welcome(user):
     body = f"Hi {user.name}, welcome!"
-    _smtp_send(user.email, "Welcome", body)
+    EmailClient().send(user.email, "Welcome", body)
```

`EmailClient` is already imported, so nothing else is needed.

After this change, nothing in this file calls `_smtp_send` (or `_legacy_format`). I didn't delete either one because other modules might import them. If they're unused elsewhere, you can remove both, along with the `smtplib`, `textwrap`, and `SMTP_HOST` lines.

The sender address is no longer set here. The old code hardcoded `noreply@example.com`. If `EmailClient` doesn't default to the right sender, you'll need to configure that on the client.
