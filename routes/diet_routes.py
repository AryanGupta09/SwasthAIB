from fastapi import APIRouter, Depends
from controllers.diet_controller import generate_diet, swap_meal, get_latest_diet, GenerateDietRequest, SwapMealRequest
from middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/api/diet", tags=["Diet"])

@router.post("/generate")
async def generate_diet_route(data: GenerateDietRequest, user_id: str = Depends(get_current_user)):
    return await generate_diet(data, user_id)

@router.post("/swap-meal")
async def swap_meal_route(data: SwapMealRequest, user_id: str = Depends(get_current_user)):
    return await swap_meal(data, user_id)

@router.get("/latest")
async def get_latest_diet_route(user_id: str = Depends(get_current_user)):
    return await get_latest_diet(user_id)
