from fastapi import APIRouter, Depends
from controllers.user_controller import get_user_profile, update_user_profile, get_bmi_history, add_bmi_record, UpdateProfileRequest, AddBMIRequest
from middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/api/user", tags=["User"])

@router.get("/profile")
async def get_profile_route(user_id: str = Depends(get_current_user)):
    return await get_user_profile(user_id)

@router.put("/profile")
async def update_profile_route(data: UpdateProfileRequest, user_id: str = Depends(get_current_user)):
    return await update_user_profile(data, user_id)

@router.get("/bmi-history")
async def get_bmi_history_route(user_id: str = Depends(get_current_user)):
    return await get_bmi_history(user_id)

@router.post("/bmi-history")
async def add_bmi_record_route(data: AddBMIRequest, user_id: str = Depends(get_current_user)):
    return await add_bmi_record(data, user_id)
