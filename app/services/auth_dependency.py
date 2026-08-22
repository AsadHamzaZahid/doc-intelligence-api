from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.config import settings

O2_bearer = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(token: str = Depends(O2_bearer), db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401, detail="authentication failed", headers={"WWW-Authenticate": "Bearer"})

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        user_id: str = payload.get("sub")

        if user_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    results = await db.execute(select(User).where(User.id == user_id))
    user = results.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user
