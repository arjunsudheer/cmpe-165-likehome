FROM python:3.11-slim


ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app/backend

RUN apt-get update && apt-get install -y \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/backend

EXPOSE 5000

CMD ["/bin/sh", "-c", "python /app/backend/db/init_db.py && python run.py"]