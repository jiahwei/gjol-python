from contextlib import asynccontextmanager
from fastapi import FastAPI

from src.bulletin.router import router as bulletin_router
from src.database import create_db_and_tables

ml_models = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model
    ml_models["create_db_and_tables"] = create_db_and_tables
    yield
    # Clean up the ML models and release resources
    ml_models.clear()


app = FastAPI(lifespan=lifespan)

app.include_router(bulletin_router, prefix="/bulletins", tags=["公告"])


@app.get("/")
async def root():
    return {"message": "Hello Applications!"}