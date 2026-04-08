FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/

ENV PYTHONPATH=/app

EXPOSE 5001

# entrypoint.sh seeds the DB (idempotent) then hands off to Flask
# Strip Windows CRLF so the shebang works in Linux (fixes "no such file or directory")
COPY backend/entrypoint.sh ./entrypoint.sh
RUN sed -i 's/\r$//' ./entrypoint.sh && chmod +x ./entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
