import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from . import log_groups, log_streams, logs, join

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for querying and joining AWS CloudWatch logs from multiple services",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(log_groups.router, prefix="/api", tags=["log-groups"])
app.include_router(log_streams.router, prefix="/api", tags=["log-streams"])
app.include_router(logs.router, prefix="/api", tags=["logs"])
app.include_router(join.router, prefix="/api", tags=["join"])

@app.get("/", tags=["root"])
async def root():
    """API health check endpoint"""
    return {
        "status": "ok",
        "message": "CloudWatch Logs Query API is running"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)