# File: backend/app/services/notification_service.py
# Status: COMPLETE
# Dependencies: app.utils.email, app.utils.sms, app.models.user, app.core.config

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app import models
from app.utils.email import send_email
from app.utils.sms import send_sms
from app.core.config import settings
from app.crud.user import user as user_crud

class NotificationService:
    def send_verification_request(
        self, 
        owner_id: int, 
        property_id: int, 
        verification_id: int,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Send verification request notification to property owner
        
        Args:
            owner_id: Property owner ID
            property_id: Property ID
            verification_id: Verification ID
            db: Optional database session
            
        Returns:
            Dictionary with notification results
        """
        # Get user if db session provided
        user = None
        if db:
            user = user_crud.get(db, id=owner_id)
            
        # Create verification URL
        verification_url = f"{settings.FRONTEND_URL}/verifications/{verification_id}"
        
        # Prepare notification content
        subject = "Property Verification Required"
        message = (
            f"Please verify the current status of your property listing. "
            f"Is your property still available for rent? "
            f"Please respond within 3 days to maintain your listing status. "
            f"Visit {verification_url} to respond."
        )
        
        # Send email notification
        email_status = {"success": False, "message": "Email not sent"}
        if user and user.email:
            email_status = self._send_email_notification(
                user.email,
                subject,
                message
            )
            
        # Send SMS notification
        sms_status = {"success": False, "message": "SMS not sent"}
        if user and user.phone_number:
            sms_status = self._send_sms_notification(
                user.phone_number,
                f"PataBasefiti: Property verification required. "
                f"Is your property still available? "
                f"Reply YES or NO. Visit app for details."
            )
            
        return {
            "success": email_status["success"] or sms_status["success"],
            "channels": {
                "email": email_status,
                "sms": sms_status
            }
        }
    
    def send_token_purchase_confirmation(
        self, 
        user_id: int, 
        amount: float, 
        tokens: int,
        transaction_id: int,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Send token purchase confirmation
        
        Args:
            user_id: User ID
            amount: Amount paid
            tokens: Number of tokens purchased
            transaction_id: Transaction ID
            db: Optional database session
            
        Returns:
            Dictionary with notification results
        """
        # Get user if db session provided
        user = None
        if db:
            user = user_crud.get(db, id=user_id)
            
        # Prepare notification content
        subject = "Token Purchase Confirmation"
        message = (
            f"Thank you for your purchase of {tokens} tokens for KES {amount}. "
            f"Your token balance has been updated. "
            f"Transaction ID: {transaction_id}"
        )
        
        # Send email notification
        email_status = {"success": False, "message": "Email not sent"}
        if user and user.email:
            email_status = self._send_email_notification(
                user.email,
                subject,
                message
            )
            
        # Send SMS notification
        sms_status = {"success": False, "message": "SMS not sent"}
        if user and user.phone_number:
            sms_status = self._send_sms_notification(
                user.phone_number,
                f"PataBasefiti: {tokens} tokens purchased for KES {amount}. "
                f"Thank you for your purchase."
            )
            
        return {
            "success": email_status["success"] or sms_status["success"],
            "channels": {
                "email": email_status,
                "sms": sms_status
            }
        }
    
    def notify_property_status_change(
        self, 
        property_id: int, 
        new_status: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Notify interested users about property status change
        
        Args:
            property_id: Property ID
            new_status: New property status
            db: Database session
            
        Returns:
            Dictionary with notification results
        """
        # Get property details
        property_obj = db.query(models.Property).filter(models.Property.id == property_id).first()
        if not property_obj:
            return {"success": False, "message": "Property not found"}
            
        # Get users who favorited this property
        favorites_query = """
            SELECT u.* FROM users u
            JOIN property_favorites pf ON u.id = pf.user_id
            WHERE pf.property_id = :property_id
        """
        interested_users = db.execute(favorites_query, {"property_id": property_id}).fetchall()
        
        # Prepare notification content
        status_message = "is now available" if new_status == "available" else f"is now {new_status}"
        subject = f"Property Status Update: {property_obj.title}"
        message = (
            f"A property you're interested in ({property_obj.title}) {status_message}. "
            f"Located at {property_obj.address}, {property_obj.city}. "
            f"Visit the app to view the latest information."
        )
        
        # Send notifications to interested users
        notification_count = 0
        for user_data in interested_users:
            user = models.User(**user_data)
            
            # Check user notification preferences
            preferences = user.notification_preferences_json
            if not preferences.get("status_updates", True):
                continue
                
            # Send email notification
            if user.email and preferences.get("email", True):
                self._send_email_notification(user.email, subject, message)
                
            # Send SMS notification
            if user.phone_number and preferences.get("sms", True):
                self._send_sms_notification(
                    user.phone_number,
                    f"PataBasefiti: Property update - {property_obj.title} {status_message}."
                )
                
            notification_count += 1
            
        return {
            "success": True,
            "notifications_sent": notification_count
        }
    
    def _send_email_notification(
        self, 
        email: str, 
        subject: str, 
        message: str
    ) -> Dict[str, Any]:
        """Send email notification"""
        try:
            send_email(
                recipient_email=email,
                subject=subject,
                body_text=message,
                sender_email=settings.SMTP_SENDER
            )
            return {"success": True, "message": "Email sent successfully"}
        except Exception as e:
            return {"success": False, "message": f"Email sending failed: {str(e)}"}
    
    def _send_sms_notification(
        self, 
        phone_number: str, 
        message: str
    ) -> Dict[str, Any]:
        """Send SMS notification"""
        try:
            send_sms(
                phone_number=phone_number,
                message=message
            )
            return {"success": True, "message": "SMS sent successfully"}
        except Exception as e:
            return {"success": False, "message": f"SMS sending failed: {str(e)}"}

# Create singleton instance
notification_service = NotificationService()