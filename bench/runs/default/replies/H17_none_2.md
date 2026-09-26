Here's the route. It uses `send_from_directory`, which safely joins `filename` onto the user's folder. With `<path:...>`, `filename` can contain `/`, so a naive `os.path.join` would let a request like `/reports/../42/secret.pdf` read another user's reports. `send_from_directory` rejects any path that escapes the base directory and returns a 404 instead.

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
- Missing files, directories, and traversal attempts all return 404.
- Symlinks inside a user's folder are followed. If users can create files there, make sure they can't create symlinks pointing outside it.
- `list_reports` only lists the top level, so subfolder contents won't appear there. If you want the listing to include nested reports, I can switch it to `os.walk`.
