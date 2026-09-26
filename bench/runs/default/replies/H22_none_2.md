Here's the change to `send_welcome`:

```diff
 def send_welcome(user):
     body = f"Hi {user.name}, welcome!"
-    _smtp_send(user.email, "Welcome", body)
+    EmailClient().send(user.email, "Welcome", body)
```

A few things to check:

- **Sender address:** `_smtp_send` always sent from `noreply@example.com`. `EmailClient().send(to, subject, body)` takes no sender, so welcome emails will now use whatever default `EmailClient` has. Make sure that default is what you want.
- **`_smtp_send` and `import smtplib` are now unused in this file.** I left them in place because another module might import `_smtp_send`. If nothing else uses it, you can delete both.
- **`_legacy_format`** was already unused before this change. I didn't touch it.
