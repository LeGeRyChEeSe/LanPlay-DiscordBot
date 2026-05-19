# Use Python 3.12 slim image for better security and smaller size
FROM python:3.13-slim

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
    LC_ALL=en_US.UTF-8

# Create non-root user for security
RUN groupadd -r botuser && useradd -r -g botuser botuser

# Set working directory
WORKDIR /app

# Install system dependencies and uv installer dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    locales \
    gcc \
    libc6-dev \
    curl \
    ca-certificates \
    && locale-gen en_US.UTF-8 \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && export PATH="/root/.local/bin:$PATH"

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with uv and remove build tools after
RUN uv pip install -r requirements.txt \
    && apt-get remove --purge -y gcc libc6-dev curl ca-certificates \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY --chown=botuser:botuser . .

# Copy version and changelog files
COPY --chown=botuser:botuser VERSION* ./
COPY --chown=botuser:botuser CHANGELOG* ./

# Create data directory for custom servers
RUN mkdir -p /app/data && chown -R botuser:botuser /app/data

# Switch to non-root user
USER botuser

# Health check - just check if the process is running since it's not a web server
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD pgrep -f "python -u main.py" || exit 1

# Run the application
CMD ["python", "-u", "main.py"]
