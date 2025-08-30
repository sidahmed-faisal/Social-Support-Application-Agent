FROM python:3.11-slim

# System setup
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1


WORKDIR /app

# Install Python dependencies first for better layer caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Create non-root user and switch
RUN addgroup --system app && adduser --system --ingroup app app \
 && chown -R app:app /app
USER app

# App port
EXPOSE 8000

# Healthcheck (hits Swagger UI)
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=5 \
  CMD curl -fsS "http://localhost:${PORT:-8000}/docs" || exit 1

# Run the API
CMD uvicorn api.server:app --host 0.0.0.0 --port ${PORT:-8000}