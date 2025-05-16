# File: backend/app/schemas/transaction.py
# Status: COMPLETE
# Dependencies: pydantic, app.schemas.base
from typing import Optional
from pydantic import BaseModel, ConfigDict
import datetime

# Shared properties
class TransactionBase(BaseModel):
    transaction_type: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    payment_method: Optional[str] = None
    description: Optional[str] = None

# Properties to receive via API on creation
class TransactionCreate(TransactionBase):
    transaction_type: str
    amount: float
    currency: str = "KES"
    payment_method: str

# Properties to receive via API on update
class TransactionUpdate(TransactionBase):
    status: Optional[str] = None
    mpesa_receipt: Optional[str] = None

# Properties shared by models stored in DB
class TransactionInDBBase(TransactionBase):
    id: int
    user_id: int
    status: str
    tokens_purchased: Optional[int] = None
    mpesa_receipt: Optional[str] = None
    package_id: Optional[int] = None
    subscription_id: Optional[int] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    
    model_config = ConfigDict(from_attributes=True)

# Properties to return via API
class Transaction(TransactionInDBBase):
    pass

# M-Pesa payment request
class MpesaPaymentRequest(BaseModel):
    phone_number: str
    amount: float
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "phone_number": "254712345678",
                "amount": 500
            }
        }
    )

# M-Pesa callback data
class MpesaCallback(BaseModel):
    transaction_id: str
    status: str
    amount: float
    phone_number: str
    receipt_number: str