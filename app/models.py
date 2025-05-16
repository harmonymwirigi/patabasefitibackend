from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, or_, func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import datetime
import json

from app.db.database import Base

class BaseJsonMixin:
    """Mixin to handle JSON fields with SQLite compatibility"""
    
    def get_json_field(self, field_name):
        field_value = getattr(self, field_name)
        if not field_value:
            return {}
        if isinstance(field_value, (dict, list)):
            return field_value
        try:
            return json.loads(field_value)
        except:
            return {}
    
    def set_json_field(self, field_name, value):
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        setattr(self, field_name, value)


class Property(Base):
    __tablename__ = "properties"
    
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    property_type = Column(String(50), nullable=False, index=True)
    rent_amount = Column(Float, nullable=False, index=True)
    bedrooms = Column(Integer, nullable=False, index=True)
    bathrooms = Column(Integer, nullable=False)
    size_sqm = Column(Float, nullable=True)
    address = Column(String(255), nullable=False)
    neighborhood = Column(String(255), nullable=True)
    city = Column(String(255), nullable=False, index=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    landmark = Column(String(255), nullable=True)
    availability_status = Column(String(50), default="available", index=True)
    verification_status = Column(String(50), default="pending")
    reliability_score = Column(Float, nullable=True)
    last_verified = Column(DateTime, nullable=True)
    expiration_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    amenities = Column(Text, default='[]')
    lease_terms = Column(Text, default='{}')
    engagement_metrics = Column(Text, default='{"view_count": 0, "favorite_count": 0, "contact_count": 0}')
    auto_verification_settings = Column(Text, default='{"enabled": true, "frequency_days": 7}')
    featured_status = Column(Text, default='{"is_featured": false}')
    
    # Relationships
    owner = relationship("User", back_populates="properties")
    images = relationship("PropertyImage", back_populates="property", cascade="all, delete-orphan")
    verifications = relationship("Verification", back_populates="property", cascade="all, delete-orphan")
    verification_history = relationship("VerificationHistory", back_populates="property", cascade="all, delete-orphan")
    favorites = relationship("PropertyFavorite", back_populates="property", cascade="all, delete-orphan")
    views = relationship("ViewedProperty", back_populates="property", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="property")
    property_amenities = relationship("PropertyAmenity", back_populates="property", cascade="all, delete-orphan")
    
    # JSON methods instead of properties
    
    def get_amenities_json(self):
        try:
            if isinstance(self.amenities, list):
                return self.amenities
            return json.loads(self.amenities) if self.amenities else []
        except:
            return []

    def set_amenities_json(self, value):
        self.amenities = json.dumps(value) if isinstance(value, list) else value

    def get_lease_terms_json(self):
        try:
            if isinstance(self.lease_terms, dict):
                return self.lease_terms
            return json.loads(self.lease_terms) if self.lease_terms else {}
        except:
            return {}

    def set_lease_terms_json(self, value):
        self.lease_terms = json.dumps(value) if isinstance(value, dict) else value

    def get_engagement_metrics_json(self):
        try:
            if isinstance(self.engagement_metrics, dict):
                return self.engagement_metrics
            return json.loads(self.engagement_metrics) if self.engagement_metrics else {"view_count": 0, "favorite_count": 0, "contact_count": 0}
        except:
            return {"view_count": 0, "favorite_count": 0, "contact_count": 0}

    def set_engagement_metrics_json(self, value):
        self.engagement_metrics = json.dumps(value) if isinstance(value, dict) else value

    def get_auto_verification_settings_json(self):
        try:
            return json.loads(self.auto_verification_settings) if self.auto_verification_settings else {"enabled": True, "frequency_days": 7}
        except:
            return {"enabled": True, "frequency_days": 7}

    def set_auto_verification_settings_json(self, value):
        self.auto_verification_settings = json.dumps(value) if value else '{"enabled": true, "frequency_days": 7}'

    def get_featured_status_json(self):
        try:
            return json.loads(self.featured_status) if self.featured_status else {"is_featured": False}
        except:
            return {"is_featured": False}

    def set_featured_status_json(self, value):
        self.featured_status = json.dumps(value) if value else '{"is_featured": false}'

class PropertyAmenity(Base):
    __tablename__ = "property_amenities"
    
    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)
    amenity = Column(String(100), nullable=False)
    
    property = relationship("Property", back_populates="property_amenities")
    
    __table_args__ = (
        UniqueConstraint('property_id', 'amenity', name='unique_property_amenity'),
    )

class PropertyImage(Base):
    __tablename__ = "property_images"
    
    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)
    path = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_primary = Column(Boolean, default=False)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    property = relationship("Property", back_populates="images")

