from contextlib import asynccontextmanager
from fastapi import FastAPI

# from src.task.daily import scheduler,apscheduler_start
from src.bulletin.router import router as bulletin_router
from src.database import create_db_and_tables
from src.spiders.test import test_resolve_notice
from src.nlp.train_model import train_model
from src.nlp.make_data import make_train_csv
from src.logs.service import LOGGING_CONFIG

from fastapi.middleware.cors import CORSMiddleware

import logging.config

def setup_logging():
    try:
        logging.config.dictConfig(LOGGING_CONFIG)
    except Exception as e:
        print(f"Error in Logging Configuration: {e}")
        logging.basicConfig(level=logging.DEBUG)
setup_logging()

ml_models = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model
    ml_models["create_db_and_tables"] = create_db_and_tables
    # ml_models["apscheduler_start"] = apscheduler_start
    # await apscheduler_start()
    test_resolve_notice(test_date="2025-02-05")
    # make_train_csv()
    # train_model()
    # add_all_html()
    yield
    # Clean up the ML models and release resources
    # scheduler.shutdown()
    ml_models.clear()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(bulletin_router, prefix="/bulletins", tags=["公告"])


@app.get("/")
async def root():
    return {"message": "Hello Applications!"}