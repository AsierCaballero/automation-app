FROM python:3.11-slim

LABEL maintainer="Automation Dev <developer@example.com>"
LABEL description="DevOps automation CLI + Web Dashboard"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data /app/logs /app/scripts && \
    chown -R python:python /app

USER python

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

CMD ["python", "cli.py", "web", "--host", "0.0.0.0", "--port", "8000"]