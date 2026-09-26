Here's the diff for `notifications.py`:

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

`send_welcome` was the only caller of `_smtp_send` in this file, so I removed `_smtp_send`, `SMTP_HOST` and the `smtplib` import along with it.

**Assumptions I couldn't check:**
- Nothing outside this file imports `_smtp_send` or `SMTP_HOST`. It's underscore-private, but I only have this file. A quick `grep -r "_smtp_send\|SMTP_HOST"` would confirm it. If anything turns up, put those lines back.
- The old code sent from `noreply@example.com`. I'm assuming `EmailClient` sets its own sender. If it doesn't, welcome emails may now go out from a different address.

I haven't run this, and there are no tests in what you shared. The change is one line, but the check that matters is sending a welcome email in a dev environment and confirming it arrives with the right subject and sender.

**Noticed, didn't touch:** `_legacy_format` has no callers in this file and already looked unused before this change. If nothing else uses it, it and the `textwrap` import can go in a separate cleanup.
