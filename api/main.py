from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.faq import router as faq_router
from api.routes.creators import router as creator_router

app = FastAPI(title="Creo API", version="2.0.0", description="Creator Success Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(faq_router, prefix="/api/v1/faq", tags=["FAQ"])
app.include_router(creator_router, prefix="/api/v1/creators", tags=["Creators"])


@app.get("/api/v1/health")
def health():
    return {"status": "ok", "version": "2.0.0"}
