# File: backend/app/utils/mpesa.py
# Status: COMPLETE
# Dependencies: requests, base64, datetime

import requests
import base64
import json
from datetime import datetime
from typing import Dict, Any

class MpesaClient:
    """Client for Safaricom M-Pesa API integration"""
    
    def __init__(
        self,
        consumer_key: str,
        consumer_secret: str,
        shortcode: str,
        passkey: str,
        environment: str = "sandbox"
    ):
        """
        Initialize M-Pesa client
        
        Args:
            consumer_key: M-Pesa API consumer key
            consumer_secret: M-Pesa API consumer secret
            shortcode: M-Pesa shortcode (paybill or till number)
            passkey: M-Pesa passkey
            environment: "sandbox" or "production"
        """
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.shortcode = shortcode
        self.passkey = passkey
        
        # Set base URLs based on environment
        if environment == "production":
            self.base_url = "https://api.safaricom.co.ke"
        else:
            self.base_url = "https://sandbox.safaricom.co.ke"
            
        # API endpoints
        self.auth_url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
        self.stk_push_url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
        self.query_url = f"{self.base_url}/mpesa/stkpushquery/v1/query"
    
    def _get_auth_token(self) -> str:
        """
        Get OAuth token for API authentication
        
        Returns:
            Access token string
        """
        # Create authorization string
        auth_string = f"{self.consumer_key}:{self.consumer_secret}"
        auth_bytes = auth_string.encode("ascii")
        auth_b64 = base64.b64encode(auth_bytes).decode("ascii")
        
        # Make request
        headers = {
            "Authorization": f"Basic {auth_b64}"
        }
        
        response = requests.get(self.auth_url, headers=headers)
        
        # Parse response
        result = response.json()
        return result.get("access_token")
    
    def _get_password(self) -> str:
        """
        Generate password for STK push
        
        Returns:
            Base64 encoded password string
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        password_str = f"{self.shortcode}{self.passkey}{timestamp}"
        password_bytes = password_str.encode("ascii")
        return base64.b64encode(password_bytes).decode("ascii"), timestamp
    
    def stk_push(
        self,
        phone_number: str,
        amount: float,
        account_reference: str,
        transaction_desc: str
    ) -> Dict[str, Any]:
        """
        Initiate STK push payment
        
        Args:
            phone_number: Customer phone number (format: 254XXXXXXXXX)
            amount: Amount to charge
            account_reference: Payment reference
            transaction_desc: Transaction description
            
        Returns:
            Dictionary with M-Pesa API response
        """
        # Get authentication token
        token = self._get_auth_token()
        
        # Generate password and timestamp
        password, timestamp = self._get_password()
        
        # Prepare request payload
        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount),  # Convert to integer (no decimal)
            "PartyA": phone_number,
            "PartyB": self.shortcode,
            "PhoneNumber": phone_number,
            "CallBackURL": "https://patabasefiti.example.com/api/v1/mpesa/callback",
            "AccountReference": account_reference,
            "TransactionDesc": transaction_desc
        }
        
        # Make request
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            self.stk_push_url,
            headers=headers,
            data=json.dumps(payload)
        )
        
        # Parse response
        return response.json()
    
    def query_stk_status(self, checkout_request_id: str) -> Dict[str, Any]:
        """
        Query STK push payment status
        
        Args:
            checkout_request_id: Checkout request ID from STK push
            
        Returns:
            Dictionary with payment status
        """
        # Get authentication token
        token = self._get_auth_token()
        
        # Generate password and timestamp
        password, timestamp = self._get_password()
        
        # Prepare request payload
        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "CheckoutRequestID": checkout_request_id
        }
        
        # Make request
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            self.query_url,
            headers=headers,
            data=json.dumps(payload)
        )
        
        # Parse response
        return response.json()