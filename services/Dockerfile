# Health Dashboard — lightweight FastAPI service monitoring other services
FROM python:3.11-slim

WORKDIR /app

# Pinned like every other dependency in this repo: requirements.txt says
# they are "pinned so the pipeline is reproducible by a third party
# (NFR-01)", and an unpinned service would not rebuild identically in six
# months. fastapi and uvicorn match requirements.txt exactly - two files
# disagreeing on a version is its own bug.
RUN pip install --no-cache-dir \
        fastapi==0.141.1 \
        uvicorn==0.53.0 \
        aiohttp==3.14.3

COPY services/health_dashboard.py .

USER 1000

EXPOSE 8080

HEALTHCHECK --interval=15s --timeout=5s --retries=2 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health').read()"

CMD ["python3", "health_dashboard.py"]
