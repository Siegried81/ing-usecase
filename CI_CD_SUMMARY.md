# CI/CD & Registry Setup Summary

## What was created

### 1. GitHub Actions Workflow (`.github/workflows/docker.yml`)
- **Multi-stage Docker build** with BuildKit + layer caching
- **Automatic push to Docker Hub** on:
  - Push to `main` → tagged as `latest`, `main`
  - Push to `develop` → tagged as `develop`
  - Git tags (e.g., `v1.0.0`) → tagged as semantic versions
  - PRs → build-only, no push
- **Security scanning** with Trivy (HIGH/CRITICAL CVEs)
- **Caching** from GitHub Actions cache (faster builds)

### 2. Health Monitoring Dashboard
- **Service**: `services/health_dashboard.py` (FastAPI + Uvicorn)
- **Port**: 8080
- **Features**:
  - Real-time health checks every 10 seconds
  - Latency measurement (ms) per service
  - Color-coded status (green/yellow/red)
  - HTML dashboard with auto-refresh
  - JSON API: `GET /health`
  - WebSocket API: `ws://localhost:8080/ws/health`

### 3. Docker Compose Integration
- **Service**: `dashboard` added to `docker-compose.yml`
- **Dockerfile**: `services/Dockerfile` (lightweight Python 3.11-slim)
- **Health checks**: All 3 services have health checks
- **Dependencies**: Dashboard depends on streamlit + api

### 4. Documentation
- **DOCKER.md** — 7.5KB comprehensive guide with all workflows
- **GITHUB_ACTIONS_SETUP.md** — Step-by-step setup instructions

## Quick Start

### Step 1: Add GitHub Secrets (one-time)
1. Go to GitHub repo → Settings → Secrets and variables → Actions
2. Create `DOCKERHUB_USERNAME` = `siegried`
3. Create `DOCKERHUB_TOKEN` = (your Docker Hub PAT token)
4. Done! Next push automatically builds and pushes

### Step 2: Start everything locally
```bash
docker compose up --pull always
# Dashboard: http://localhost:8080
# Streamlit: http://localhost:8501
# API:       http://localhost:8000
```

### Step 3: Deploy a release
```bash
git tag v1.0.0
git push origin v1.0.0
# GitHub Actions automatically builds and pushes to Docker Hub
```

## File Structure

```
.github/workflows/
  docker.yml                    ← CI/CD workflow (auto-build on push)
services/
  health_dashboard.py           ← FastAPI health monitor
  Dockerfile                    ← Lightweight dashboard image
docker-compose.yml             ← Updated with dashboard service
docker-compose.dev.yml         ← Development overrides
docker-compose.prod.yml        ← Production hardening
DOCKER.md                       ← Complete Docker guide
GITHUB_ACTIONS_SETUP.md        ← Setup instructions
```

## Key Features

| Feature | Location | Description |
|---------|----------|-------------|
| **Auto-build** | `.github/workflows/docker.yml` | Push triggers → Docker Hub |
| **Health checks** | `docker-compose.yml` | All services monitored |
| **Dashboard** | Port 8080 | Visual health status |
| **JSON API** | `/health` | Programmatic health checks |
| **Security** | Trivy scan in workflow | HIGH/CRITICAL CVEs reported |
| **Caching** | GitHub Actions + Docker | Faster rebuilds |

## Example Scenarios

### Scenario 1: Regular development
```bash
# Edit code locally
docker compose -f docker-compose.yml -f docker-compose.dev.yml up

# Services auto-reload
# Dashboard shows real-time status at http://localhost:8080

# Commit and push
git push origin main
# GitHub Actions automatically builds and pushes new image
```

### Scenario 2: Production deployment
```bash
# Create a release tag
git tag v2.0.0
git push origin v2.0.0

# Wait for GitHub Actions to finish (~2-3 min)
# Pull and deploy
docker pull siegried/ing-comparator:v2.0.0
docker compose up -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Scenario 3: Monitor all services
```bash
# All three services running
docker compose up

# View health dashboard
curl http://localhost:8080/health | jq

# Or visit http://localhost:8080 in browser
```

## Monitoring & Troubleshooting

### Check build status
- GitHub Actions tab → Click the workflow
- See build logs and security scan results

### Health dashboard down
```bash
docker compose ps
docker compose logs dashboard
```

### Image won't pull from Docker Hub
```bash
# Ensure workflow pushed successfully
# Check on https://hub.docker.com/r/siegried/ing-comparator

# If stuck, rebuild locally and push
docker login
docker build -t siegried/ing-comparator:latest .
docker push siegried/ing-comparator:latest
```

## What's Next

1. ✅ Add GitHub Secrets (DOCKERHUB_USERNAME, DOCKERHUB_TOKEN)
2. ✅ Test: `git push` → watch GitHub Actions build
3. ✅ Verify image appears on Docker Hub
4. ✅ Create a release: `git tag v1.0.0 && git push origin v1.0.0`
5. ✅ Use the health dashboard to monitor deployments

## Security Notes

- No credentials baked into images
- All secrets passed at runtime via `.env` or environment variables
- Non-root user (UID 1000) in all containers
- Production compose includes read-only root filesystem + capability drop
- Trivy scans all pushed images for known CVEs

