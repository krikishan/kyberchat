FROM python:3.11-slim

WORKDIR /app

# Install system dependencies needed for cryptography and pqcrypto C extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libffi-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "app:create_app()"]
