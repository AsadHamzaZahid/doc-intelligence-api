from app.services.auth_dependency import get_current_user
from fastapi import APIRouter, Depends, status, HTTPException
from app.schemas.user import UserCreate, UserOut, Token
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User
from sqlalchemy import select
from app.services.security import hash_password, verify_password, create_access_token
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Request
from app.services.limiter import limiter


router = APIRouter(prefix="/auth", tags=['auth'])


@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def signup(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    results = await db.execute(select(User).where(User.email == user_in.email))
    user_existing = results.scalar_one_or_none()
    if user_existing:
        raise HTTPException(status_code=400, detail="User already exists")

    new_user = User(email=user_in.email,
                    hash_password=hash_password(user_in.password))

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    results = await db.execute(select(User).where(User.email == form_data.username))
    user = results.scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.hash_password):
        raise HTTPException(status_code=401, detail="login failed completely")

    create_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": create_token, "token_type": "bearer"}


@router.get("/me", response_model=UserOut)
async def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user
