# Docker Quick Start

## Setup: GitHub Secrets & Docker Hub

Before running the CI/CD pipeline, add these secrets to your GitHub repository (Settings → Secrets and variables → Actions):

1. **`DOCKERHUB_USERNAME`** — Your Docker Hub username (e.g., `siegried`)
2. **`DOCKERHUB_TOKEN`** — Docker Hub personal access token
   - Go to https://hub.docker.com/settings/security
   - Create a new token with read/write permissions
   - Copy and paste it as the secret

## Build & Run

### Dashboard only (no API keys required)
```bash
docker compose up streamlit
# Visit http://localhost:8501
```

### Full stack with Health Dashboard
```bash
cp .env.example .env
# Fill in your LLM keys in .env (optional for dashboard)
docker compose up --pull always
# Health Dashboard: http://localhost:8080
# Streamlit:        http://localhost:8501
# API:              http://localhost:8000
```

### Development (hot reload enabled)
```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
# Changes in src/, config/, streamlit_app.py auto-reload
```

### Production (hardened, resource-limited)
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Common Tasks

### Run the analysis pipeline
```bash
docker compose run --rm streamlit \
  python3 scripts/run_analysis.py --dataset data/processed/campaigns_scored.csv \
  --product-family auto --no-strict
```

### Run collection (requires LLM key + .env)
```bash
docker compose run --rm api \
  python3 scripts/run_collection.py --config scripts/collection_targets.yaml \
  --method headless --out data/processed/campaigns.csv
```

### Run tests
```bash
docker compose run --rm streamlit python3 -m pytest tests/ -q
```

### View logs
```bash
docker compose logs streamlit -f
docker compose logs api -f
docker compose logs dashboard -f
```

### Rebuild image (after requirements.txt changes)
```bash
docker compose build --no-cache
docker compose up --pull always
```

### Clean up volumes
```bash
docker compose down -v
```

## Architecture

| Service | Port | Purpose |
|---------|------|---------|
| **streamlit** | 8501 | Dashboard — reads committed data/outputs, no API key needed |
| **api** | 8000 | FastAPI — recommendations, generated site, requires .env keys |
| **dashboard** | 8080 | Health Monitor — real-time health checks for all services |

## Health Dashboard

A dedicated monitoring service automatically included in `docker compose up`. Access it at **http://localhost:8080**.

**Features:**
- Real-time health checks every 10 seconds
- Latency measurement (ms) per service  
- Service status indicators with color coding (green/yellow/red)
- JSON API endpoint: `GET http://localhost:8080/health`
- WebSocket support for live updates: `ws://localhost:8080/ws/health`
- Auto-refresh HTML dashboard every 10 seconds

**Manual health check:**
```bash
curl http://localhost:8080/health | jq
```

**View in browser:**
Simply navigate to http://localhost:8080 after running `docker compose up`.

## CI/CD Pipeline

GitHub Actions automatically builds and pushes your image to Docker Hub.

**Workflow: `.github/workflows/docker.yml`**

### Triggers
- **Push to `main` or `develop`** → builds and pushes as `latest` and `branch-name`
- **Git tags** (e.g., `v1.0.0`) → builds and pushes as semantic version
- **Pull requests to `main`** → builds for testing only (no push)

### Example: Push a release
```bash
git tag v1.0.0
git push origin v1.0.0
# GitHub Actions automatically builds and pushes to:
# - docker.io/siegried/ing-comparator:v1.0.0
# - docker.io/siegried/ing-comparator:1.0
# - docker.io/siegried/ing-comparator:1
```

### View build status
Go to your GitHub repository → Actions tab to see build progress and logs.

### Security scanning
Trivy vulnerability scanner runs on all pushed images (non-blocking).

### Pull pre-built image
```bash
docker pull siegried/ing-comparator:latest
docker run -p 8501:8501 siegried/ing-comparator:latest
```

## Environment Variables

Copy `.env.example` to `.env` and fill in:
- `DEEPSEEK_API_KEY` / `GROQ_API_KEY` — LLM extraction
- `OPENROUTER_API_KEY`, `CEREBRAS_API_KEY` — LLM fallbacks
- `NEWSAPI_KEY` — bank reputation headlines
- `SEMANTIC_SCHOLAR_API_KEY` — academic search

**Never commit .env to version control.**

## Health Checks

All three services include health checks:
- **Streamlit**: `/_stcore/health` endpoint (30s interval)
- **API**: `/health` endpoint (30s interval)
- **Dashboard**: `/health` endpoint (15s interval)

Monitor with:
```bash
docker compose ps
```

## Volumes

- `streamlit_data` — shared data/ directory
- `streamlit_outputs` — generated outputs/
- `api_data` — data/ for API (read-only)
- `api_outputs` — API-generated files
- `streamlit_cache` — Streamlit cache directory

Clear all with: `docker compose down -v`

## Dockerfile Details

### Main application (Dockerfile)
1. **Stage 1 (web)**: Node 20-slim → React build → dist/ bundle
2. **Stage 2 (pipeline)**: Python 3.11-slim → install deps + Playwright → runs Streamlit + FastAPI
3. **Non-root user**: `app` (UID 1000) for security

### Health Dashboard (services/Dockerfile)
- Lightweight FastAPI service
- Python 3.11-slim base
- ~200MB total size

No secrets baked in. Chromium installed deterministically from Playwright version.

## Troubleshooting

### Port already in use
```bash
docker compose down
docker ps  # Check for orphaned containers
```

### Health Dashboard shows "Unreachable"
```bash
# Check if dependent services are running
docker compose ps

# View service logs
docker compose logs streamlit
docker compose logs api
```

### Out of memory during Playwright install
```bash
docker system prune -a  # Clean unused images
docker compose build --no-cache
```

### .env not loaded in API container
Ensure `.env` exists and `docker compose restart api` — env_file is read on container start.

### Slow first startup
Playwright downloads Chromium (~200MB) on first build. Subsequent rebuilds are cached.

### GitHub Actions build failure
Check the Actions tab for detailed logs. Common causes:
- `DOCKERHUB_TOKEN` not set or expired → regenerate in Docker Hub settings
- Out of space on GitHub runner → try `docker system prune` in action
- Rate limit hit on Docker Hub → wait a few minutes and retry

## Local Development Workflow

```bash
# 1. Clone and setup
git clone <repo>
cd ing-comparator
cp .env.example .env

# 2. Start with dev overrides (hot reload)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up

# 3. Edit files locally — they auto-reload in the container
# (src/, config/, streamlit_app.py, etc.)

# 4. View health dashboard
open http://localhost:8080

# 5. Run tests in container
docker compose exec streamlit python3 -m pytest tests/ -q

# 6. Commit and push — GitHub Actions takes it from here
git add .
git commit -m "feature: add X"
git push origin main
```

## Production Deployment

```bash
# 1. Use production overrides (security hardened)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 2. Monitor with health dashboard
curl http://localhost:8080/health

# 3. View logs
docker compose logs -f streamlit api dashboard

# 4. Scale only the API if needed
docker compose up -d --scale api=3
```

## References

- [docs/pipeline.md](docs/pipeline.md) — full runbook
- [README.md](README.md) — project overview
- [technical_deep_dive.md](technical_deep_dive.md) — architecture details
- [GitHub Actions workflow](.github/workflows/docker.yml) — CI/CD pipeline
