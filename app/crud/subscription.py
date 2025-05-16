from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta
from app.crud.base import CRUDBase
from app.models import SubscriptionPlan, UserSubscription
from app.schemas.subscription import SubscriptionPlanCreate, SubscriptionPlanUpdate, UserSubscriptionCreate, UserSubscriptionUpdate

class CRUDSubscriptionPlan(CRUDBase[SubscriptionPlan, SubscriptionPlanCreate, SubscriptionPlanUpdate]):
    def get_active_plans(
        self, db: Session, *, user_type: Optional[str] = None, skip: int = 0, limit: int = 100
    ) -> List[SubscriptionPlan]:
        query = db.query(SubscriptionPlan).filter(SubscriptionPlan.is_active == True)
        
        if user_type:
            query = query.filter(SubscriptionPlan.user_type == user_type)
            
        return query.offset(skip).limit(limit).all()

class CRUDUserSubscription(CRUDBase[UserSubscription, UserSubscriptionCreate, UserSubscriptionUpdate]):
    def create_subscription(
        self, 
        db: Session, 
        *, 
        user_id: int, 
        plan_id: int,
        auto_renew: bool = False,
        duration_months: int = 1
    ) -> UserSubscription:
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=30 * duration_months)
        
        db_obj = UserSubscription(
            user_id=user_id,
            plan_id=plan_id,
            start_date=start_date,
            end_date=end_date,
            auto_renew=auto_renew
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_active_subscription(
        self, db: Session, *, user_id: int
    ) -> Optional[UserSubscription]:
        now = datetime.utcnow()
        return (
            db.query(UserSubscription)
            .filter(
                UserSubscription.user_id == user_id,
                UserSubscription.end_date > now
            )
            .order_by(desc(UserSubscription.end_date))
            .first()
        )
    
    def get_user_subscriptions(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[UserSubscription]:
        return (
            db.query(UserSubscription)
            .filter(UserSubscription.user_id == user_id)
            .order_by(desc(UserSubscription.start_date))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def cancel_subscription(
        self, db: Session, *, subscription_id: int
    ) -> UserSubscription:
        subscription = self.get(db, id=subscription_id)
        if subscription:
            subscription.auto_renew = False
            db.add(subscription)
            db.commit()
            db.refresh(subscription)
        return subscription

subscription_plan = CRUDSubscriptionPlan(SubscriptionPlan)
user_subscription = CRUDUserSubscription(UserSubscription)