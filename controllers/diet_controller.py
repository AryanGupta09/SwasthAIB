import os
import json
from fastapi import HTTPException
from pydantic import BaseModel
from typing import Optional, List, Any
from beanie import PydanticObjectId
from groq import Groq
from models.user import User, LatestDietPlan
from models.diet import Diet, MealsData
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class GenerateDietRequest(BaseModel):
    goal: Optional[str] = "maintain"
    foodPreference: Optional[str] = None
    diseases: Optional[List[str]] = []

class SwapMealRequest(BaseModel):
    mealType: Optional[str] = None
    currentMeal: Optional[str] = None
    preference: Optional[str] = None

def to_oid(user_id: str):
    return PydanticObjectId(user_id)

def get_meal_type_by_time() -> str:
    hour = datetime.now().hour
    if 5 <= hour < 11:
        return "breakfast"
    elif 11 <= hour < 15:
        return "lunch"
    elif 15 <= hour < 18:
        return "snacks"
    else:
        return "dinner"

async def generate_diet(data: GenerateDietRequest, user_id: str):
    try:
        user = await User.get(to_oid(user_id))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        bmi = user.bmi or 22.0
        weight = user.weight or 70.0
        goal = data.goal or "maintain"
        food_pref = data.foodPreference or user.foodPreference or "vegetarian"
        diseases = data.diseases or user.diseases or []
        diseases_str = ", ".join(diseases) if diseases else "none"

        daily_protein = round(weight * 1.2, 1)

        prompt = f"""You are an expert Indian nutritionist. Create a detailed one-day Indian diet plan.

User Profile:
- BMI: {bmi}
- Weight: {weight} kg
- Goal: {goal}
- Food Preference: {food_pref}
- Health Conditions: {diseases_str}
- Daily Protein Target: {daily_protein}g

Return ONLY a valid JSON object (no markdown, no explanation) in this exact format:
{{
  "breakfast": [
    {{"meal": "Oats Upma with vegetables", "protein": 8}},
    {{"meal": "Boiled eggs (2)", "protein": 12}},
    {{"meal": "Green tea", "protein": 0}}
  ],
  "lunch": [
    {{"meal": "Dal tadka with 2 rotis", "protein": 15}},
    {{"meal": "Paneer bhurji", "protein": 18}},
    {{"meal": "Cucumber raita", "protein": 4}}
  ],
  "snacks": [
    {{"meal": "Roasted chana (30g)", "protein": 8}},
    {{"meal": "Buttermilk", "protein": 3}}
  ],
  "dinner": [
    {{"meal": "Moong dal khichdi", "protein": 12}},
    {{"meal": "Mixed vegetable sabzi", "protein": 5}},
    {{"meal": "Low-fat curd", "protein": 6}}
  ]
}}

Make meals appropriate for the user's food preference ({food_pref}) and health conditions ({diseases_str}).
Use common Indian foods. Each meal entry must have "meal" (string) and "protein" (number in grams)."""

        groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        response = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are an expert Indian nutritionist. Always respond with valid JSON only, no markdown formatting."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=1000
        )

        raw = response.choices[0].message.content or "{}"
        raw = raw.strip()
        # Strip markdown code blocks if present
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])

        try:
            meals_json = json.loads(raw)
        except json.JSONDecodeError:
            # Fallback default plan
            meals_json = {
                "breakfast": [{"meal": "Poha with peanuts", "protein": 8}, {"meal": "Banana", "protein": 1}],
                "lunch": [{"meal": "Dal rice", "protein": 14}, {"meal": "Sabzi", "protein": 4}],
                "snacks": [{"meal": "Roasted chana", "protein": 8}],
                "dinner": [{"meal": "Roti with dal", "protein": 12}, {"meal": "Salad", "protein": 2}]
            }

        meals_data = MealsData(
            dailyProteinTarget=daily_protein,
            breakfast=meals_json.get("breakfast", []),
            lunch=meals_json.get("lunch", []),
            snacks=meals_json.get("snacks", []),
            dinner=meals_json.get("dinner", [])
        )

        # Save diet document
        diet = Diet(
            userId=user_id,
            bmi=bmi,
            goal=goal,
            dailyProteinTarget=daily_protein,
            meals=meals_data,
            createdAt=datetime.now()
        )
        await diet.insert()

        # Update user's latest diet plan
        user.latestDietPlan = LatestDietPlan(
            meals=meals_json,
            bmi=bmi,
            goal=goal,
            dailyProteinTarget=daily_protein,
            createdAt=datetime.now()
        )
        await user.save()

        return {
            "success": True,
            "dietPlan": {
                "bmi": bmi,
                "goal": goal,
                "dailyProteinTarget": daily_protein,
                "meals": meals_json
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate diet plan: {str(e)}")

async def swap_meal(data: SwapMealRequest, user_id: str):
    try:
        user = await User.get(to_oid(user_id))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        meal_type = data.mealType or get_meal_type_by_time()
        current_meal = data.currentMeal or "current meal"
        food_pref = data.preference or user.foodPreference or "vegetarian"

        prompt = f"""You are an expert Indian nutritionist. Suggest 3 alternative Indian meal options to swap for: "{current_meal}"

Meal type: {meal_type}
Food preference: {food_pref}
User health conditions: {", ".join(user.diseases or []) or "none"}

Return ONLY a valid JSON array (no markdown) like:
[
  {{"meal": "Moong dal chilla", "protein": 12, "reason": "High protein, easy to digest"}},
  {{"meal": "Paneer sandwich on whole wheat", "protein": 15, "reason": "Good protein and fiber"}},
  {{"meal": "Sprouts salad with lemon", "protein": 9, "reason": "Light and nutritious"}}
]"""

        groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        response = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are an expert Indian nutritionist. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.8,
            max_tokens=400
        )

        raw = response.choices[0].message.content or "[]"
        raw = raw.strip()
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])

        try:
            alternatives = json.loads(raw)
        except json.JSONDecodeError:
            alternatives = [
                {"meal": "Moong dal chilla", "protein": 12, "reason": "High protein and easy to digest"},
                {"meal": "Vegetable upma", "protein": 6, "reason": "Light and filling"},
                {"meal": "Curd rice", "protein": 8, "reason": "Probiotic and cooling"}
            ]

        return {
            "success": True,
            "mealType": meal_type,
            "currentMeal": current_meal,
            "alternatives": alternatives
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to swap meal: {str(e)}")

async def get_latest_diet(user_id: str):
    try:
        user = await User.get(to_oid(user_id))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if not user.latestDietPlan:
            return {"success": True, "dietPlan": None}
        plan = user.latestDietPlan.dict()
        return {"success": True, "dietPlan": plan}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch diet plan: {str(e)}")
