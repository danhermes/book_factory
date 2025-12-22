# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create necessary directories and ensure shell scripts have LF line endings
RUN mkdir -p output/outlines output/chapters output/research && \
    find . -name "*.sh" -type f -exec sed -i 's/\r$//' {} \;

# Set environment variables
ENV PYTHONPATH=/app

# Set entrypoint
ENTRYPOINT ["python"]
CMD ["book_cli.py", "outline"]