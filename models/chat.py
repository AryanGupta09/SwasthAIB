from typing import Optional
from datetime import datetime
from beanie import Document

class Chat(Document):
    userId: str
    role: str
    message: str
    timestamp: datetime = datetime.now()

    class Settings:
        name = "chats"
