Here's the route. It uses `send_from_directory`, which resolves `filename` safely inside the user's folder, so a request like `/reports/../2/secret.pdf` returns 404 instead of reading another user's report.

```python
import os
from flask import Flask, send_from_directory
from flask_login import login_required, current_user

app = Flask(__name__)
REPORTS_DIR = "/srv/app/reports"


@app.route("/reports")
@login_required
def list_reports():
    user_dir = os.path.join(REPORTS_DIR, str(current_user.id))
    return {"files": os.listdir(user_dir)}


@app.route("/reports/<path:filename>")
@login_required
def get_report(filename):
    user_dir = os.path.join(REPORTS_DIR, str(current_user.id))
    return send_from_directory(user_dir, filename)
```

Notes:

- **Why not `send_file(os.path.join(user_dir, filename))`?** `<path:...>` accepts slashes, so `..` segments would let a user escape their own folder. `send_from_directory` uses `werkzeug.security.safe_join` internally. It rejects `..`, absolute paths, and (on Windows) drive letters and backslashes, and returns 404 if the file doesn't exist.
- **Symlinks:** `safe_join` checks the path string, not where symlinks point. If users can create symlinks inside their report folders, add a check that `os.path.realpath` of the result stays under `os.path.realpath(user_dir)`.
- **Downloads:** to force a download prompt instead of showing the file in the browser (e.g. PDFs), pass `as_attachment=True`.
- **Listing:** `list_reports` still uses `os.listdir`, so it only shows the top level. It won't list files in subfolders. I can change it to use `os.walk` and return relative paths if you want the listing to match the new route.
