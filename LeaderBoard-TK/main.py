import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from db.database import engine, SessionLocal, Base
from models.user import User  # noqa: F401  — registers the model with Base
from controllers.leaderboard_controller import router
from services import leaderboard_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SYNC_INTERVAL_SECONDS = 5 * 60 + 30  # 5 minutes and 30 seconds


async def periodic_sync():
    """Background task: sync external API -> SQLite on an interval."""
    while True:
        db = SessionLocal()
        try:
            count = await leaderboard_service.fetch_and_sync(db)
            logger.info(f"Auto-sync completed: {count} records processed")
        except Exception as e:
            logger.error(f"Sync failed: {e}")
        finally:
            db.close()
        await asyncio.sleep(SYNC_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables + launch background sync
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
    task = asyncio.create_task(periodic_sync())
    logger.info("External API auto-sync enabled")
    yield
    # Shutdown: cancel background task
    if task is not None:
        task.cancel()


app = FastAPI(title="Leaderboard API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)

@app.middleware("http")
async def no_cache_for_html(request, call_next):
    response = await call_next(request)
    if request.url.path == "/" or request.url.path.endswith(".html"):
        response.headers["Cache-Control"] = "no-cache, must-revalidate"
    return response

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def root():
    return FileResponse(STATIC_DIR / "index.html")
