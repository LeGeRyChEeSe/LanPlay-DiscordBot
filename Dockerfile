# Use Python 3.12 slim image for better security and smaller size
FROM python:3.12-slim

# Build arguments for version information
ARG VERSION="unknown"
ARG BUILD_DATE
ARG VCS_REF

# Labels for image metadata
LABEL org.opencontainers.image.title="LAN Play Discord Bot" \
      org.opencontainers.image.description="Modern Discord bot for LAN Play servers" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.vendor="LAN Play Bot" \
      org.opencontainers.image.licenses="MIT"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LANG=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create non-root user for security
RUN groupadd -r botuser && useradd -r -g botuser botuser

# Set working directory
WORKDIR /app

# Install system dependencies and build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    locales \
    gcc \
    libc6-dev \
    && locale-gen en_US.UTF-8 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies and remove build tools after
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt && \
    apt-get remove --purge -y gcc libc6-dev && \
    apt-get autoremove -y

# Copy application code
COPY --chown=botuser:botuser . .

# Copy version and changelog files
COPY --chown=botuser:botuser VERSION* ./
COPY --chown=botuser:botuser CHANGELOG* ./

# Create data directory for custom servers
RUN mkdir -p /app/data && chown -R botuser:botuser /app/data

# Switch to non-root user
USER botuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health', timeout=5)" || exit 1

# Expose port for health checks (if needed)
EXPOSE 8080

# Run the application
CMD ["python", "-u", "main.py"]