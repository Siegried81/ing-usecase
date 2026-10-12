# Banking Campaigns Comparator

## Quick reference

- **Source code, Dockerfile, issues:** https://github.com/Siegried81/ing-usecase
- **Maintained by:** Siegried81
- **Also on:** GitHub Container Registry, `ghcr.io/siegried81/<image>`
- **Architecture:** `linux/amd64`

## Supported tags

- `latest`: the current `main` branch
- `X.Y.Z` and `X`: released versions (git tags `vX.Y.Z`), the ones to pin for a stable deployment
- `sha-xxxxxxx`: one specific commit

## What is it?

How Belgian banks communicate comparable products differently: a Streamlit comparator, a web UI served by a small API, and a health dashboard.

Images from this repository:

- `ing-comparator`: Streamlit UI on 8501; same image serves the web UI/API on 8000
- `ing-comparator-dashboard`: service health dashboard on 8080

## How to use this image

```bash
docker run -d -p 8501:8501 siegried/ing-comparator
# open http://localhost:8501

# web UI + API
docker run -d -p 8000:8000 --env-file .env siegried/ing-comparator \
  python3 scripts/serve_web.py --host 0.0.0.0 --port 8000
```

## Environment variables

None are required to start the UI. Secrets are **never** baked into the image: pass
them at run time with `-e NAME=value` or `--env-file .env` (see `.env.example` in the repo).

| Variable | Purpose |
|---|---|
| `GROQ_API_KEY / DEEPSEEK_API_KEY / OPENROUTER_API_KEY` | LLM providers (optional for the UI) |
| `NEWSAPI_KEY` | news collection |

## Volumes

- `/app/data`: collected dataset
- `/app/outputs`: generated reports

## License

See the LICENSE file in the source repository, if any. As with every image, it is
your responsibility to check that your use complies with the licenses of the
software it contains.
