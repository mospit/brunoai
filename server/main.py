"""
Bruno AI Server - Main FastAPI application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from bruno_ai_server.routes import auth_router, pantry_router

# Create FastAPI app instance
app = FastAPI(
    title="Bruno AI Server",
    description="FastAPI backend for Bruno AI - household food management",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(pantry_router)


@app.get("/")
async def root():
    """Root health check endpoint that returns 'pong'"""
    return {"message": "pong"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "bruno-ai-server"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
