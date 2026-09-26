Here's the switch. `send_welcome` now goes through `EmailClient`. That left `_smtp_send`, `smtplib` and `SMTP_HOST` unused in this file, so I removed them.

```diff
-import smtplib
 import textwrap
 from email_client import EmailClient
 
-SMTP_HOST = "localhost"
-
-
-def _smtp_send(to, subject, body):
-    with smtplib.SMTP(SMTP_HOST) as s:
-        s.sendmail("noreply@example.com", [to], f"Subject: {subject}\n\n{body}")
-
 
 def _legacy_format(name):
     return textwrap.fill(f"Dear {name}, welcome aboard!", 40)
 
 
 def send_welcome(user):
     body = f"Hi {user.name}, welcome!"
-    _smtp_send(user.email, "Welcome", body)
+    EmailClient().send(user.email, "Welcome", body)
```

Things I couldn't check from this file alone:

- **Other callers of `_smtp_send`:** it's private by name, but I haven't seen the rest of the codebase. Run `grep -rn "_smtp_send\|SMTP_HOST" .` before merging. If anything else imports them, put those lines back.
- **Sender address:** the old code sent from `noreply@example.com`. `EmailClient().send(to, subject, body)` takes no sender, so the From address is now whatever `EmailClient` uses by default. I haven't seen that code. Check it if the sender matters.
- **Errors:** before, SMTP failures raised `smtplib` exceptions. If `EmailClient` raises something else or returns a status instead, update any caller that catches `smtplib.SMTPException`.

I noticed but didn't touch `_legacy_format`, which isn't called anywhere in this file and looks like leftover dead code. It's a small cleanup candidate, and it's the only reason `textwrap` is still imported.
