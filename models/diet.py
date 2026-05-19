from typing import Optional, List, Any
from datetime import datetime
from beanie import Document
from pydantic import BaseModel

class MealsData(BaseModel):
    dailyProteinTarget: Optional[float] = None
    breakfast: Optional[List[Any]] = []
    lunch: Optional[List[Any]] = []
    snacks: Optional[List[Any]] = []
    dinner: Optional[List[Any]] = []

class Diet(Document):
    userId: str
    bmi: Optional[float] = None
    goal: Optional[str] = None
    dailyProteinTarget: Optional[float] = None
    meals: Optional[MealsData] = None
    createdAt: datetime = datetime.now()

    class Settings:
        name = "diets"
