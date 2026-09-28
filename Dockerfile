# syntax=docker/dockerfile:1

# Banking Campaigns Comparator - the full pipeline in one image.
#
# It carries everything: collection (Playwright + Chromium), analysis,
# generation, the Streamlit operator dashboard and the FastAPI backend. That
# makes it big (~1.5 GB, most of it the browser). If you only need to look at
# results, the analysis stage alone needs neither Chromium nor a key.
#
# No secret is baked in. The LLM and news API keys are read from the
# environment at runtime - see the run examples at the bottom of this file.

# ---- stage 1: the React business UI -------------------------------------
# Built here so the image carries a ready bundle and no Node at runtime.
FROM node:20-slim AS web
WORKDIR /build
# package files first: this layer is cached until the lockfile itself changes.
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build


# ---- stage 2: the pipeline ----------------------------------------------
# 3.11 to match .github/workflows/tests.yml - the pinned dependency set is the
# one CI actually proves.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PLAYWRIGHT_BROWSERS_PATH=/opt/playwright

WORKDIR /app

# The three requirement files are split upstream on purpose: streamlit is
# UI-only and pytrends is unofficial and rate-limited, so neither is allowed to
# weigh on the pipeline's own pinned set. A full-pipeline image wants all
# three. Every version is pinned "so the pipeline is reproducible by a third
# party (NFR-01)".
COPY requirements.txt requirements-streamlit.txt requirements-geo.txt ./
RUN pip install --no-cache-dir \
        -r requirements.txt \
        -r requirements-streamlit.txt \
        -r requirements-geo.txt

# Chromium and the system libraries headless Chrome needs. This is the bulk of
# the image. The browser version comes from playwright==1.57.0 installed just
# above, so the client and the browser cannot drift apart - which is the whole
# reason this is not a separate apt-get install of chromium.
RUN playwright install --with-deps chromium \
    && rm -rf /var/lib/apt/lists/*

COPY . .
COPY --from=web /build/dist ./web/dist

# Collection writes snapshots and screenshots, and every analysis run rewrites
# outputs/. As root those land root-owned in any mounted volume, which is
# painful to clean up from the host.
RUN useradd --create-home --uid 1000 app \
    && chown -R app:app /app /opt/playwright
USER app

# 8501 the Streamlit dashboard, 8000 the FastAPI backend.
EXPOSE 8501 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python3 -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health').read()"

# Streamlit is the default because it is the one surface that is complete on
# its own: it reads the committed dataset and needs no second process and no
# API key. --server.address 0.0.0.0 is required - the default binds loopback,
# which is unreachable from outside the container.
CMD ["streamlit", "run", "streamlit_app.py", \
     "--server.address", "0.0.0.0", \
     "--server.port", "8501"]


# ---- how to run ---------------------------------------------------------
#
#   docker build -t ing-comparator .
#
# The dashboard, no key needed:
#   docker run --rm -p 8501:8501 ing-comparator
#
# The full business UI instead: the React bundle at /, the API under /api and
# the generated demo site at /site, all from one process on one port. It needs
# an LLM key, and it binds loopback by default, hence --host:
#   docker run --rm -p 8000:8000 --env-file .env ing-comparator \
#     python3 scripts/serve_web.py --host 0.0.0.0 --port 8000
#
# The bundle comes from the node stage above. serve_web.py mounts it only if
# web/dist exists, so the same file still runs in development where Vite serves
# the UI on :5173 instead.
#
# Re-run the analysis and keep the artefacts on the host:
#   docker run --rm -v "$PWD/outputs:/app/outputs" ing-comparator \
#     python3 scripts/run_analysis.py --dataset data/processed/campaigns_scored.csv \
#       --product-family auto --no-strict
#
# Collection. Writes into data/raw and data/processed, so mount them or the
# captures die with the container. assert_can_fetch() still checks robots.txt
# live before every fetch inside the container, exactly as it does on a laptop:
#   docker run --rm --env-file .env \
#     -v "$PWD/data:/app/data" ing-comparator \
#     python3 scripts/run_collection.py --config scripts/collection_targets.yaml \
#       --method headless --out data/processed/campaigns.csv
#
# --out is explicit on purpose: the script's own default is real_captures.csv,
# which is NOT the file the analysis reads. Omitting it collects successfully
# and changes nothing downstream, which is a confusing way to lose an hour.
#
# The test suite (no network - it passes with sockets disabled):
#   docker run --rm ing-comparator python3 -m pytest tests/ -q
