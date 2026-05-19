from typing import Optional
from datetime import datetime
from beanie import Document

class Workout(Document):
    userId: str
    workoutType: str
    duration: int
    caloriesBurned: int
    intensity: str
    notes: Optional[str] = None
    date: datetime = datetime.now()

    class Settings:
        name = "workouts"
