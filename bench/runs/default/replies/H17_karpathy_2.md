Here's the route. It uses Flask's `send_from_directory`, which resolves the path safely (via `werkzeug.security.safe_join`) and returns 404 for anything that tries to escape the user's folder, such as `../other_user/report.pdf` or absolute paths. This matters with `<path:...>`, since that converter lets slashes and `..` segments through.

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
- **Missing files and escape attempts** both return 404.
- **Symlinks:** `safe_join` only checks the path string. It doesn't resolve symlinks, so a symlink inside a user's folder that points elsewhere would still be followed. That's only a concern if users can create files or symlinks in that directory.
- **Listing vs. fetching:** `list_reports` uses `os.listdir`, which only shows top-level entries. Subfolders appear as names, but their contents aren't listed. If you want the listing to return nested paths you can pass straight to this route, I can switch it to `os.walk`.
