from fastapi import APIRouter, Depends
from controllers.workout_controller import log_workout, get_workout_history, get_weekly_summary, delete_workout, get_workout_suggestions, LogWorkoutRequest, WorkoutSuggestionRequest
from middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/api/workout", tags=["Workout"])

@router.post("/log")
async def log_workout_route(data: LogWorkoutRequest, user_id: str = Depends(get_current_user)):
    return await log_workout(data, user_id)

@router.get("/history")
async def get_history_route(user_id: str = Depends(get_current_user)):
    return await get_workout_history(user_id)

@router.get("/weekly-summary")
async def weekly_summary_route(user_id: str = Depends(get_current_user)):
    return await get_weekly_summary(user_id)

@router.delete("/{workout_id}")
async def delete_workout_route(workout_id: str, user_id: str = Depends(get_current_user)):
    return await delete_workout(workout_id, user_id)

@router.post("/suggestions")
async def suggestions_route(data: WorkoutSuggestionRequest, user_id: str = Depends(get_current_user)):
    return await get_workout_suggestions(data, user_id)
