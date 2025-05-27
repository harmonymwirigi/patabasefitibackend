# backend/app/api/api_v1/endpoints/messages.py
# Complete messages endpoint for the messaging system

from typing import Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func
from pydantic import BaseModel
import uuid

from app import crud, models
from app.api import deps

router = APIRouter()

# Pydantic models for request/response
class ConversationCreate(BaseModel):
    receiver_id: int
    property_id: Optional[int] = None
    initial_message: Optional[str] = None

class MessageSend(BaseModel):
    conversation_id: str
    receiver_id: int
    content: str

class ConversationResponse(BaseModel):
    id: str
    participants: List[dict]
    property: Optional[dict] = None
    last_message: Optional[dict] = None
    unread_count: int
    created_at: datetime
    updated_at: datetime

class MessageResponse(BaseModel):
    id: int
    conversation_id: str
    sender_id: int
    receiver_id: int
    content: str
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime
    sender: dict

@router.get("/conversations", response_model=List[ConversationResponse])
def get_conversations(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = 50
) -> Any:
    """
    Get all conversations for the current user.
    """
    try:
        # Get conversations where user is a participant
        conversations = db.query(models.Message.conversation_id).filter(
            or_(
                models.Message.sender_id == current_user.id,
                models.Message.receiver_id == current_user.id
            )
        ).distinct().all()
        
        conversation_ids = [c.conversation_id for c in conversations]
        
        result = []
        for conv_id in conversation_ids:
            # Get all participants in this conversation
            participants_query = db.query(models.Message.sender_id, models.Message.receiver_id).filter(
                models.Message.conversation_id == conv_id
            ).distinct().all()
            
            participant_ids = set()
            for p in participants_query:
                participant_ids.add(p.sender_id)
                participant_ids.add(p.receiver_id)
            
            # Get participant details
            participants = db.query(models.User).filter(
                models.User.id.in_(participant_ids)
            ).all()
            
            # Get last message
            last_message = db.query(models.Message).filter(
                models.Message.conversation_id == conv_id
            ).order_by(desc(models.Message.created_at)).first()
            
            # Count unread messages for current user
            unread_count = db.query(models.Message).filter(
                models.Message.conversation_id == conv_id,
                models.Message.receiver_id == current_user.id,
                models.Message.is_read == False
            ).count()
            
            # Get property info if exists
            property_info = None
            if last_message and last_message.property_id:
                property_obj = db.query(models.Property).filter(
                    models.Property.id == last_message.property_id
                ).first()
                if property_obj:
                    property_info = {
                        "id": property_obj.id,
                        "title": property_obj.title
                    }
            
            # Format response
            conversation_data = {
                "id": conv_id,
                "participants": [
                    {
                        "id": p.id,
                        "full_name": p.full_name,
                        "email": p.email,
                        "profile_image": p.profile_image
                    } for p in participants
                ],
                "property": property_info,
                "last_message": {
                    "id": last_message.id,
                    "content": last_message.content,
                    "sender_id": last_message.sender_id,
                    "created_at": last_message.created_at,
                    "is_read": last_message.is_read
                } if last_message else None,
                "unread_count": unread_count,
                "created_at": last_message.created_at if last_message else datetime.utcnow(),
                "updated_at": last_message.created_at if last_message else datetime.utcnow()
            }
            
            result.append(conversation_data)
        
        # Sort by last message time
        result.sort(key=lambda x: x["updated_at"], reverse=True)
        
        return result[skip:skip + limit]
        
    except Exception as e:
        print(f"Error getting conversations: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving conversations: {str(e)}"
        )

@router.post("/conversations", response_model=ConversationResponse)
def create_conversation(
    *,
    db: Session = Depends(deps.get_db),
    conversation_in: ConversationCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create a new conversation.
    """
    try:
        # Check if receiver exists
        receiver = db.query(models.User).filter(
            models.User.id == conversation_in.receiver_id
        ).first()
        
        if not receiver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Receiver not found"
            )
        
        # Check if conversation already exists
        existing_conversation = db.query(models.Message.conversation_id).filter(
            or_(
                and_(
                    models.Message.sender_id == current_user.id,
                    models.Message.receiver_id == conversation_in.receiver_id
                ),
                and_(
                    models.Message.sender_id == conversation_in.receiver_id,
                    models.Message.receiver_id == current_user.id
                )
            )
        ).first()
        
        if existing_conversation:
            # Return existing conversation
            conv_id = existing_conversation.conversation_id
        else:
            # Create new conversation ID
            conv_id = str(uuid.uuid4())
        
        # If initial message provided, send it
        if conversation_in.initial_message:
            message = models.Message(
                conversation_id=conv_id,
                sender_id=current_user.id,
                receiver_id=conversation_in.receiver_id,
                property_id=conversation_in.property_id,
                content=conversation_in.initial_message,
                status="sent"
            )
            db.add(message)
            db.commit()
            db.refresh(message)
        
        # Return conversation details
        participants = [
            {
                "id": current_user.id,
                "full_name": current_user.full_name,
                "email": current_user.email,
                "profile_image": current_user.profile_image
            },
            {
                "id": receiver.id,
                "full_name": receiver.full_name,
                "email": receiver.email,
                "profile_image": receiver.profile_image
            }
        ]
        
        property_info = None
        if conversation_in.property_id:
            property_obj = db.query(models.Property).filter(
                models.Property.id == conversation_in.property_id
            ).first()
            if property_obj:
                property_info = {
                    "id": property_obj.id,
                    "title": property_obj.title
                }
        
        return {
            "id": conv_id,
            "participants": participants,
            "property": property_info,
            "last_message": None,
            "unread_count": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error creating conversation: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating conversation: {str(e)}"
        )

@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
def get_messages(
    *,
    db: Session = Depends(deps.get_db),
    conversation_id: str,
    current_user: models.User = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    Get messages for a specific conversation.
    """
    try:
        # Verify user has access to this conversation
        user_message = db.query(models.Message).filter(
            models.Message.conversation_id == conversation_id,
            or_(
                models.Message.sender_id == current_user.id,
                models.Message.receiver_id == current_user.id
            )
        ).first()
        
        if not user_message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found or access denied"
            )
        
        # Get messages with sender info
        messages = db.query(models.Message).options(
            joinedload(models.Message.sender)
        ).filter(
            models.Message.conversation_id == conversation_id
        ).order_by(models.Message.created_at).offset(skip).limit(limit).all()
        
        result = []
        for message in messages:
            message_data = {
                "id": message.id,
                "conversation_id": message.conversation_id,
                "sender_id": message.sender_id,
                "receiver_id": message.receiver_id,
                "content": message.content,
                "is_read": message.is_read,
                "read_at": message.read_at,
                "created_at": message.created_at,
                "sender": {
                    "id": message.sender.id,
                    "full_name": message.sender.full_name,
                    "email": message.sender.email,
                    "profile_image": message.sender.profile_image
                }
            }
            result.append(message_data)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting messages: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving messages: {str(e)}"
        )

