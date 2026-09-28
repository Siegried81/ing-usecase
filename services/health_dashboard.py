"""Health check dashboard for docker compose services.

Monitors Streamlit, FastAPI, and database health with a simple web interface.
Accessible at http://localhost:8080
"""

import asyncio
import time
from datetime import datetime
from typing import TypedDict

import aiohttp
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse

app = FastAPI(title="Health Dashboard")


class ServiceStatus(TypedDict):
    name: str
    url: str
    status: str
    latency_ms: float
    last_check: str
    color: str


# Service definitions
SERVICES = {
    "streamlit": {
        "url": "http://streamlit:8501/_stcore/health",
        "name": "Streamlit Dashboard",
    },
    "api": {
        "url": "http://api:8000/health",
        "name": "FastAPI Backend",
    },
}

# Store latest status
service_statuses: dict[str, ServiceStatus] = {}


async def check_service_health(service_id: str, config: dict) -> ServiceStatus:
    """Check a single service health."""
    url = config["url"]
    name = config["name"]
    start = time.time()

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            async with session.get(url, raise_for_status=True) as resp:
                if resp.status == 200:
                    latency = (time.time() - start) * 1000
                    return {
                        "name": name,
                        "url": url,
                        "status": "✅ Healthy",
                        "latency_ms": round(latency, 1),
                        "last_check": datetime.now().strftime("%H:%M:%S"),
                        "color": "#10b981",
                    }
    except asyncio.TimeoutError:
        return {
            "name": name,
            "url": url,
            "status": "⏱️ Timeout",
            "latency_ms": 5000.0,
            "last_check": datetime.now().strftime("%H:%M:%S"),
            "color": "#f59e0b",
        }
    except Exception as e:
        return {
            "name": name,
            "url": url,
            "status": f"❌ Unreachable ({type(e).__name__})",
            "latency_ms": 0.0,
            "last_check": datetime.now().strftime("%H:%M:%S"),
            "color": "#ef4444",
        }


async def health_check_loop():
    """Continuous health check loop."""
    while True:
        try:
            tasks = [
                check_service_health(sid, config)
                for sid, config in SERVICES.items()
            ]
            results = await asyncio.gather(*tasks)
            for sid, status in zip(SERVICES.keys(), results):
                service_statuses[sid] = status
        except Exception as e:
            print(f"Health check error: {e}")
        await asyncio.sleep(10)  # Check every 10 seconds


@app.on_event("startup")
async def startup():
    """Start the health check background task."""
    asyncio.create_task(health_check_loop())


@app.get("/health")
async def health():
    """Service health endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": service_statuses,
    }


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Render the health dashboard HTML."""
    statuses_html = ""
    overall_healthy = True

    for sid, status in service_statuses.items():
        color = status["color"]
        status_str = status["status"]
        latency = status["latency_ms"]

        if "Unreachable" in status_str or "Timeout" in status_str:
            overall_healthy = False

        statuses_html += f"""
        <div class="service-card" style="border-left: 4px solid {color}">
            <div class="service-header">
                <h3>{status['name']}</h3>
                <span class="status-badge" style="background-color: {color}">{status_str}</span>
            </div>
            <div class="service-details">
                <p><strong>Endpoint:</strong> {status['url']}</p>
                <p><strong>Latency:</strong> <span class="latency">{latency} ms</span></p>
                <p><strong>Last Check:</strong> {status['last_check']}</p>
            </div>
        </div>
        """

    overall_status = "All Systems Healthy" if overall_healthy else "Issues Detected"
    overall_color = "#10b981" if overall_healthy else "#ef4444"

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Banking Comparator — Health Dashboard</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
                color: #e2e8f0;
                min-height: 100vh;
                padding: 20px;
            }}
            .container {{
                max-width: 900px;
                margin: 0 auto;
            }}
            .header {{
                text-align: center;
                margin-bottom: 40px;
            }}
            .header h1 {{
                font-size: 2.5em;
                margin-bottom: 10px;
                background: linear-gradient(135deg, #60a5fa, #a78bfa);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }}
            .header p {{
                color: #94a3b8;
                font-size: 0.95em;
            }}
            .overall-status {{
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 30px;
                text-align: center;
                backdrop-filter: blur(10px);
            }}
            .overall-status .indicator {{
                display: inline-block;
                width: 16px;
                height: 16px;
                border-radius: 50%;
                background-color: {overall_color};
                margin-right: 10px;
                animation: pulse 2s ease-in-out infinite;
            }}
            @keyframes pulse {{
                0%, 100% {{ opacity: 1; }}
                50% {{ opacity: 0.6; }}
            }}
            .overall-status p {{
                font-size: 1.2em;
                font-weight: 500;
            }}
            .services {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}
            .service-card {{
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 20px;
                backdrop-filter: blur(10px);
                transition: all 0.3s ease;
            }}
            .service-card:hover {{
                background: rgba(255, 255, 255, 0.08);
                border-color: rgba(255, 255, 255, 0.2);
            }}
            .service-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
                padding-bottom: 10px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }}
            .service-header h3 {{
                font-size: 1.1em;
                font-weight: 600;
            }}
            .status-badge {{
                padding: 6px 12px;
                border-radius: 20px;
                font-size: 0.85em;
                font-weight: 600;
                color: white;
                text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
            }}
            .service-details {{
                font-size: 0.9em;
            }}
            .service-details p {{
                margin: 8px 0;
                color: #cbd5e1;
            }}
            .service-details strong {{
                color: #e2e8f0;
            }}
            .latency {{
                font-weight: 600;
                color: #60a5fa;
            }}
            .refresh-info {{
                text-align: center;
                color: #64748b;
                font-size: 0.9em;
                margin-top: 20px;
            }}
            .api-link {{
                text-align: center;
                margin-top: 20px;
            }}
            .api-link a {{
                color: #60a5fa;
                text-decoration: none;
                font-size: 0.9em;
            }}
            .api-link a:hover {{
                text-decoration: underline;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏦 Banking Comparator</h1>
                <p>Service Health Dashboard</p>
            </div>

            <div class="overall-status">
                <p><span class="indicator"></span>{overall_status}</p>
            </div>

            <div class="services">
                {statuses_html}
            </div>

            <div class="refresh-info">
                🔄 Checks run automatically every 10 seconds
            </div>

            <div class="api-link">
                <a href="/health">View JSON Health API</a>
            </div>
        </div>

        <script>
            // Auto-refresh the page every 10 seconds
            setInterval(() => {{
                location.reload();
            }}, 10000);
        </script>
    </body>
    </html>
    """


@app.websocket("/ws/health")
async def websocket_health(websocket: WebSocket):
    """WebSocket endpoint for real-time health updates."""
    await websocket.accept()
    try:
        while True:
            await websocket.send_json({
                "timestamp": datetime.now().isoformat(),
                "services": service_statuses,
            })
            await asyncio.sleep(5)
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
