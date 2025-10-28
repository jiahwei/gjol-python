"""APP 的入口

"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# from src.task.daily import scheduler,apscheduler_start
from src.bulletin.router import router as bulletin_router
from src.dev.router import router as dev_router
from src.database import create_db_and_tables
from src.logs.service import setup_logging

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

ENV = os.getenv("ENV", "development")

# 根据环境决定是否显示文档
docs_url = None if ENV == "production" else "/docs"
redoc_url = None if ENV == "production" else "/redoc"
openapi_url = None if ENV == "production" else "/openapi.json"

app = FastAPI(
    lifespan=lifespan,
    title="gjoldb API",
    description="gjoldbAPI",
    version="1.0.0",
    docs_url=docs_url,
    redoc_url=redoc_url,
    openapi_url=openapi_url,
)

# 根据环境配置CORS
if ENV == "production":
    origins = [
        "https://gjoldb.info",
        "https://www.gjoldb.info",
    ]
else:
    origins = ["*"]  # 开发环境允许所有来源

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(bulletin_router, prefix="/bulletins", tags=["公告"])
app.include_router(dev_router, prefix="/dev", tags=["开发"])


@app.get("/")
async def root():
    return {"message": "Hello Applications!"}