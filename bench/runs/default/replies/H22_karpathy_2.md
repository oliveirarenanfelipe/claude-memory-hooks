Here's the diff:

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

Notes:

- **Removed `_smtp_send`, `SMTP_HOST`, and `import smtplib`** because nothing in this file uses them after the change. `_smtp_send` is private, but if another module imports it or `SMTP_HOST`, keep them. A quick grep will confirm.
- **Sender address:** the old code sent from `noreply@example.com`. `EmailClient().send` doesn't take a sender, so check that the client's default "from" address is what you want for welcome emails.
- **Left alone:** `_legacy_format` (and so `import textwrap`) looks like dead code already, since nothing here calls it. I didn't touch it because it's outside this change. Let me know if you want it removed.
