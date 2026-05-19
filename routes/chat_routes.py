from fastapi import APIRouter, Depends
from controllers.chat_controller import send_message, get_chat_history, clear_chat_history, SendMessageRequest
from middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/api/chat", tags=["Chat"])

@router.post("/send")
async def send_message_route(data: SendMessageRequest, user_id: str = Depends(get_current_user)):
    return await send_message(data, user_id)

@router.get("/history")
async def get_history_route(user_id: str = Depends(get_current_user)):
    return await get_chat_history(user_id)

@router.delete("/clear")
async def clear_history_route(user_id: str = Depends(get_current_user)):
    return await clear_chat_history(user_id)
