"""
Bruno AI Server - Main FastAPI application
"""

import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, Depends, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from sqlalchemy.ext.asyncio import AsyncSession
from bruno_ai_server.middleware.auth_middleware import AuthenticationMiddleware
from bruno_ai_server.middleware.security_middleware import SecurityHeadersMiddleware

from bruno_ai_server.config import settings
from bruno_ai_server.database import get_async_session
from bruno_ai_server.routes import auth_router, pantry_router, voice_router, categories_router
from bruno_ai_server.routes.auth import compat_router
from bruno_ai_server.routes.expiration import router as expiration_router
from bruno_ai_server.schemas import RefreshTokenRequest, UserCreate, UserLogin
from bruno_ai_server.services.scheduler_service import scheduler_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown."""
    # Startup
    scheduler_service.start()
    print("Background scheduler started")
    
    # Export OpenAPI spec to file on startup for build process
    try:
        openapi_spec = app.openapi()
        
        # Create build directory if it doesn't exist
        build_dir = Path("build")
        build_dir.mkdir(exist_ok=True)
        
        # Write OpenAPI spec to file
        openapi_file = build_dir / "openapi.json"
        with open(openapi_file, "w") as f:
            json.dump(openapi_spec, f, indent=2)
            
        print(f"OpenAPI spec exported to {openapi_file}")
    except Exception as e:
        print(f"Failed to export OpenAPI spec: {e}")
    
    yield
    
    # Shutdown
    scheduler_service.stop()
    print("Background scheduler stopped")


# Create FastAPI app instance
app = FastAPI(
    title="Bruno AI Server",
    description="FastAPI backend for Bruno AI - household food management",
    version="0.1.0",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    lifespan=lifespan,
)

# Define allowed origins based on environment
def get_allowed_origins():
    """Get CORS allowed origins based on environment."""
    if settings.is_production:
        # In production, restrict to mobile bundle IDs and known domains
        return [
            "https://brunoai.app",
            "https://api.brunoai.app",
            "brunoai://",  # iOS app scheme
            "com.brunoai.client://",  # Android app scheme  
        ]
    else:
        # In development, allow localhost and common dev ports
        return [
            "http://localhost:3000",
            "http://localhost:8080", 
            "http://localhost:5000",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8080",
            "http://127.0.0.1:5000",
        ]

# Add CORS middleware with proper origin restrictions
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "User-Agent",
        "X-Requested-With",
        "X-CSRF-Token",
    ],
    expose_headers=["X-Total-Count", "X-Page-Count"],
)

# Add security headers middleware
app.add_middleware(
    SecurityHeadersMiddleware
)

# Add authentication middleware
app.add_middleware(
    AuthenticationMiddleware
)

# Include routers with /api prefix for API Gateway routing
app.include_router(auth_router, prefix="/api")
app.include_router(pantry_router, prefix="/api")
app.include_router(categories_router, prefix="/api")
app.include_router(voice_router, prefix="/api")
app.include_router(expiration_router, prefix="/api")

# Include backwards compatibility router for legacy /auth endpoints
app.include_router(compat_router, prefix="/api")

# Direct auth routes (without /api prefix) for client compatibility
direct_auth_router = APIRouter(prefix="", tags=["direct-auth"], include_in_schema=False)

@direct_auth_router.post("/auth/register")
async def direct_register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_async_session),
):
    """Direct auth endpoint - same as /api/users/register."""
    from bruno_ai_server.routes.auth import register_user
    return await register_user(user_data, db)

@direct_auth_router.post("/auth/login")
async def direct_login_user(
    user_data: UserLogin,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_async_session),
):
    """Direct auth endpoint - same as /api/users/login."""
    from bruno_ai_server.routes.auth import login_user
    return await login_user(user_data, request, response, db)

@direct_auth_router.post("/auth/refresh")
async def direct_refresh_access_token(
    token_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_async_session),
):
    """Direct auth endpoint - same as /api/users/refresh."""
    from bruno_ai_server.routes.auth import refresh_access_token
    return await refresh_access_token(token_data, db)

@direct_auth_router.get("/auth/csrf-token")
async def direct_get_csrf_token(request: Request):
    """Direct auth endpoint - same as /api/users/csrf-token."""
    from bruno_ai_server.routes.auth import get_csrf_token
    return await get_csrf_token(request)

app.include_router(direct_auth_router)


@app.get("/")
async def root():
    """Root health check endpoint that returns 'pong'"""
    return {"message": "pong"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "bruno-ai-server"}


def custom_openapi():
    """Generate custom OpenAPI schema."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add JWT security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token for authentication"
        }
    }
    
    # Add audience verification info
    openapi_schema["info"]["x-audience"] = "bruno-ai-mobile-app"
    openapi_schema["info"]["x-jwt-issuer"] = "bruno-ai-server"
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.get("/openapi.json", include_in_schema=False)
async def get_openapi_json():
    """Export OpenAPI spec as JSON."""
    return app.openapi()




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
