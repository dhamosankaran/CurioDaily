# Stage 1: Builder
FROM --platform=linux/amd64 python:3.9-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Final
FROM --platform=linux/amd64 python:3.9-slim

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV HOST=0.0.0.0
ENV PORT=8080
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=docker
ENV BACKEND_CORS_ORIGINS=[]

# Set work directory
WORKDIR /autonomous_newsletter

# Copy the entire project directory
COPY . /autonomous_newsletter

# Make entrypoint script executable
RUN chmod +x /autonomous_newsletter/entrypoint.sh

# Expose the port the app runs on
EXPOSE 8080

# Use entrypoint script to determine which command to run
ENTRYPOINT ["/autonomous_newsletter/entrypoint.sh"]