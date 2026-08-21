from app.database import engine
from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.routers import health, auth, documents

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Doc Intelligence API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(documents.router)

...


@app.on_event("startup")
async def verify_db_connection():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logging.info("DB CONNECTION OK")
    except Exception as e:
        logging.error(f"DB CONNECTION FAILED: {type(e).__name__}: {e}")
