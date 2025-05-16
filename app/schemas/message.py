# File: backend/app/schemas/message.py
# Status: COMPLETE
# Dependencies: pydantic, app.schemas.base
from typing import Optional, List
from pydantic import BaseModel
import datetime

# Message model
class MessageBase(BaseModel):
    content: str
    property_id: Optional[int] = None

# For creating a new message
class MessageCreate(MessageBase):
    receiver_id: int

# For updating a message (e.g., marking as read)
class MessageUpdate(BaseModel):
    is_read: Optional[bool] = None
    status: Optional[str] = None

# Message in DB with all properties
class MessageInDBBase(MessageBase):
    id: int
    conversation_id: str
    sender_id: int
    receiver_id: int
    is_read: bool
    read_at: Optional[datetime.datetime] = None
    status: str
    created_at: datetime.datetime
    
    class Config:
        orm_mode = True

# Message to return via API
class Message(MessageInDBBase):
    sender_name: Optional[str] = None
    receiver_name: Optional[str] = None
    property_title: Optional[str] = None

# Conversation summary
class Conversation(BaseModel):
    conversation_id: str
    other_user_id: int
    other_user_name: str
    other_user_image: Optional[str] = None
    property_id: Optional[int] = None
    property_title: Optional[str] = None
    last_message: str
    last_message_time: datetime.datetime
    unread_count: int
    
    class Config:
        orm_mode = True

# List of messages in a conversation
class MessageList(BaseModel):
    messages: List[Message]
    conversation_id: str
    other_user: dict
    property: Optional[dict] = None