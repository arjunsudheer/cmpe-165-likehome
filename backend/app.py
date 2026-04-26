import os

from backend import create_app
from backend.scheduler import start_scheduler

app = create_app()

if __name__ == "__main__":
    # 0.0.0.0 is required in Docker; falls back fine for local dev too
    debug = os.environ.get("FLASK_DEBUG", "").lower() in {"1", "true", "yes", "on"}
    
    # In debug mode, Flask starts two processes (one for the reloader).
    # We only want to start the scheduler in the main process to avoid duplicate jobs.
    if not debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        start_scheduler()
        
    app.run(host="0.0.0.0", port=5001, debug=debug)
