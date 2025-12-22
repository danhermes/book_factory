# Docker Setup for Book Factory

This document provides quick instructions for using the Docker setup for the Book Factory project.

## Prerequisites

- Docker and Docker Compose installed on your system
- OpenAI API key and other required credentials

## Quick Start

1. **Set up environment variables**

   Copy the example environment file and add your API keys:

   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

2. **Build and start the containers**

   ```bash
   docker compose build
   docker compose up -d
   ```

3. **Run CLI commands**

   ```bash
   # Generate a book outline
   docker compose run --rm book_factory python book_cli.py outline

   # Generate a specific chapter
   docker compose run --rm book_factory python book_cli.py write --chapter 1

   # Run the full book generation flow
   docker compose run --rm book_factory python book_cli.py flow
   ```

4. **Access generated content**

   All generated content will be available in the `./output` directory on your host machine.

## Stopping the Services

```bash
docker compose down
```

## Viewing Logs

```bash
docker compose logs -f
```

## Troubleshooting

If you encounter issues:

1. Check that your `.env` file contains all required API keys
2. Ensure the output directory has proper permissions
3. Check container logs for specific error messages

For more detailed information, refer to the full [Docker Migration Plan](DOCKER_MIGRATION_PLAN.md).