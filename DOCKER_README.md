# Docker Deployment Guide for Medical Record Inspector

## Quick Start

### Build the Docker Image

```bash
cd medical-record-inspector
docker build -t medical-record-inspector .
```

### Run with Docker

```bash
docker run -p 8000:8000 --env-file .env medical-record-inspector
```

### Run with Docker Compose

```bash
# Create .env file first
cp .env.example .env
# Edit .env with your API key

# Start with docker-compose
docker-compose up -d
```

## Environment Variables

The following environment variables can be configured:

| Variable | Default | Description |
|----------|---------|-------------|
| ANTHROPIC_API_KEY | - | Your Anthropic API key (required) |
| MODEL_NAME | claude-3-5-sonnet-20240620 | LLM model to use |
| LOG_LEVEL | INFO | Logging level |
| PORT | 8000 | Server port |
| HOST | 0.0.0.0 | Server host |
| CACHE_EXPIRY_HOURS | 24 | Cache expiry time |

## Volumes

The following volumes are recommended for data persistence:

- `/app/data/history` - Evaluation history
- `/app/logs` - Log files
- `/app/reports` - Exported reports

## API Access

Once running, the API is accessible at:

- Health Check: `http://localhost:8000/api/health`
- Quality Assessment: `http://localhost:8000/api/v1/assess`
- List Standards: `http://localhost:8000/api/v1/list-standards`
- API Documentation: `http://localhost:8000/docs`

## Stopping the Container

```bash
# With Docker Compose
docker-compose down

# With Docker
docker stop <container-name>
docker rm <container-name>
```

## Updating the Image

```bash
# Stop the container
docker-compose down

# Rebuild the image
docker-compose build

# Start again
docker-compose up -d
```

## Troubleshooting

### API Key Not Found

Make sure your `.env` file is correctly mounted and contains `ANTHROPIC_API_KEY`.

### Port Already in Use

Change the port mapping in `docker-compose.yml`:

```yaml
ports:
  - "8001:8000"  # Map host port 8001 to container port 8000
```

### Permission Issues

Ensure the container has write permissions to mounted volumes:

```bash
# Linux/Mac: Change ownership
sudo chown -R 1000:1000 ./data ./logs ./reports
```
