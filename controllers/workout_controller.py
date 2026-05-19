import os
import json
from fastapi import HTTPException
from pydantic import BaseModel
from typing import Optional, List
from beanie import PydanticObjectId
from groq import Groq
from models.workout import Workout
from models.user import User
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

class LogWorkoutRequest(BaseModel):
    workoutType: str
    duration: int
    caloriesBurned: int
    intensity: str
    notes: Optional[str] = None

class WorkoutSuggestionRequest(BaseModel):
    fitnessGoal: Optional[str] = "general fitness"
    fitnessLevel: Optional[str] = "beginner"
    availableTime: Optional[int] = 30
    equipment: Optional[str] = "none"

def to_oid(user_id: str):
    return PydanticObjectId(user_id)

async def log_workout(data: LogWorkoutRequest, user_id: str):
    try:
        workout = Workout(
            userId=user_id,
            workoutType=data.workoutType,
            duration=data.duration,
            caloriesBurned=data.caloriesBurned,
            intensity=data.intensity,
            notes=data.notes,
            date=datetime.now()
        )
        await workout.insert()
        result = workout.dict()
        result["_id"] = str(workout.id)
        return {"success": True, "message": "Workout logged successfully", "workout": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log workout: {str(e)}")

async def get_workout_history(user_id: str):
    try:
        workouts = await Workout.find(Workout.userId == user_id).sort(-Workout.date).limit(50).to_list()
        result = []
        for w in workouts:
            wd = w.dict()
            wd["_id"] = str(w.id)
            result.append(wd)
        return {"success": True, "workouts": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch workout history: {str(e)}")

async def get_weekly_summary(user_id: str):
    try:
        week_ago = datetime.now() - timedelta(days=7)
        workouts = await Workout.find(
            Workout.userId == user_id,
            Workout.date >= week_ago
        ).to_list()

        total_workouts = len(workouts)
        total_calories = sum(w.caloriesBurned for w in workouts)
        total_duration = sum(w.duration for w in workouts)

        workout_types: dict = {}
        for w in workouts:
            wt = w.workoutType
            workout_types[wt] = workout_types.get(wt, 0) + 1

        return {
            "success": True,
            "summary": {
                "totalWorkouts": total_workouts,
                "totalCaloriesBurned": total_calories,
                "totalDurationMinutes": total_duration,
                "workoutTypes": workout_types,
                "averageCaloriesPerWorkout": round(total_calories / total_workouts, 1) if total_workouts > 0 else 0,
                "averageDurationMinutes": round(total_duration / total_workouts, 1) if total_workouts > 0 else 0
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch weekly summary: {str(e)}")

async def delete_workout(workout_id: str, user_id: str):
    try:
        workout = await Workout.get(to_oid(workout_id))
        if not workout:
            raise HTTPException(status_code=404, detail="Workout not found")
        if workout.userId != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this workout")
        await workout.delete()
        return {"success": True, "message": "Workout deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete workout: {str(e)}")

async def get_workout_suggestions(data: WorkoutSuggestionRequest, user_id: str):
    try:
        user = await User.get(to_oid(user_id))
        bmi = user.bmi if user else 22.0
        diseases = ", ".join(user.diseases or []) if user else "none"

        prompt = f"""You are an expert Indian fitness coach. Create a personalized workout plan.

User Profile:
- BMI: {bmi}
- Health Conditions: {diseases}
- Fitness Goal: {data.fitnessGoal}
- Fitness Level: {data.fitnessLevel}
- Available Time: {data.availableTime} minutes
- Equipment: {data.equipment}

Return ONLY a valid JSON object (no markdown) in this format:
{{
  "warmup": [
    {{"exercise": "Jumping jacks", "duration": "2 minutes", "sets": null, "reps": null}},
    {{"exercise": "Arm circles", "duration": "1 minute", "sets": null, "reps": null}}
  ],
  "mainWorkout": [
    {{"exercise": "Squats", "duration": null, "sets": 3, "reps": 15}},
    {{"exercise": "Push-ups", "duration": null, "sets": 3, "reps": 10}},
    {{"exercise": "Plank", "duration": "30 seconds", "sets": 3, "reps": null}}
  ],
  "cooldown": [
    {{"exercise": "Child's pose stretch", "duration": "1 minute", "sets": null, "reps": null}},
    {{"exercise": "Hamstring stretch", "duration": "1 minute", "sets": null, "reps": null}}
  ],
  "tips": [
    "Stay hydrated throughout the workout",
    "Focus on form over speed"
  ],
  "estimatedCalories": 200
}}

Tailor exercises to the fitness level ({data.fitnessLevel}) and available time ({data.availableTime} min).
Consider health conditions: {diseases}."""

        groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        response = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are an expert fitness coach. Always respond with valid JSON only, no markdown."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=800
        )

        raw = response.choices[0].message.content or "{}"
        raw = raw.strip()
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])

        try:
            suggestions = json.loads(raw)
        except json.JSONDecodeError:
            suggestions = {
                "warmup": [{"exercise": "Jumping jacks", "duration": "2 minutes", "sets": None, "reps": None}],
                "mainWorkout": [
                    {"exercise": "Squats", "duration": None, "sets": 3, "reps": 15},
                    {"exercise": "Push-ups", "duration": None, "sets": 3, "reps": 10}
                ],
                "cooldown": [{"exercise": "Stretching", "duration": "3 minutes", "sets": None, "reps": None}],
                "tips": ["Stay hydrated", "Rest between sets"],
                "estimatedCalories": 150
            }

        return {
            "success": True,
            "fitnessGoal": data.fitnessGoal,
            "fitnessLevel": data.fitnessLevel,
            "availableTime": data.availableTime,
            "suggestions": suggestions
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workout suggestions: {str(e)}")
