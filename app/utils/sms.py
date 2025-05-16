# File: backend/app/utils/sms.py
# Status: COMPLETE
# Dependencies: requests, app.core.config

import requests
from typing import Dict, Any
from app.core.config import settings

def send_sms(
    phone_number: str,
    message: str
) -> bool:
    """
    Send SMS using Africa's Talking API
    
    Args:
        phone_number: Recipient phone number
        message: SMS message content
        
    Returns:
        True if SMS sent successfully, False otherwise
    """
    # Format phone number if needed
    if not phone_number.startswith("+"):
        # Add Kenyan country code if not present
        if phone_number.startswith("0"):
            phone_number = "+254" + phone_number[1:]
        elif phone_number.startswith("254"):
            phone_number = "+" + phone_number
        else:
            phone_number = "+254" + phone_number
            
    # Prepare API request
    url = "https://api.africastalking.com/version1/messaging"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
        "ApiKey": settings.AT_API_KEY
    }
    
    payload = {
        "username": settings.AT_USERNAME,
        "to": phone_number,
        "message": message,
        "from": settings.AT_SENDER_ID  # Optional sender ID
    }
    
    try:
        # Send request
        response = requests.post(url, headers=headers, data=payload)
        
        # Check response
        result = response.json()
        
        if result.get("SMSMessageData", {}).get("Recipients", []):
            recipients = result["SMSMessageData"]["Recipients"]
            
            # Check if any recipient was successful
            for recipient in recipients:
                if recipient.get("status") == "Success":
                    return True
                    
        return False
        
    except Exception as e:
        print(f"Error sending SMS: {e}")
        return False