from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.core.database import get_db
from app.core.auth import verify_password, create_access_token, decode_token, get_password_hash
from app.models.models import User

router = APIRouter()
security = HTTPBearer()

@router.post("/login")
async def login(email: str, password: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"sub": user.id, "email": user.email, "role": user.role.value})
    return {"access_token": token, "token_type": "bearer", "user_id": user.id}

@router.post("/register")
async def register(email: str, password: str, name: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    from app.core.auth import get_password_hash
    user = User(
        id=str(uuid.uuid4()),
        email=email,
        name=name,
        password_hash=get_password_hash(password)
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return {"user_id": user.id, "email": user.email}

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: AsyncSession = Depends(get_db)):
    token = credentials.credentials
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    result = await db.execute(select(User).where(User.id == payload["sub"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user
