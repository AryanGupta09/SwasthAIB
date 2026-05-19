from fastapi import HTTPException
from pydantic import BaseModel
from typing import Optional
from beanie import PydanticObjectId
from models.user import User, BMIRecord
from datetime import datetime

class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    foodPreference: Optional[str] = None
    diseases: Optional[object] = None

class AddBMIRequest(BaseModel):
    weight: float
    height: float
    bmi: float

def to_oid(user_id: str):
    return PydanticObjectId(user_id)

async def get_user_profile(user_id: str):
    try:
        user = await User.get(to_oid(user_id))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user_data = user.dict()
        user_data["_id"] = str(user.id)
        user_data.pop("password", None)
        return user_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch profile: {str(e)}")

async def update_user_profile(data: UpdateProfileRequest, user_id: str):
    try:
        user = await User.get(to_oid(user_id))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if data.name is not None: user.name = data.name
        if data.age is not None: user.age = int(data.age)
        if data.gender is not None: user.gender = data.gender
        if data.foodPreference is not None: user.foodPreference = data.foodPreference
        if data.height is not None: user.height = float(data.height)
        if data.weight is not None: user.weight = float(data.weight)
        if user.height and user.weight:
            h = user.height / 100
            user.bmi = round(user.weight / (h * h), 1)
        if data.diseases is not None:
            if isinstance(data.diseases, list): user.diseases = data.diseases
            elif isinstance(data.diseases, str): user.diseases = [d.strip() for d in data.diseases.split(",")] if data.diseases else []
            else: user.diseases = []
        user.updatedAt = datetime.now()
        await user.save()
        updated = user.dict()
        updated["_id"] = str(user.id)
        updated.pop("password", None)
        return {"message": "Profile updated successfully", "user": updated}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")

async def get_bmi_history(user_id: str):
    try:
        user = await User.get(to_oid(user_id))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"bmiHistory": user.bmiHistory or []}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch BMI history: {str(e)}")

async def add_bmi_record(data: AddBMIRequest, user_id: str):
    try:
        user = await User.get(to_oid(user_id))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if user.bmiHistory is None: user.bmiHistory = []
        user.bmiHistory.append(BMIRecord(weight=float(data.weight), height=float(data.height), bmi=float(data.bmi), date=datetime.now()))
        if len(user.bmiHistory) > 30: user.bmiHistory = user.bmiHistory[-30:]
        user.weight = float(data.weight)
        user.height = float(data.height)
        user.bmi = float(data.bmi)
        user.updatedAt = datetime.now()
        await user.save()
        return {"message": "BMI record added successfully", "bmiHistory": [r.dict() for r in user.bmiHistory]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add BMI record: {str(e)}")
