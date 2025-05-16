from typing import Optional, List
from pydantic import BaseModel, ConfigDict
import datetime

# Shared properties
class SubscriptionPlanBase(BaseModel):
    name: Optional[str] = None
    user_type: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    billing_cycle: Optional[str] = None
    tokens_included: Optional[int] = None
    max_listings: Optional[int] = None
    features: Optional[List[str]] = None
    is_active: Optional[bool] = None

# For creating a new subscription plan
class SubscriptionPlanCreate(SubscriptionPlanBase):
    name: str
    user_type: str
    price: float
    currency: str = "KES"
    billing_cycle: str

# For updating a subscription plan
class SubscriptionPlanUpdate(SubscriptionPlanBase):
    pass

# Subscription plan in DB with all properties
class SubscriptionPlanInDBBase(SubscriptionPlanBase):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    
    model_config = ConfigDict(from_attributes=True)

# Subscription plan to return via API
class SubscriptionPlan(SubscriptionPlanInDBBase):
    pass

# User subscription model
class UserSubscriptionBase(BaseModel):
    auto_renew: Optional[bool] = None

# For creating a new user subscription
class UserSubscriptionCreate(UserSubscriptionBase):
    plan_id: int
    payment_method: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "plan_id": 1,
                "payment_method": "mpesa",
                "auto_renew": True
            }
        }
    )

# For updating a user subscription
class UserSubscriptionUpdate(UserSubscriptionBase):
    pass

# User subscription in DB with all properties
class UserSubscriptionInDBBase(UserSubscriptionBase):
    id: int
    user_id: int
    plan_id: int
    start_date: datetime.datetime
    end_date: datetime.datetime
    created_at: datetime.datetime
    updated_at: datetime.datetime
    
    model_config = ConfigDict(from_attributes=True)

# User subscription to return via API
class UserSubscription(UserSubscriptionInDBBase):
    plan: Optional[SubscriptionPlan] = None