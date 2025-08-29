FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -e .

# Copy application code
COPY tiktok_ads_mcp/ ./tiktok_ads_mcp/
COPY examples/ ./examples/
COPY *.md ./
COPY LICENSE ./

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check (Fly.io handles this via fly.toml)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the remote server
CMD ["python", "-m", "tiktok_ads_mcp.remote_main", "--host", "0.0.0.0", "--port", "8000"]