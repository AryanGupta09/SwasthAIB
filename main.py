import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from config.database import connect_database
from routes.auth_routes import router as auth_router
from routes.chat_routes import router as chat_router
from routes.diet_routes import router as diet_router
from routes.user_routes import router as user_router
from routes.health_routes import router as health_router
from routes.workout_routes import router as workout_router

load_dotenv()

app = FastAPI(
    title="SwasthAI Backend",
    description="Indian Fitness & Nutrition AI Backend",
    version="2.0.0",
)

@app.on_event("startup")
async def startup_event():
    try:
        await connect_database()
    except Exception as e:
        print(f"STARTUP ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise

limiter = Limiter(key_func=get_remote_address, default_limits=["100/15minutes"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

node_env = os.getenv("NODE_ENV", "development")

if node_env == "production":
    allowed_origins = [
        "https://swasthai.vercel.app",
        "https://swasthai-frontend.vercel.app",
    ]
    allow_origin_regex = r"https://.*\.vercel\.app"
else:
    allowed_origins = ["http://localhost:5173"]
    allow_origin_regex = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=allow_origin_regex,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(diet_router)
app.include_router(user_router)
app.include_router(health_router)
app.include_router(workout_router)

@app.get("/")
async def root():
    return {"message": "SwasthAI Python Backend Running"}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error", "error": str(exc)}
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 5000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
