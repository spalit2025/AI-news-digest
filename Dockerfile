FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for lxml and reportlab
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libxml2-dev \
    libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create reports directory
RUN mkdir -p reports

ENV PYTHONUNBUFFERED=1

CMD sh -c "echo 'Starting on port ${PORT:-8080}' && exec gunicorn app:app --bind 0.0.0.0:${PORT:-8080} --workers 2 --timeout 300 --access-logfile - --error-logfile -"
