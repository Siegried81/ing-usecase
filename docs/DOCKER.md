# Docker

## Services and ports

| Service | Host port | Container port | Purpose |
|---|---|---|---|
| `streamlit` | 8506 | 8501 | Key-free dashboard, reads the data baked into the image |
| `api` | 8006 | 8000 | FastAPI + React UI + generated site; needs LLM keys in `.env` |
| `dashboard` | 8606 | 8080 | Health monitor, profile `monitoring` (opt-in) |

## Run

```bash
cp .env.example .env                    # optional for the dashboard, needed for the API
docker compose up --build               # streamlit + api
docker compose --profile monitoring up  # adds the health dashboard
docker compose pull                     # use the published image instead of building
```

The default compose file runs the image as built: no source is mounted, so what
you see is what was baked in. `api_outputs` is a named volume that keeps generated
recommendations and site across restarts (`docker compose down -v` resets it).

## Variants

| File | Use |
|---|---|
| `docker/docker-compose.dev.yml` | live `src/`, `scripts/`, `config/`, `streamlit_app.py`, debug logs |
| `docker-compose.debug.yml` | debugpy attach from VS Code (ports 5678/5679, localhost only) |
| `docker/docker-compose.prod.yml` | read-only root, dropped capabilities, resource limits |

```bash
docker compose -f docker-compose.yml -f docker/docker-compose.dev.yml up --build
docker compose -f docker-compose.yml -f docker/docker-compose.prod.yml up -d
```

## One-off tasks

```bash
docker compose run --rm streamlit python3 scripts/run_analysis.py \
  --dataset data/processed/campaigns_scored.csv --product-family auto --no-strict
docker compose run --rm streamlit python3 -m pytest tests/ -q
```

Collection needs keys, Chromium (in the image) and a volume for `data/`; see the
run examples at the bottom of the `Dockerfile`.

## Images and CI

`.github/workflows/publish.yml` builds both images, smoke-tests them, then pushes
to GHCR (`ghcr.io/siegried81/<image>`, built-in `GITHUB_TOKEN`) and, when the
secrets exist, to Docker Hub. Pushes to `main` publish `latest`; tags `vX.Y.Z`
publish `X.Y.Z` and `X`.

Repository secrets (Settings, Secrets and variables, Actions):

- `DOCKERHUB_USERNAME`: Docker Hub user.
- `DOCKERHUB_TOKEN`: access token with read/write scope (hub.docker.com/settings/security).
- `GITHUB_TOKEN`: provided automatically, nothing to add.

Without the two Docker Hub secrets, only GHCR is published. A failing build is
usually an expired `DOCKERHUB_TOKEN`.

## Troubleshooting

- Port in use: `docker compose down`, then `docker ps` for orphans.
- `.env` change not seen: `docker compose restart api` (read at container start).
- Dashboard shows "Unreachable": `docker compose ps` and `docker compose logs api`.
- Never commit `.env`; keys are passed at run time, none is baked in.
