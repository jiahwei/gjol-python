from contextlib import asynccontextmanager
from fastapi import FastAPI

from src.task.daily import scheduler,apscheduler_start,dayily_fun
from src.bulletin.router import router as bulletin_router
from src.database import create_db_and_tables
from src.spiders.test import test_resolve_notice

ml_models = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model
    ml_models["create_db_and_tables"] = create_db_and_tables
    ml_models["apscheduler_start"] = apscheduler_start
    # await apscheduler_start()
    test_resolve_notice()
    yield
    # Clean up the ML models and release resources
    # scheduler.shutdown()
    ml_models.clear()


app = FastAPI(lifespan=lifespan)

app.include_router(bulletin_router, prefix="/bulletins", tags=["公告"])


@app.get("/")
async def root():
    return {"message": "Hello Applications!"}