class TokenPackage(Base):
    __tablename__ = "token_packages"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    token_count = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    currency = Column(String(10), default="KES")
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    duration_days = Column(Integer, default=0)
    features = Column(Text, default='[]')
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    transactions = relationship("Transaction", back_populates="token_package")
    
    # JSON methods instead of properties
    def get_features_json(self):
        try:
            return json.loads(self.features) if self.features else []
        except:
            return []
    
    def set_features_json(self, value):
        self.features = json.dumps(value) if value else '[]'

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    transaction_type = Column(String(50), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="KES")
    status = Column(String(50), nullable=False)
    payment_method = Column(String(50), nullable=True)
    mpesa_receipt = Column(String(100), nullable=True)
    tokens_purchased = Column(Integer, nullable=True)
    package_id = Column(Integer, ForeignKey("token_packages.id", ondelete="SET NULL"), nullable=True)
    subscription_id = Column(Integer, ForeignKey("subscription_plans.id", ondelete="SET NULL"), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    user = relationship("User", back_populates="transactions")
    token_package = relationship("TokenPackage", back_populates="transactions")
    subscription_plan = relationship("SubscriptionPlan", back_populates="transactions")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String(100), nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="SET NULL"), nullable=True)
    content = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
    status = Column(String(50), default="sent")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    sender = relationship("User", foreign_keys=[sender_id], back_populates="messages_sent")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="messages_received")
    property = relationship("Property", back_populates="messages")

class Verification(Base):
    __tablename__ = "verifications"
    
    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)
    verification_type = Column(String(50), nullable=False)
    requested_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String(50), default="pending")
    responder_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    expiration = Column(DateTime, nullable=True)
    response_data = Column(Text, nullable=True)
    system_decision = Column(Text, nullable=True)
    
    # Relationships
    property = relationship("Property", back_populates="verifications")
    responder = relationship("User")
    
    # JSON methods instead of properties
    def get_response_json(self):
        try:
            return json.loads(self.response_data) if self.response_data else {}
        except:
            return {}
    
    def set_response_json(self, value):
        self.response_data = json.dumps(value) if value else '{}'
    
    def get_system_decision_json(self):
        try:
            return json.loads(self.system_decision) if self.system_decision else {}
        except:
            return {}
    
    def set_system_decision_json(self, value):
        self.system_decision = json.dumps(value) if value else '{}'

class VerificationHistory(Base):
    __tablename__ = "verification_history"
    
    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), nullable=False)
    verified_by = Column(String(50), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    notes = Column(Text, nullable=True)
    
    property = relationship("Property", back_populates="verification_history")

class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    user_type = Column(String(50), nullable=False)
    price = Column(Float, nullable=False)
    currency = Column(String(10), default="KES")
    billing_cycle = Column(String(50), nullable=False)
    tokens_included = Column(Integer, default=0)
    max_listings = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    features = Column(Text, default='[]')
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    subscriptions = relationship("UserSubscription", back_populates="plan")
    transactions = relationship("Transaction", back_populates="subscription_plan")
    
    # JSON methods instead of properties
    def get_features_json(self):
        try:
            return json.loads(self.features) if self.features else []
        except:
            return []
    
    def set_features_json(self, value):
        self.features = json.dumps(value) if value else '[]'

class UserSubscription(Base):
    __tablename__ = "user_subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id", ondelete="CASCADE"), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    auto_renew = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    user = relationship("User", back_populates="subscriptions")
    plan = relationship("SubscriptionPlan", back_populates="subscriptions")

class SearchHistory(Base):
    __tablename__ = "search_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    parameters = Column(Text, nullable=False)
    results_count = Column(Integer, default=0)
    token_cost = Column(Integer, default=1)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    user = relationship("User", back_populates="search_history")
    
    # JSON methods instead of properties
    def get_parameters_json(self):
        try:
            return json.loads(self.parameters) if self.parameters else {}
        except:
            return {}
    
    def set_parameters_json(self, value):
        self.parameters = json.dumps(value) if value else '{}'

class ViewedProperty(Base):
    __tablename__ = "viewed_properties"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)
    last_viewed = Column(DateTime, default=datetime.datetime.utcnow)
    view_count = Column(Integer, default=1)
    
    user = relationship("User", back_populates="views")
    property = relationship("Property", back_populates="views")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'property_id', name='unique_user_property_view'),
    )

class PropertyFavorite(Base):
    __tablename__ = "property_favorites"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    user = relationship("User", back_populates="favorites")
    property = relationship("Property", back_populates="favorites")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'property_id', name='unique_user_property_favorite'),
    )
