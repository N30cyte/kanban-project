FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install from the full resolved lock so the build never re-resolves
# transitive dependencies (root cause of past failed builds). Generous
# timeout/retries keep flaky networks from killing the build mid-download.
COPY requirements.txt requirements.lock ./
RUN pip install --no-cache-dir --timeout 60 --retries 10 -r requirements.lock

COPY . .

EXPOSE 8000
# Migrate on every start (idempotent for an already-migrated database),
# then run the server.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
