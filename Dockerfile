FROM python:3.11-slim

# Install system dependencies for WeasyPrint and Playwright
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    fonts-liberation \
    fonts-dejavu-core \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (chromium only, for social audit)
RUN playwright install chromium --with-deps 2>/dev/null || true

# Copy application code
COPY . .

# Create output directory
RUN mkdir -p /data/sessions

# Expose port (Railway sets PORT env var)
EXPOSE 8080

# Start the webhook server
CMD python retell_webhook.py --port ${PORT:-8080} --output-dir /data/sessions
