# Banking Campaigns Comparator

## Quick reference

- **Source, Dockerfile, issues:** https://github.com/Siegried81/ing-usecase
- **Also on:** `ghcr.io/siegried81/<image>`
- **Architecture:** `linux/amd64`

## Tags

- `latest`: current `main`
- `X.Y.Z` and `X`: releases (git tags `vX.Y.Z`); pin these for a stable deployment
- `sha-xxxxxxx`: one commit

## Images

- `ing-comparator`: Streamlit dashboard (container port 8501); the same image serves the web UI and API on 8000
- `ing-comparator-dashboard`: health dashboard (container port 8080)

## Use

```bash
docker run -d -p 8506:8501 siegried/ing-comparator
# open http://localhost:8506

# web UI + API on http://localhost:8006
docker run -d -p 8006:8000 --env-file .env siegried/ing-comparator \
  python3 scripts/serve_web.py --host 0.0.0.0 --port 8000
```

The repository's `docker-compose.yml` publishes the same ports (8506, 8006) and
the health dashboard on 8606 under `--profile monitoring`.

## Environment

None is required to start the dashboard. Keys are passed at run time
(`-e NAME=value` or `--env-file .env`, see `.env.example`), never baked in.

| Variable | Purpose |
|---|---|
| `DEEPSEEK_API_KEY`, `GROQ_API_KEY`, `OPENROUTER_API_KEY` | LLM providers |
| `NEWSAPI_KEY`, `NEWSAPI_AI_KEY` | news headlines |

## Volumes

`/app/data` (dataset) and `/app/outputs` (generated reports). Check that your use
complies with the licenses of the software the image contains.
