import uvicorn
from src.database import init_db
from src.config import config

# Import app (already wrapped with _LargeBodyMiddleware in routes.py)
from src.api.routes import app

# Initialize database on startup (app is the wrapper; the inner FastAPI app
# has its own startup events registered via @app.on_event in routes.py)
# We need to register on the inner FastAPI app, not the wrapper.
# The inner app is app.inner (the FastAPI instance).
if hasattr(app, 'inner'):
    _fastapi_app = app.inner
else:
    _fastapi_app = app

@_fastapi_app.on_event("startup")
async def startup_event():
    init_db()

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=config.api_host,
        port=config.api_port,
        reload=config.debug,
        log_level="info",
        timeout_keep_alive=300
    )