## Concise Docker Compose Setup

### 1. **Create Structure**
```bash
mkdir orchestrator && cd orchestrator
mkdir tools/{tool1,tool2,tool3}
```

### 2. **Write docker-compose.yml**
```yaml
services:
  orchestrator:
    build: .
    ports: ["8000:8000"]
    networks: [app-net]
    
  tool1:
    build: ./tools/tool1
    networks: [app-net]
    
  tool2:
    build: ./tools/tool2  
    networks: [app-net]

networks:
  app-net:
```

### 3. **Create Tool Dockerfiles**
```dockerfile
# tools/tool1/Dockerfile
FROM python:3.11-slim
COPY app.py .
CMD ["python", "app.py"]
```

### 4. **Create Orchestrator Dockerfile**
```dockerfile
# Dockerfile
FROM python:3.11-slim
COPY orchestrator.py .
CMD ["python", "orchestrator.py"]
```

### 5. **Run**
```bash
docker compose up -d        # Start everything
docker compose logs -f      # Watch logs
docker compose ps           # Check status