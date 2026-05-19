from fastapi import APIRouter
from controllers.auth_controller import register, login, RegisterRequest, LoginRequest

router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.post("/register")
async def register_route(data: RegisterRequest):
    return await register(data)

@router.post("/login")
async def login_route(data: LoginRequest):
    return await login(data)
