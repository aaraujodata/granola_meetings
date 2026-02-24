FROM python:3.12-slim

WORKDIR /app

# Install dependencies (both core pipeline + web backend)
COPY requirements.txt /app/requirements-core.txt
COPY web/backend/requirements.txt /app/requirements-web.txt
RUN pip install --no-cache-dir -r /app/requirements-core.txt -r /app/requirements-web.txt

# Copy application code
COPY src/ /app/src/
COPY scripts/ /app/scripts/
COPY web/backend/ /app/web/backend/
COPY granola_pipeline.py /app/granola_pipeline.py

ENV PYTHONPATH=/app
WORKDIR /app/web/backend

# Entrypoint builds a combined CA bundle if custom certs exist in .ca-certs/
COPY web/backend/docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh
ENTRYPOINT ["/app/docker-entrypoint.sh"]

EXPOSE 8000
