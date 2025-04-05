import logging.config
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# from src.task.daily import scheduler,apscheduler_start
from src.bulletin.router import router as bulletin_router
from src.dev.router import router as dev_router
from src.database import create_db_and_tables
from src.logs.service import LOGGING_CONFIG


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
    yield
    # Clean up the ML models and release resources
    # scheduler.shutdown()
    ml_models.clear()


app = FastAPI(
    lifespan=lifespan,
    title="gjoldb API",
    description="gjoldbAPI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://gjoldb.info",
        "https://www.gjoldb.info",
        # 如果有其他需要访问API的前端域名，也可以添加在这里
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(bulletin_router, prefix="/bulletins", tags=["公告"])
app.include_router(dev_router, prefix="/dev", tags=["开发"])


@app.get("/")
async def root():
    return {"message": "Hello Applications!"}