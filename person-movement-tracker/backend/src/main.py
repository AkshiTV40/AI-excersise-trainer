import uvicorn
from .database import init_db

try:
    from .api.routes import app
    from .config import config
except ImportError:
    from api.routes import app
    from config import config

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=config.api_host,
        port=config.api_port,
        reload=config.debug,
        log_level="info"
    )