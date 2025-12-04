FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for OpenCV, PaddleOCR, and other libraries
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgthread-2.0-0 \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ------------------------------------------------------------------
# Python dependencies
# ------------------------------------------------------------------
# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# ------------------------------------------------------------------
# Application code
# ------------------------------------------------------------------
# Copy the entire server directory
COPY . .

# Create necessary directories (will be bind-mounted from host)
RUN mkdir -p debug_crops models

# ------------------------------------------------------------------
# Non-root user setup (to mirror local execution)
# ------------------------------------------------------------------
ARG APP_USER_ID=1000
ARG APP_GROUP_ID=1000

RUN groupadd -g "${APP_GROUP_ID}" appgroup \
    && useradd -u "${APP_USER_ID}" -g appgroup -m appuser \
    && chown -R appuser:appgroup /app

USER appuser

# Expose the port the app runs on
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DEVICE=cpu

# Run the server
CMD ["python", "server.py"]

