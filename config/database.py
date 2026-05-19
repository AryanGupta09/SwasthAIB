import os
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from dotenv import load_dotenv

load_dotenv()

async def connect_database():
    from models.user import User
    from models.chat import Chat
    from models.diet import Diet
    from models.workout import Workout

    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        raise ValueError("MONGO_URI environment variable not set")

    client = AsyncIOMotorClient(mongo_uri)
    try:
        db = client.get_default_database()
    except Exception:
        db = client["swasthai"]

    await init_beanie(database=db, document_models=[User, Chat, Diet, Workout])
    print("MongoDB connected successfully")
