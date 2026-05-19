import os
from fastapi import HTTPException
from pydantic import BaseModel
from groq import Groq
from models.chat import Chat
from dotenv import load_dotenv

load_dotenv()

class SendMessageRequest(BaseModel):
    message: str

async def send_message(data: SendMessageRequest, user_id: str):
    try:
        if not data.message or not data.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        previous_chats = await Chat.find(Chat.userId == user_id).sort(-Chat.timestamp).limit(10).to_list()
        previous_chats.reverse()
        conversation_history = [{"role": "system", "content": 'You are an expert Indian fitness and nutrition coach named "SwasthAI Coach". Give practical advice using Indian food examples. Keep responses concise and encouraging.'}]
        for chat in previous_chats:
            conversation_history.append({"role": "user" if chat.role == "user" else "assistant", "content": chat.message})
        conversation_history.append({"role": "user", "content": data.message})
        chat_completion = groq_client.chat.completions.create(messages=conversation_history, model="llama-3.3-70b-versatile", temperature=0.8, max_tokens=500)
        reply = chat_completion.choices[0].message.content or "Sorry, I could not generate a response."
        await Chat(userId=user_id, role="user", message=data.message.strip()).insert()
        await Chat(userId=user_id, role="assistant", message=reply.strip()).insert()
        return {"success": True, "reply": reply.strip()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat service unavailable: {str(e)}")

async def get_chat_history(user_id: str):
    try:
        chats = await Chat.find(Chat.userId == user_id).sort(+Chat.timestamp).limit(50).to_list()
        result = []
        for chat in chats:
            c = chat.dict()
            c["_id"] = str(chat.id)
            result.append(c)
        return {"success": True, "chats": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch chat history: {str(e)}")

async def clear_chat_history(user_id: str):
    try:
        await Chat.find(Chat.userId == user_id).delete()
        return {"success": True, "message": "Chat history cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear chat history: {str(e)}")
