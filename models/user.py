from typing import Optional, List, Any
from datetime import datetime
from beanie import Document
from pydantic import BaseModel, ConfigDict

class BMIRecord(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    weight: float
    height: float
    bmi: float
    date: datetime = datetime.now()

class MealOption(BaseModel):
    meal: str
    protein: Optional[float] = None

class MealsData(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    dailyProteinTarget: Optional[float] = None
    breakfast: Optional[List[Any]] = []
    lunch: Optional[List[Any]] = []
    snacks: Optional[List[Any]] = []
    dinner: Optional[List[Any]] = []

class LatestDietPlan(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    meals: Optional[Any] = None
    bmi: Optional[float] = None
    goal: Optional[str] = None
    dailyProteinTarget: Optional[float] = None
    createdAt: datetime = datetime.now()

class User(Document):
    name: Optional[str] = None
    email: str
    password: str
    height: Optional[float] = None
    weight: Optional[float] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    foodPreference: Optional[str] = None
    diseases: Optional[List[str]] = []
    bmi: Optional[float] = None
    bmiHistory: Optional[List[BMIRecord]] = []
    latestDietPlan: Optional[LatestDietPlan] = None
    profilePicture: Optional[str] = None
    createdAt: datetime = datetime.now()
    updatedAt: datetime = datetime.now()

    class Settings:
        name = "users"
