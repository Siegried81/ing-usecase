# Architecture Overview

## System Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                     Your Local Machine / Server                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │         Docker Compose Network (ing-usecase)            │    │
│  │                                                          │    │
│  │  ┌──────────────────┐  ┌──────────────────┐             │    │
│  │  │  Streamlit UI    │  │   FastAPI API    │             │    │
│  │  │  Port 8501       │  │   Port 8000      │             │    │
│  │  │  (Dashboard)     │  │  (Backend)       │             │    │
│  │  │                  │  │                  │             │    │
│  │  │ - Home page      │  │ - Recommendations│             │    │
│  │  │ - Analysis       │  │ - Web gen        │             │    │
│  │  │ - Profiles       │  │ - API docs       │             │    │
│  │  │ - Data view      │  │ - Site backend   │             │    │
│  │  └──────────────────┘  └──────────────────┘             │    │
│  │           ▲                      ▲                       │    │
│  │           │ reads                │ depends on            │    │
│  │           └──────────────────────┘                       │    │
│  │                   ▲                                       │    │
│  │                   │ monitors health                       │    │
│  │           ┌───────┴────────┐                             │    │
│  │           │  Health Dashboard      │                     │    │
│  │           │  Port 8080             │                     │    │
│  │           │  (Monitoring)          │                     │    │
│  │           │                        │                     │    │
│  │           │  - Service status      │                     │    │
│  │           │  - Latency checks      │                     │    │
│  │           │  - JSON API            │                     │    │
│  │           │  - HTML dashboard      │                     │    │
│  │           │  - WebSocket updates   │                     │    │
│  │           └────────────────────────┘                     │    │
│  │                   ▲                                       │    │
│  │                   │ pings every 10s                       │    │
│  │                                                          │    │
│  │  ┌─────────────────────────────────────────────────┐   │    │
│  │  │  Persistent Volumes                             │   │    │
│  │  │                                                  │   │    │
│  │  │  - streamlit_data   (data/)                     │   │    │
│  │  │  - streamlit_outputs (outputs/)                 │   │    │
│  │  │  - api_data         (data/, read-only)          │   │    │
│  │  │  - api_outputs      (outputs/)                  │   │    │
│  │  │  - streamlit_cache  (.streamlit/)               │   │    │
│  │  └─────────────────────────────────────────────────┘   │    │
│  │                                                          │    │
│  └──────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                              ▼                                   │
│                         .env file                                │
│              (LLM keys, API credentials)                         │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │        External Services (via .env)                    │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │  - DeepSeek LLM        (extraction)                   │    │
│  │  - Groq LLM            (fallback extraction)          │    │
│  │  - NewsAPI             (reputation headlines)         │    │
│  │  - Semantic Scholar    (academic search)             │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
         │
         │
         ▼
    ┌────────────────────────────────────────┐
    │      GitHub Repository                 │
    ├────────────────────────────────────────┤
    │                                        │
    │  .github/workflows/docker.yml          │
    │  (CI/CD Pipeline)                      │
    │                                        │
    │  On push/tag:                          │
    │  1. Checkout code                      │
    │  2. Build Docker image (multi-stage)   │
    │  3. Run tests in container             │
    │  4. Security scan (Trivy)              │
    │  5. Push to Docker Hub                 │
    │                                        │
    └────────────────────────────────────────┘
         │
         ▼
    ┌────────────────────────────────────────┐
    │      Docker Hub Registry               │
    ├────────────────────────────────────────┤
    │ siegried/ing-comparator                │
    │                                        │
    │ Tags:                                  │
    │ - latest   (main branch)               │
    │ - main     (main branch)               │
    │ - develop  (develop branch)            │
    │ - v1.0.0   (release tags)              │
    │ - 1.0      (semantic versions)         │
    │ - 1        (major version)             │
    │ - branch-{sha} (commit hash)           │
    │                                        │
    └────────────────────────────────────────┘
         │
         ▼
    Can be pulled anywhere:
    docker pull siegried/ing-comparator:v1.0.0
```

## Workflow: Development → Production

```
┌─────────────────┐
│  Local Dev      │
│  Edit code      │
│  docker compose │
│  up --dev       │
│  (hot reload)   │
└────────┬────────┘
         │
         │ git push
         ▼
┌──────────────────────┐
│  GitHub Repository   │
│                      │
│  Trigger Workflow:   │
│  docker.yml          │
└────────┬─────────────┘
         │
         │ Build & Test
         ▼
