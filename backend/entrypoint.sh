#!/bin/sh
set -e

echo ">>> Initialising database…"
python -m backend.db.init_db

echo ">>> Starting Flask on port 5001…"
exec python -m backend.app