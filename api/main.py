from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import time
import uuid
from collections import defaultdict

from api.routes.faq import router as faq_router
from api.routes.creators import router as creator_router
from api.routes.campaigns import router as campaign_router
from api.routes.discovery import router as discovery_router

app = FastAPI(title="BigBell API", version="2.0.0", description="Creator Success Platform API")

# Observability: request counts + total latency per route (excl. /metrics)
_request_counts: dict[str, int] = defaultdict(int)
_request_latency_total: dict[str, float] = defaultdict(float)

# CORS: pin to specific origins in production; allow all in dev
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:8501,http://127.0.0.1:8501").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Simple in-memory rate limiter (per IP)
_rate_limits: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds


async def observability_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    route = request.url.path
    if route != "/metrics":
        _request_counts[route] += 1
        _request_latency_total[route] += elapsed_ms
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time-ms"] = f"{elapsed_ms:.2f}"
    return response


async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    # Clean old entries
    _rate_limits[client_ip] = [t for t in _rate_limits[client_ip] if now - t < RATE_LIMIT_WINDOW]
    if len(_rate_limits[client_ip]) >= RATE_LIMIT_REQUESTS:
        return JSONResponse(
            status_code=429,
            content={"detail": f"Rate limit exceeded: {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW}s"},
        )
    _rate_limits[client_ip].append(now)
    response = await call_next(request)
    return response

app.middleware("http")(observability_middleware)
app.middleware("http")(rate_limit_middleware)

app.include_router(faq_router, prefix="/api/v1/faq", tags=["FAQ"])
app.include_router(creator_router, prefix="/api/v1/creators", tags=["Creators"])
app.include_router(campaign_router, prefix="/api/v1/campaigns", tags=["Campaigns"])
app.include_router(discovery_router, prefix="/api/v1/discovery", tags=["Discovery"])


@app.get("/api/v1/health")
def health():
    return {"status": "ok", "version": "2.0.0"}


@app.get("/metrics")
def metrics():
    return {
        route: {
            "count": _request_counts[route],
            "avg_latency_ms": round(_request_latency_total[route] / _request_counts[route], 2),
        }
        for route in _request_counts
    }
