import uvicorn

try:
    from .api.routes import app
    from .config import config
except ImportError:
    from api.routes import app
    from config import config

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=config.api_host,
        port=config.api_port,
        reload=config.debug,
        log_level="info"
    )