@router.post("/send", response_model=MessageResponse)
def send_message(
    *,
    db: Session = Depends(deps.get_db),
    message_in: MessageSend,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Send a message.
    """
    try:
        # Verify receiver exists
        receiver = db.query(models.User).filter(
            models.User.id == message_in.receiver_id
        ).first()
        
        if not receiver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Receiver not found"
            )
        
        # Create message
        message = models.Message(
            conversation_id=message_in.conversation_id,
            sender_id=current_user.id,
            receiver_id=message_in.receiver_id,
            content=message_in.content,
            status="sent"
        )
        
        db.add(message)
        db.commit()
        db.refresh(message)
        
        # Return message with sender info
        return {
            "id": message.id,
            "conversation_id": message.conversation_id,
            "sender_id": message.sender_id,
            "receiver_id": message.receiver_id,
            "content": message.content,
            "is_read": message.is_read,
            "read_at": message.read_at,
            "created_at": message.created_at,
            "sender": {
                "id": current_user.id,
                "full_name": current_user.full_name,
                "email": current_user.email,
                "profile_image": current_user.profile_image
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error sending message: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending message: {str(e)}"
        )

@router.put("/{message_id}/read")
def mark_message_as_read(
    *,
    db: Session = Depends(deps.get_db),
    message_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Mark a message as read.
    """
    try:
        message = db.query(models.Message).filter(
            models.Message.id == message_id,
            models.Message.receiver_id == current_user.id
        ).first()
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        message.is_read = True
        message.read_at = datetime.utcnow()
        
        db.add(message)
        db.commit()
        
        return {"success": True, "message": "Message marked as read"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error marking message as read: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error marking message as read: {str(e)}"
        )

@router.get("/unread-count")
def get_unread_count(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get total unread message count for current user.
    """
    try:
        count = db.query(models.Message).filter(
            models.Message.receiver_id == current_user.id,
            models.Message.is_read == False
        ).count()
        
        return {"total_unread": count}
        
    except Exception as e:
        print(f"Error getting unread count: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting unread count: {str(e)}"
        )
    
@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation_by_id(
    *,
    db: Session = Depends(deps.get_db),
    conversation_id: str,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get a specific conversation by ID.
    """
    try:
        # Verify user has access to this conversation
        user_message = db.query(models.Message).filter(
            models.Message.conversation_id == conversation_id,
            or_(
                models.Message.sender_id == current_user.id,
                models.Message.receiver_id == current_user.id
            )
        ).first()
        
        if not user_message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found or access denied"
            )
        
        # Get all participants in this conversation
        participants_query = db.query(models.Message.sender_id, models.Message.receiver_id).filter(
            models.Message.conversation_id == conversation_id
        ).distinct().all()
        
        participant_ids = set()
        for p in participants_query:
            participant_ids.add(p.sender_id)
            participant_ids.add(p.receiver_id)
        
        # Get participant details
        participants = db.query(models.User).filter(
            models.User.id.in_(participant_ids)
        ).all()
        
        # Get last message
        last_message = db.query(models.Message).filter(
            models.Message.conversation_id == conversation_id
        ).order_by(desc(models.Message.created_at)).first()
        
        # Count unread messages for current user
        unread_count = db.query(models.Message).filter(
            models.Message.conversation_id == conversation_id,
            models.Message.receiver_id == current_user.id,
            models.Message.is_read == False
        ).count()
        
        # Get property info if exists
        property_info = None
        if last_message and last_message.property_id:
            property_obj = db.query(models.Property).filter(
                models.Property.id == last_message.property_id
            ).first()
            if property_obj:
                property_info = {
                    "id": property_obj.id,
                    "title": property_obj.title
                }
        
        # Format response
        conversation_data = {
            "id": conversation_id,
            "participants": [
                {
                    "id": p.id,
                    "full_name": p.full_name,
                    "email": p.email,
                    "profile_image": p.profile_image
                } for p in participants
            ],
            "property": property_info,
            "last_message": {
                "id": last_message.id,
                "content": last_message.content,
                "sender_id": last_message.sender_id,
                "created_at": last_message.created_at,
                "is_read": last_message.is_read
            } if last_message else None,
            "unread_count": unread_count,
            "created_at": last_message.created_at if last_message else datetime.utcnow(),
            "updated_at": last_message.created_at if last_message else datetime.utcnow()
        }
        
        return conversation_data
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting conversation: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving conversation: {str(e)}"
        )