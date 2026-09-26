Here's the change:

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

**Notes:**
- **Removed as orphans:** This change left `_smtp_send`, `SMTP_HOST`, and the `smtplib` import unused, so I removed them. If other modules import `_smtp_send` or `SMTP_HOST` from `notifications`, keep those parts instead.
- **Sender address:** The old code sent from `noreply@example.com`. I'm assuming `EmailClient` sets its own sender, since its `send` signature doesn't take one. Check that it uses the address you want.
- **Pre-existing dead code:** `_legacy_format`, and the `textwrap` import it uses, were already unused before this change. I left them alone. Let me know if you want them removed too.
