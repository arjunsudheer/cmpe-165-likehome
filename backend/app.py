import os

from backend import create_app
from backend.scheduler import start_scheduler

app = create_app()
start_scheduler()

if __name__ == "__main__":
    # 0.0.0.0 is required in Docker; falls back fine for local dev too
    debug = os.environ.get("FLASK_DEBUG", "").lower() in {"1", "true", "yes", "on"}
    app.run(host="0.0.0.0", port=5001, debug=debug)
