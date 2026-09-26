Here's the route. It uses `send_from_directory`, which runs the path through `werkzeug.security.safe_join`. That matters here because `<path:filename>` accepts slashes, so a request like `/reports/../42/secret.pdf` could otherwise reach another user's folder. `safe_join` rejects `..` segments and absolute paths and returns a 404 instead.

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
- Missing files and traversal attempts both return 404, so the route doesn't reveal whether a file exists outside the user's folder.
- `safe_join` doesn't resolve symlinks. If anything could place a symlink inside a user's folder that points elsewhere, it would be followed. If that's possible in your setup, tell me and I'll add a `realpath` check.
- `list_reports` only lists the top level of the user's folder, so files in subfolders won't appear there. If you want them listed, it would need to switch to `os.walk`.
