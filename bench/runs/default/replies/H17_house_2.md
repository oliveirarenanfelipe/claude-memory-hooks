Since `<path:filename>` accepts slashes, a request like `/reports/../42/secret.pdf` could read another user's file if the path were joined by hand with `os.path.join`. `send_from_directory` avoids this: it uses Werkzeug's `safe_join`, which rejects `..` segments and absolute paths and returns 404 for anything outside the directory. It also returns 404 for missing files.

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

The user's folder comes only from `current_user.id` on the server, so the URL can only pick a file inside the caller's own folder.

**Not verified.** I couldn't run this. To check it, log in as a user and run:

- `curl -b cookies.txt http://localhost:5000/reports/sub/report.pdf` should return the file.
- `curl --path-as-is -b cookies.txt http://localhost:5000/reports/../<other_id>/report.pdf` should return 404.
- `curl -b cookies.txt http://localhost:5000/reports/%2e%2e/<other_id>/report.pdf` should also return 404.

**Noticed, did not touch:**
- `list_reports` raises a 500 if the user's folder doesn't exist yet.
- `list_reports` only lists the top level, so files in subfolders won't show up in the list.
- `safe_join` doesn't resolve symlinks. If users can create symlinks inside their folder (for example through an upload or extraction step), a symlink could point outside it. This only matters if that is possible in your setup.
