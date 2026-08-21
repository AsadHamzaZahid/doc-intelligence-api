from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from app.config import settings
from fastapi import FastAPI

app = FastAPI(title="Doc Intelligence API")

engine = create_async_engine(
    # tests the connection before using it, reconnects if dead
    settings.database_url, connect_args={"ssl": "require"},   pool_pre_ping=True,
    pool_recycle=300,)


Async_Sessionmaker = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with Async_Sessionmaker() as session:
        yield session


@app.on_event("startup")
async def verify_db_connection():
    import logging
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logging.info("DB CONNECTION OK")
    except Exception as e:
        logging.error(f"DB CONNECTION FAILED: {type(e).__name__}: {e}")
