"""
数据库连接和会话管理模块

本模块提供了SQLModel数据库的连接配置、会话管理和表创建功能。
使用SQLite作为默认数据库引擎，支持异步会话获取。
"""

from sqlmodel import Session, SQLModel, create_engine

from constants import DEFAULT_SQLITE_PATH

# 配置SQLite数据库URL
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DEFAULT_SQLITE_PATH}"

# SQLite连接参数，允许在多线程环境中使用
connect_args = {"check_same_thread": False}

# 创建数据库引擎实例，echo=True启用SQL语句日志输出
engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True, connect_args=connect_args)

def get_session():
    """
    创建并返回数据库会话
    
    使用yield返回会话对象，适用于FastAPI的依赖注入系统
    会话在使用完毕后会自动关闭
    
    Returns:
        Session: SQLModel会话对象
    """
    with Session(engine) as session:
        yield session

def create_db_and_tables():
    """
    创建数据库和所有已定义的表
    
    根据SQLModel中定义的模型自动创建数据库表结构
    如果表已存在则不会重新创建
    """
    SQLModel.metadata.create_all(engine)
    