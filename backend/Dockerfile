FROM python:3.11-slim

WORKDIR /app

# Install deps first — separate layer so it is cached unless requirements change
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend package into /app/backend/ so "import backend" resolves
COPY backend/ ./backend/

# /app must be on PYTHONPATH so the backend package is discoverable
ENV PYTHONPATH=/app

EXPOSE 5001

# entrypoint.sh seeds the DB (idempotent) then hands off to Flask
COPY backend/entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]