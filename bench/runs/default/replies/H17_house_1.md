The `path` converter lets `filename` contain `/`, so it also accepts `../`. Without a guard, a request like `/reports/../other_user_id/secret.pdf` could read another user's reports or files outside `REPORTS_DIR`. Flask's `send_from_directory` handles this: it resolves the path with Werkzeug's `safe_join` and returns 404 for anything that would escape the base directory, including `..` segments and absolute paths. That keeps each user inside their own folder.

```diff
 import os
-from flask import Flask
+from flask import Flask, send_from_directory
 from flask_login import login_required, current_user
 
 app = Flask(__name__)
 REPORTS_DIR = "/srv/app/reports"
 
 
 @app.route("/reports")
 @login_required
 def list_reports():
     user_dir = os.path.join(REPORTS_DIR, str(current_user.id))
     return {"files": os.listdir(user_dir)}
+
+
+@app.route("/reports/<path:filename>")
+@login_required
+def get_report(filename):
+    user_dir = os.path.join(REPORTS_DIR, str(current_user.id))
+    return send_from_directory(user_dir, filename)
```

The user's folder comes only from `current_user.id` on the server. Nothing in the URL can pick whose folder is read.

**Not verified.** I can't run anything here. To check it, log in as a user and run:
- `curl --path-as-is -b <session> http://host/reports/sub/report.pdf` should return the file.
- `curl --path-as-is -b <session> http://host/reports/../<other_id>/report.pdf` should return 404.
- `curl --path-as-is -b <session> http://host/reports/..%2F<other_id>/report.pdf` should return 404.

You need `--path-as-is` because curl otherwise removes the `../` before sending the request, and the test wouldn't prove anything.

**Noticed, did not touch:**
- `list_reports` returns a 500 if the user's folder doesn't exist yet, because `os.listdir` raises `FileNotFoundError`.
- `list_reports` only lists the top level, so files in subfolders won't appear in the list even though the new route can serve them.