class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"
    
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="SET NULL"), nullable=True)
    session_id = Column(String(100), nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    metadata_content = Column(Text, default='{}')  # Renamed from metadata to metadata_content
    location = Column(Text, nullable=True)
    
    user = relationship("User")
    property = relationship("Property")
    
    # JSON methods instead of properties
    def get_metadata_json(self):
        try:
            return json.loads(self.metadata_content) if self.metadata_content else {}
        except:
            return {}
    
    def set_metadata_json(self, value):
        self.metadata_content = json.dumps(value) if value else '{}'

class JSONSerializable:
    """Base mixin for models with JSON fields"""
    
    def get_json_field(self, field_name, default=None):
        """Get a JSON field as a Python object"""
        field_value = getattr(self, field_name)
        if field_value is None:
            return default
            
        if not isinstance(field_value, (dict, list, str)):
            return field_value
            
        if isinstance(field_value, (dict, list)):
            return field_value
            
        try:
            return json.loads(field_value)
        except:
            return default
            
    def set_json_field(self, field_name, value, default=None):
        """Set a JSON field, ensuring it's stored as a JSON string"""
        if value is None:
            setattr(self, field_name, None)
            return
            
        if isinstance(value, str):
            # Check if it's already a valid JSON string
            try:
                json.loads(value)
                setattr(self, field_name, value)
            except:
                setattr(self, field_name, json.dumps(default))
        else:
            # Convert to JSON string
            setattr(self, field_name, json.dumps(value))


class JSONField:
    """Mixin to provide helper methods for JSON fields in SQLite"""
    
    @staticmethod
    def to_json_string(value):
        """Convert value to JSON string if it's a dict or list"""
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            return json.dumps(value)
        return value
    
    @staticmethod
    def from_json_string(value, default=None):
        """Convert JSON string to Python object"""
        if value is None:
            return default
        if isinstance(value, (dict, list)):
            return value
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return default

# Add JSONField methods to existing models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    google_id = Column(String(255), unique=True, nullable=True)
    auth_type = Column(String(50), nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=True)
    phone_number = Column(String(50), nullable=True)
    role = Column(String(50), nullable=False)
    profile_image = Column(String(255), nullable=True)
    token_balance = Column(Integer, default=0)
    reliability_score = Column(Float, nullable=True)
    account_status = Column(String(50), default="active")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    notification_preferences = Column(Text, default='{"email": true, "sms": true, "in_app": true}')
    token_history = Column(Text, default='[]')
    
    # Relationships
    properties = relationship("Property", back_populates="owner", cascade="all, delete-orphan")
    favorites = relationship("PropertyFavorite", back_populates="user", cascade="all, delete-orphan")
    views = relationship("ViewedProperty", back_populates="user", cascade="all, delete-orphan")
    search_history = relationship("SearchHistory", back_populates="user", cascade="all, delete-orphan")
    messages_sent = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")
    messages_received = relationship("Message", foreign_keys="Message.receiver_id", back_populates="receiver")
    transactions = relationship("Transaction", back_populates="user")
    subscriptions = relationship("UserSubscription", back_populates="user", cascade="all, delete-orphan")
    
    # Add JSON serialization methods
    def __setattr__(self, key, value):
        """Override setattr to handle JSON fields"""
        if key == 'notification_preferences' and not isinstance(value, str) and value is not None:
            value = JSONField.to_json_string(value)
        elif key == 'token_history' and not isinstance(value, str) and value is not None:
            value = JSONField.to_json_string(value)
        super().__setattr__(key, value)
    
    # JSON methods as before
    def get_notification_preferences(self):
        """Get notification preferences as a Python dictionary"""
        if hasattr(self, '_notification_preferences_dict'):
            return self._notification_preferences_dict
            
        try:
            if isinstance(self.notification_preferences, dict):
                result = self.notification_preferences
            else:
                result = json.loads(self.notification_preferences) if self.notification_preferences else {"email": True, "sms": True, "in_app": True}
        except:
            result = {"email": True, "sms": True, "in_app": True}
            
        self._notification_preferences_dict = result
        return result

    def set_notification_preferences(self, value):
        """Set notification preferences, ensuring it's stored as a JSON string"""
        if isinstance(value, dict):
            self.notification_preferences = json.dumps(value)
        else:
            self.notification_preferences = value
        if hasattr(self, '_notification_preferences_dict'):
            delattr(self, '_notification_preferences_dict')

    def get_token_history(self):
        """Get token history as a Python list"""
        if hasattr(self, '_token_history_list'):
            return self._token_history_list
            
        try:
            if isinstance(self.token_history, list):
                result = self.token_history
            else:
                result = json.loads(self.token_history) if self.token_history else []
        except:
            result = []
            
        self._token_history_list = result
        return result

    def set_token_history(self, value):
        """Set token history, ensuring it's stored as a JSON string"""
        if isinstance(value, list):
            self.token_history = json.dumps(value)
        else:
            self.token_history = value
        if hasattr(self, '_token_history_list'):
            delattr(self, '_token_history_list')