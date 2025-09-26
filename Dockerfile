# Multi-stage Docker build for Agentic Red-Team Manager
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY setup.py pyproject.toml ./

# Install the package
RUN pip install -e .

# Create non-root user
RUN useradd --create-home --shell /bin/bash redteam
USER redteam

# Expose port for API server
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["uvicorn", "src.api.server:app", "--host", "0.0.0.0", "--port", "8000"]

# Development stage
FROM base as development

USER root

# Install development dependencies
COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt

# Install additional development tools
RUN apt-get update && apt-get install -y \
    vim \
    tmux \
    htop \
    && rm -rf /var/lib/apt/lists/*

USER redteam

# Override command for development
CMD ["uvicorn", "src.api.server:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM base as production

# Copy configuration files
COPY configs/ ./configs/

# Set production environment
ENV ENVIRONMENT=production

# Use production command
CMD ["uvicorn", "src.api.server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]