from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_
from app.crud.base import CRUDBase
from app.models import Message
from app.schemas.message import MessageCreate, MessageUpdate

class CRUDMessage(CRUDBase[Message, MessageCreate, MessageUpdate]):
    def create_message(
        self, 
        db: Session, 
        *, 
        sender_id: int, 
        receiver_id: int,
        content: str,
        property_id: Optional[int] = None
    ) -> Message:
        # Generate conversation ID (smaller ID first, then larger ID)
        user_ids = sorted([sender_id, receiver_id])
        conversation_id = f"{user_ids[0]}_{user_ids[1]}"
        
        # If property is involved, add to conversation ID
        if property_id:
            conversation_id = f"{conversation_id}_prop_{property_id}"
        
        db_obj = Message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content,
            property_id=property_id
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_conversation_messages(
        self, db: Session, *, conversation_id: str, skip: int = 0, limit: int = 100
    ) -> List[Message]:
        return (
            db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_user_conversations(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[dict]:
        # This is a complex query that gets the latest message from each conversation
        # and counts unread messages. For SQLite, we'll use a simpler approach.
        
        # First, get all conversation IDs for the user
        conversation_ids = (
            db.query(Message.conversation_id)
            .filter(or_(Message.sender_id == user_id, Message.receiver_id == user_id))
            .distinct()
            .all()
        )
        
        conversation_ids = [conv[0] for conv in conversation_ids]
        
        result = []
        for conv_id in conversation_ids:
            # Get the latest message
            latest_message = (
                db.query(Message)
                .filter(Message.conversation_id == conv_id)
                .order_by(desc(Message.created_at))
                .first()
            )
            
            if not latest_message:
                continue
                
            # Get unread count
            unread_count = (
                db.query(func.count(Message.id))
                .filter(
                    Message.conversation_id == conv_id,
                    Message.receiver_id == user_id,
                    Message.is_read == False
                )
                .scalar()
            )
            
            # Determine the other user in the conversation
            other_user_id = latest_message.sender_id if latest_message.sender_id != user_id else latest_message.receiver_id
            
            result.append({
                "conversation_id": conv_id,
                "other_user_id": other_user_id,
                "property_id": latest_message.property_id,
                "last_message": latest_message.content,
                "last_message_time": latest_message.created_at,
                "unread_count": unread_count or 0
            })
            
        # Sort by latest message time
        result.sort(key=lambda x: x["last_message_time"], reverse=True)
        
        # Apply skip and limit
        return result[skip:skip+limit]
    
    def mark_as_read(
        self, db: Session, *, message_ids: List[int]
    ) -> int:
        count = (
            db.query(Message)
            .filter(Message.id.in_(message_ids))
            .update(
                {"is_read": True, "read_at": func.now()},
                synchronize_session=False
            )
        )
        db.commit()
        return count
    
    def mark_conversation_as_read(
        self, db: Session, *, conversation_id: str, user_id: int
    ) -> int:
        count = (
            db.query(Message)
            .filter(
                Message.conversation_id == conversation_id,
                Message.receiver_id == user_id,
                Message.is_read == False
            )
            .update(
                {"is_read": True, "read_at": func.now()},
                synchronize_session=False
            )
        )
        db.commit()
        return count

message = CRUDMessage(Message)