import os
import bcrypt
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from jose import jwt
from pydantic import BaseModel
from models.user import User
from dotenv import load_dotenv

load_dotenv()

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

async def register(data: RegisterRequest):
    existing = await User.find_one(User.email == data.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")
    hashed = bcrypt.hashpw(data.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user = User(name=data.name, email=data.email, password=hashed)
    await user.insert()
    return {"message": "User registered successfully"}

async def login(data: LoginRequest):
    user = await User.find_one(User.email == data.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    is_match = bcrypt.checkpw(data.password.encode("utf-8"), user.password.encode("utf-8"))
    if not is_match:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong password")
    secret = os.getenv("JWT_SECRET", "mysecretkey123")
    token = jwt.encode({"id": str(user.id), "exp": datetime.utcnow() + timedelta(days=7)}, secret, algorithm="HS256")
    user_data = user.dict()
    user_data["_id"] = str(user.id)
    user_data.pop("password", None)
    return {"token": token, "user": user_data}
