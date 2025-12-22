# Docker Compose Migration Plan for Book Factory

This document outlines the comprehensive plan for containerizing the Book Factory project using Docker Compose. The migration will enable consistent deployment across environments, simplified setup, and improved collaboration.

## Table of Contents

1. [Project Structure Analysis](#project-structure-analysis)
2. [Docker Compose Architecture](#docker-compose-architecture)
3. [Service Definitions](#service-definitions)
4. [Dockerfile Specifications](#dockerfile-specifications)
5. [Configuration Details](#configuration-details)
6. [Implementation Steps](#implementation-steps)
7. [Usage Instructions](#usage-instructions)
8. [Troubleshooting Tips](#troubleshooting-tips)

## Project Structure Analysis

The Book Factory project is a Python-based application for generating book content using AI. The key components include:

### Core Components

- **CLI Interface** (`book_cli.py`): Main entry point for the application
- **Chapter Generation** (`run_chapter.py`): Script for generating individual chapters
- **Book Writing Flow** (`src/book_writing_flow/main.py`): Core application logic
- **Book Layout** (`src/book_layout`): Professional-grade typesetting system for final publication
- **Book Quick Draft** (`src/book_quick_draft`): Rapid prototyping and draft generation system

### Dependencies

- **AI Services**: OpenAI API for content generation
- **Web Framework**: FastAPI for potential API endpoints
- **Database**: SQLAlchemy for data persistence
- **Utilities**: Various Python libraries for processing and formatting
- **Typesetting**: LaTeX, pandoc, and related tools for PDF generation

### Data Flow

1. User initiates book generation via CLI
2. System generates book outline
3. Individual chapters are generated based on the outline
4. Output is saved to the filesystem
5. Book layout or quick draft services can be used to generate PDFs

## Docker Compose Architecture

The Docker Compose setup will consist of the following components:

### Services

1. **book_factory**: Main application container
   - Contains the core Python application
   - Exposes CLI commands via entrypoint

2. **book_layout**: Professional typesetting service
   - Converts Markdown to beautifully formatted PDFs
   - Uses LaTeX and pandoc for high-quality output
   - Optimized for final publication

3. **book_quick_draft**: Rapid draft generation service
   - Quickly converts Markdown to readable PDFs
   - Simpler workflow for early drafts and previews
   - Includes cover page integration

4. **web** (optional future extension):
   - FastAPI web interface for the application
   - Exposes HTTP endpoints

### Volumes

1. **output_data**: Persistent volume for generated content
   - Maps to `/app/output` in the containers
   - Preserves generated books across container restarts

2. **config_data**: Volume for configuration files
   - Maps to `/app/.env` in the containers
   - Allows configuration changes without rebuilding

3. **source_volumes**: Volumes for source code
   - Maps source directories to containers for development
   - Enables real-time code changes without rebuilding

### Networks

1. **app-network**: Internal network for service communication
   - Isolates application traffic
   - Enables secure communication between services

## Service Definitions

### book_factory Service

```yaml
book_factory:
  build:
    context: .
    dockerfile: Dockerfile
  volumes:
    - ./output:/app/output
    - ./.env:/app/.env
  environment:
    - PYTHONPATH=/app
  command: ["python", "book_cli.py"]
  networks:
    - app-network
```

### book_layout Service

```yaml
book_layout:
  build:
    context: .
    dockerfile: Dockerfile.book_layout
  volumes:
    - ./output:/app/output
    - ./src/book_layout:/app/src/book_layout
  environment:
    - PYTHONPATH=/app
  networks:
    - app-network
```

### book_quick_draft Service

```yaml
book_quick_draft:
  build:
    context: .
    dockerfile: Dockerfile.book_quick_draft
  volumes:
    - ./output:/app/output
    - ./src/book_quick_draft:/app/src/book_quick_draft
  environment:
    - PYTHONPATH=/app
  networks:
    - app-network
```

### web Service (Future Extension)

```yaml
web:
  build:
    context: .
    dockerfile: Dockerfile.web
  ports:
    - "8000:8000"
  volumes:
    - ./output:/app/output
    - ./.env:/app/.env
  environment:
    - PYTHONPATH=/app
  command: ["uvicorn", "src.web.main:app", "--host", "0.0.0.0", "--port", "8000"]
  depends_on:
    - book_factory
  networks:
    - app-network
```

## Dockerfile Specifications

### Main Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p output/outlines output/chapters output/research

# Set environment variables
ENV PYTHONPATH=/app

# Set entrypoint
ENTRYPOINT ["python"]
CMD ["book_cli.py"]
```

### Book Layout Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    texlive-full \
    pandoc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the book_layout module
COPY src/book_layout /app/src/book_layout

# Create necessary directories
RUN mkdir -p /app/output/chapters /app/output/outlines

# Set environment variables
ENV PYTHONPATH=/app

# Set working directory to book_layout
WORKDIR /app/src/book_layout

# Make build script executable
RUN chmod +x build.sh

# Default command
CMD ["./build.sh"]
```

### Book Quick Draft Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    texlive-xetex \
    pandoc \
    imagemagick \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Configure ImageMagick policy to allow PDF operations
RUN sed -i 's/rights="none" pattern="PDF"/rights="read|write" pattern="PDF"/' /etc/ImageMagick-6/policy.xml

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the book_quick_draft module
COPY src/book_quick_draft /app/src/book_quick_draft

# Create necessary directories
RUN mkdir -p /app/output/chapters

# Set environment variables
ENV PYTHONPATH=/app

# Set working directory to book_quick_draft
WORKDIR /app/src/book_quick_draft

# Make build script executable
RUN chmod +x build_book.sh

# Default command
CMD ["./build_book.sh"]
```

### Web Dockerfile (Future Extension)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p output/outlines output/chapters output/research

# Set environment variables
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Set entrypoint
CMD ["uvicorn", "src.web.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Configuration Details

### Environment Variables

The application requires the following environment variables:

- `OPENAI_API_KEY`: API key for OpenAI services
- `BRIGHDATA_USERNAME`: Username for Brighdata services
- `BRIGHDATA_PASSWORD`: Password for Brighdata services

These will be provided via a `.env` file mounted into the container.

### Volume Configuration

- **Output Volume**: Maps to `./output:/app/output` to persist generated content
- **Environment Volume**: Maps to `./.env:/app/.env` for configuration
- **Source Volumes**: Maps source directories for development:
  - `./src/book_layout:/app/src/book_layout`
  - `./src/book_quick_draft:/app/src/book_quick_draft`

### Network Configuration

- All services will be on the same `app-network` for internal communication
- Only the web service (if implemented) will expose ports to the host

## Implementation Steps

### 1. Create Docker Compose File

Create a `docker-compose.yml` file in the project root with all services defined.

### 2. Create Dockerfiles

Create the following Dockerfiles in the project root:
- `Dockerfile` - For the main book_factory service
- `Dockerfile.book_layout` - For the book_layout service
- `Dockerfile.book_quick_draft` - For the book_quick_draft service

### 3. Create .dockerignore

Create a `.dockerignore` file to exclude unnecessary files:

```
.git
.gitignore
.env
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg
venv/
venv312/
bookenv/
```

### 4. Update .env File

Ensure the `.env` file contains all required environment variables:

```
OPENAI_API_KEY=your_openai_api_key
BRIGHDATA_USERNAME=your_brighdata_username
BRIGHDATA_PASSWORD=your_brighdata_password
```

### 5. Test the Setup

Build and run the Docker Compose setup:

```bash
docker compose build
docker compose up -d
```

## Usage Instructions

### Building the Docker Image

```bash
docker compose build
```

### Running the Application

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Stop all services
docker compose down
```

### Running CLI Commands

```bash
# Generate a book outline
docker compose run --rm book_factory python book_cli.py outline

# Generate a specific chapter
docker compose run --rm book_factory python book_cli.py write --chapter 1

# Run the full book generation flow
docker compose run --rm book_factory python book_cli.py flow
```

### Using Book Layout Service

```bash
# Generate a professionally formatted PDF
docker compose run --rm book_layout ./build.sh
```

### Using Book Quick Draft Service

```bash
# Generate a quick draft PDF
docker compose run --rm book_quick_draft ./build_book.sh
```

### Accessing Generated Content

All generated content will be available in the `./output` directory on the host machine.

## Troubleshooting Tips

### Common Issues

1. **Missing Environment Variables**
   - Ensure the `.env` file is properly mounted and contains all required variables
   - Check container logs for environment-related errors

2. **Permission Issues**
   - Ensure the output directory has proper permissions
   - Run `chmod -R 777 ./output` if necessary

3. **Network Connectivity**
   - If services can't communicate, check the network configuration
   - Ensure all services are on the same network

4. **API Rate Limiting**
   - OpenAI API may have rate limits
   - Implement retry logic or rate limiting in the application

5. **LaTeX/Pandoc Issues**
   - Check if all required LaTeX packages are installed
   - Verify pandoc version compatibility

### Debugging

1. **Check Container Logs**
   ```bash
   docker compose logs -f book_factory
   docker compose logs -f book_layout
   docker compose logs -f book_quick_draft
   ```

2. **Access Container Shell**
   ```bash
   docker compose exec book_factory bash
   docker compose exec book_layout bash
   docker compose exec book_quick_draft bash
   ```

3. **Verify Volume Mounts**
   ```bash
   docker compose exec book_factory ls -la /app/output
   docker compose exec book_layout ls -la /app/src/book_layout
   docker compose exec book_quick_draft ls -la /app/src/book_quick_draft
   ```

4. **Check Environment Variables**
   ```bash
   docker compose exec book_factory env
   ```

### Performance Optimization

1. **Resource Allocation**
   - Adjust container resource limits in docker-compose.yml if needed
   - Monitor resource usage with `docker stats`

2. **Build Optimization**
   - Use multi-stage builds for smaller images
   - Optimize the Dockerfile for better layer caching

3. **Volume Performance**
   - Consider using named volumes instead of bind mounts for better performance
   - Use volume drivers appropriate for your environment