┌──────────────────────┐
│  GitHub Actions      │
│                      │
│  1. Build image      │
│  2. Run pytest       │
│  3. Security scan    │
│  4. Push to Hub      │
└────────┬─────────────┘
         │
         │ Success
         ▼
┌──────────────────────┐
│  Docker Hub          │
│                      │
│  Image available:    │
│  siegried/ing-...    │
│  {branch/version}    │
└────────┬─────────────┘
         │
         │ docker pull
         ▼
┌──────────────────────┐
│  Production Server   │
│                      │
│  docker compose      │
│  -f prod.yml up      │
│                      │
│  Hardened + monitored│
└──────────────────────┘
```

## Service Dependencies

```
dashboard (port 8080)
    ├─ depends_on: streamlit
    │               │
    │               ├─ reads: data/, outputs/
    │               └─ health: /_stcore/health
    │
    └─ depends_on: api
                    │
                    ├─ reads: .env
                    ├─ reads: data/ (ro)
                    ├─ reads: web/dist
                    └─ health: /health

All services:
- Non-root user (UID 1000)
- Health checks enabled
- Restart policy: unless-stopped
- Network: shared (default bridge)
```

## Build Pipeline Stages (Multi-stage Dockerfile)

```
Stage 1: node:20-slim
  │
  ├─ COPY web/package*.json
  ├─ RUN npm ci                   ← Cache layer
  ├─ COPY web/
  └─ RUN npm run build            ← Produces dist/


Stage 2: python:3.11-slim
  │
  ├─ COPY requirements*.txt
  ├─ RUN pip install              ← Cache layer
  ├─ RUN playwright install       ← Chromium binary (~200MB)
  │       --with-deps chromium
  ├─ COPY . .
  ├─ COPY --from=web dist/        ← From stage 1
  ├─ RUN useradd app              ← Non-root user
  │       chown -R app:app
  ├─ USER app
  └─ CMD streamlit run ...        ← Default (Streamlit)
     or python3 serve_web.py      ← Can override to FastAPI


Stage 3 (Dashboard): python:3.11-slim
  │
  ├─ COPY services/health_dashboard.py
  ├─ RUN pip install fastapi aiohttp
  ├─ USER 1000                    ← Non-root
  └─ CMD python3 health_dashboard.py
```

## Health Check Mechanism

```
Health Dashboard (port 8080)
    │
    ├─ Every 10 seconds:
    │
    ├─ GET http://streamlit:8501/_stcore/health
    │  │
    │  ├─ Status: ✅ (if 200ms response)
    │  ├─ Latency: X ms
    │  └─ Color: Green
    │
    ├─ GET http://api:8000/health
    │  │
    │  ├─ Status: ✅ (if 200ms response)
    │  ├─ Latency: X ms
    │  └─ Color: Green
    │
    └─ Render HTML dashboard + JSON API


Browser or API client:
    │
    ├─ GET http://localhost:8080/          → HTML dashboard
    ├─ GET http://localhost:8080/health    → JSON API
    └─ WS  ws://localhost:8080/ws/health   → WebSocket stream
```

## Data Flow: Analysis Pipeline

```
User Input (Streamlit UI)
    │
    ├─ Browse data at http://localhost:8501
    ├─ View analysis results
    ├─ Download outputs
    └─ Triggers optional pipeline runs


Behind the scenes:
    │
    ├─ Reads: data/processed/campaigns_scored.csv
    │
    ├─ Transformations:
    │  ├─ schema.coerce_types()
    │  ├─ analysis.feature_accounting()
    │  ├─ analysis.positioning()
    │  └─ ai_score.compute()
    │
    ├─ Generates: outputs/*.png, *.csv, *.json
    │
    └─ Persisted in: streamlit_outputs volume


FastAPI Backend (if used):
    │
    ├─ Endpoint: POST /recommendations
    ├─ Reads: outputs/report.json
    ├─ Uses: LLM keys from .env
    ├─ Returns: Generated recommendations
    └─ Serves: React UI + demo site
```

## Deployment Topology

### Development
```
Local machine
  └─ docker compose up --dev
      ├─ Hot reload volumes bound
      ├─ Debug logging enabled
      └─ All ports exposed
```

### Production
```
Remote server
  └─ docker compose -f prod.yml up -d
      ├─ Read-only root filesystem
      ├─ Cap drop (no dangerous capabilities)
      ├─ Resource limits (CPU/Memory)
      ├─ Restart policy: unless-stopped
      └─ Health checks: continuous
```

---

**Update frequency:** Last updated when CI/CD was added (2026-09-28)
