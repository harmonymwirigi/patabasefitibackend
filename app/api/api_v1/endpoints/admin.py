# backend/app/api/api_v1/endpoints/admin.py
# Fixed admin endpoint with correct imports and relationships

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status as http_status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_, desc, text, extract
from datetime import datetime, timedelta
from fastapi.encoders import jsonable_encoder

from app.schemas.user import User, UserCreate, UserUpdate
from app.schemas.verification import Verification
from app.schemas.property import Property

from app import crud, models
from app.api import deps

router = APIRouter()

@router.get("/stats", response_model=Dict[str, Any])
def get_stats(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    Get platform statistics.
    """
    # Count users
    total_users = db.query(models.User).count()
    tenant_users = db.query(models.User).filter(models.User.role == "tenant").count()
    owner_users = db.query(models.User).filter(models.User.role == "owner").count()
    
    # Count properties
    total_properties = db.query(models.Property).count()
    available_properties = db.query(models.Property).filter(
        models.Property.availability_status == "available"
    ).count()
    verified_properties = db.query(models.Property).filter(
        models.Property.verification_status == "verified"
    ).count()
    
    # Count transactions
    total_transactions = db.query(models.Transaction).count()
    completed_transactions = db.query(models.Transaction).filter(
        models.Transaction.status == "completed"
    ).count()
    
    # Calculate revenue (simplified for demo)
    revenue = db.query(func.sum(models.Transaction.amount)).filter(
        models.Transaction.status == "completed"
    ).scalar() or 0
    
    # Active subscriptions
    active_subscriptions = db.query(models.UserSubscription).filter(
        models.UserSubscription.end_date > datetime.utcnow()
    ).count()
    
    return {
        "users": {
            "total": total_users,
            "tenants": tenant_users,
            "owners": owner_users
        },
        "properties": {
            "total": total_properties,
            "available": available_properties,
            "verified": verified_properties
        },
        "transactions": {
            "total": total_transactions,
            "completed": completed_transactions,
            "revenue": float(revenue) if revenue else 0
        },
        "subscriptions": {
            "active": active_subscriptions
        }
    }

@router.get("/users", response_model=List[User])
def get_users(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    user_status: Optional[str] = None,  # Renamed to avoid conflict
    role: Optional[str] = None,
    current_user: models.User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    Retrieve users with optional filtering.
    """
    # Build filter conditions
    filters = []
    if user_status and user_status != "all":
        filters.append(models.User.account_status == user_status)
    if role and role != "all":
        filters.append(models.User.role == role)
    
    # Query with filters
    if filters:
        users = db.query(models.User).filter(and_(*filters)).offset(skip).limit(limit).all()
    else:
        users = crud.user.get_multi(db, skip=skip, limit=limit)
    
    return users

@router.put("/users/{user_id}/status", response_model=User)
def update_user_status(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    user_status: str = Body(..., embed=True),  # Renamed to avoid conflict
    current_user: models.User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    Update user account status.
    """
    user = crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Validate status
    valid_statuses = ["active", "inactive", "suspended"]
    if user_status not in valid_statuses:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
        )
    
    # Update user
    user_in = {"account_status": user_status}
    updated_user = crud.user.update(db, db_obj=user, obj_in=user_in)
    
    return updated_user

@router.put("/users/{user_id}/role", response_model=User)
def update_user_role(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    role: str = Body(..., embed=True),
    current_user: models.User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    Update user role.
    """
    user = crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Validate role
    valid_roles = ["tenant", "owner", "admin"]
    if role not in valid_roles:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}",
        )
    
    # Update user
    user_in = {"role": role}
    updated_user = crud.user.update(db, db_obj=user, obj_in=user_in)
    
    return updated_user

@router.get("/properties/pending-verification", response_model=List[Dict])
def get_pending_verifications(
    *,
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    verification_status: Optional[str] = None,  # Renamed to avoid conflict
    current_user: models.User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    Get properties pending verification.
    """
    try:
        # Build the query with proper relationships
        query = db.query(models.Verification)
        
        # Apply eager loading using the correct relationship name
        query = query.options(
            joinedload(models.Verification.related_property).joinedload(models.Property.owner),
            joinedload(models.Verification.related_property).joinedload(models.Property.images)
        )
        
        # Apply status filter if provided
        if verification_status and verification_status != "all":
            query = query.filter(models.Verification.status == verification_status)
        else:
            # Default to pending if no status specified
            query = query.filter(models.Verification.status == "pending")
        
        # Execute query with pagination
        verifications = query.offset(skip).limit(limit).all()
        
        # Process the results to ensure proper structure
        result = []
        for verification in verifications:
            v_dict = {
                "id": verification.id,
                "property_id": verification.property_id,
                "verification_type": verification.verification_type,
                "requested_at": verification.requested_at,
                "status": verification.status,
                "responder_id": verification.responder_id,
                "expiration": verification.expiration,
                "response_data": verification.get_response_json() if hasattr(verification, "get_response_json") else {},
                "system_decision": verification.get_system_decision_json() if hasattr(verification, "get_system_decision_json") else {}
            }
            
            # Add property information if available (using related_property)
            if hasattr(verification, 'related_property') and verification.related_property:
                prop = verification.related_property
                prop_dict = {
                    "id": prop.id,
                    "title": prop.title,
                    "description": prop.description,
                    "property_type": prop.property_type,
                    "rent_amount": prop.rent_amount,
                    "bedrooms": prop.bedrooms,
                    "bathrooms": prop.bathrooms,
                    "address": prop.address,
                    "city": prop.city,
                    "neighborhood": prop.neighborhood,
                    "verification_status": prop.verification_status,
                    "availability_status": prop.availability_status
                }
                
                # Add owner information if available
                if hasattr(prop, "owner") and prop.owner:
                    prop_dict["owner"] = {
                        "id": prop.owner.id,
                        "full_name": prop.owner.full_name,
                        "email": prop.owner.email
                    }
                
                # Add images if available
                if hasattr(prop, "images") and prop.images:
                    prop_dict["images"] = []
                    for img in prop.images:
                        prop_dict["images"].append({
                            "id": img.id,
                            "path": img.path,
                            "is_primary": img.is_primary,
                            "uploaded_at": img.uploaded_at
                        })
                
                v_dict["property"] = prop_dict
            else:
                # If no related property, try to fetch it manually
                property_obj = db.query(models.Property).filter(
                    models.Property.id == verification.property_id
                ).first()
                
                if property_obj:
                    # Get owner
                    owner = db.query(models.User).filter(
                        models.User.id == property_obj.owner_id
                    ).first()
                    
                    # Get images
                    images = db.query(models.PropertyImage).filter(
                        models.PropertyImage.property_id == property_obj.id
                    ).all()
                    
                    prop_dict = {
                        "id": property_obj.id,
                        "title": property_obj.title,
                        "description": property_obj.description,
                        "property_type": property_obj.property_type,
                        "rent_amount": property_obj.rent_amount,
                        "bedrooms": property_obj.bedrooms,
                        "bathrooms": property_obj.bathrooms,
                        "address": property_obj.address,
                        "city": property_obj.city,
                        "neighborhood": property_obj.neighborhood,
                        "verification_status": property_obj.verification_status,
                        "availability_status": property_obj.availability_status
                    }
                    
                    if owner:
                        prop_dict["owner"] = {
                            "id": owner.id,
                            "full_name": owner.full_name,
                            "email": owner.email
                        }
                    
                    if images:
                        prop_dict["images"] = []
                        for img in images:
                            prop_dict["images"].append({
                                "id": img.id,
                                "path": img.path,
                                "is_primary": img.is_primary,
                                "uploaded_at": img.uploaded_at
                            })
                    
                    v_dict["property"] = prop_dict
            
            result.append(v_dict)
        
        return result
        
    except Exception as e:
        import traceback
        print(f"Error in get_pending_verifications: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting pending verifications: {str(e)}"
        )

@router.put("/properties/{property_id}/verify", response_model=Property)
def verify_property(
    *,
    db: Session = Depends(deps.get_db),
    property_id: int,
    verification_status: str = Body(..., embed=True),  # Renamed to avoid conflict
    notes: str = Body(None, embed=True),
    current_user: models.User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    Verify a property.
    """
    property_obj = crud.property.get(db, id=property_id)
    if not property_obj:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Property not found",
        )
    
    # Validate status
    valid_statuses = ["verified", "rejected", "pending_changes"]
    if verification_status not in valid_statuses:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
        )
    
    # Update property verification status
    property_obj = crud.property.update_verification_status(
        db, property_id=property_id, status=verification_status
    )
    
    # Create verification history entry
    crud.verification.create_history_entry(
        db,
        property_id=property_id,
        status=verification_status,
        verified_by=f"admin_{current_user.id}",
        notes=notes
    )
    
    # Check for active verifications and update
    verifications = crud.verification.get_property_verifications(
        db, property_id=property_id, skip=0, limit=5
    )
    
    for verification in verifications:
        if verification.status == "pending":
            crud.verification.admin_verify(
                db,
                verification_id=verification.id,
                admin_id=current_user.id,
                status=verification_status,
                notes=notes
            )
    
    return property_obj

@router.get("/analytics/properties", response_model=Dict[str, Any])
def get_property_analytics(
    db: Session = Depends(deps.get_db),
    time_range: str = Query("month", enum=["week", "month", "year"]),
    current_user: models.User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    Get property analytics data.
    """
    # Calculate date range filter based on time_range parameter
    now = datetime.utcnow()
    if time_range == "week":
        start_date = now - timedelta(days=7)
    elif time_range == "month":
        start_date = now - timedelta(days=30)
    else:  # year
        start_date = now - timedelta(days=365)
    
    # Get new properties count in the time range
    new_properties_count = db.query(models.Property).\
        filter(models.Property.created_at >= start_date).count()
    
    # Get popular neighborhoods
    popular_neighborhoods = db.query(
        models.Property.neighborhood,
        func.count(models.Property.id).label("count")
    ).\
    filter(models.Property.neighborhood != None).\
    group_by(models.Property.neighborhood).\
    order_by(desc("count")).\
    limit(5).\
    all()
    
    neighborhoods_data = [
        {"name": n.neighborhood, "count": n.count} 
        for n in popular_neighborhoods
    ]
    
    # Get property types distribution
    property_types = db.query(
        models.Property.property_type,
        func.count(models.Property.id).label("count")
    ).\
    group_by(models.Property.property_type).\
    order_by(desc("count")).\
    all()
    
    property_types_data = [
        {"type": pt.property_type.capitalize(), "count": pt.count} 
        for pt in property_types
    ]
    
    return {
        "newPropertiesCount": new_properties_count,
        "popularNeighborhoods": neighborhoods_data,
        "propertyTypes": property_types_data
    }

@router.get("/analytics/users", response_model=Dict[str, Any])
def get_user_analytics(
    db: Session = Depends(deps.get_db),
    time_range: str = Query("month", enum=["week", "month", "year"]),
    current_user: models.User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    Get user analytics data.
    """
    # Date filters based on time range
    now = datetime.utcnow()
    if time_range == "week":
        start_date = now - timedelta(days=7)
        date_format = "%Y-%m-%d"
        date_trunc = "day"
    elif time_range == "month":
        start_date = now - timedelta(days=30)
        date_format = "%Y-%W"
        date_trunc = "week"
    else:  # year
        start_date = now - timedelta(days=365)
        date_format = "%Y-%m"
        date_trunc = "month"
    
    # Count active users (logged in within the past 30 days)
    active_users = db.query(models.User).\
        filter(models.User.last_login >= now - timedelta(days=30)).\
        count()
    
    # Simplified registration trend (fallback data)
    registration_trend = []
    if time_range == "week":
        registration_trend = [
            {"date": (now - timedelta(days=i)).strftime("%Y-%m-%d"), "tenants": 5+i, "owners": 2+i}
            for i in range(7, 0, -1)
        ]
    elif time_range == "month":
        registration_trend = [
            {"date": f"2025-{20+i}", "tenants": 20+i*5, "owners": 8+i*2}
            for i in range(4)
        ]
    else:  # year
        registration_trend = [
            {"date": f"2025-{1+i:02d}", "tenants": 30+i*5, "owners": 10+i*2}
            for i in range(5)
        ]
    
    # Get users by role
    users_by_role = db.query(
        models.User.role,
        func.count(models.User.id).label("count")
    ).\
    group_by(models.User.role).\
    all()
    
    users_by_role_data = [
        {"role": role.role.capitalize(), "count": role.count} 
        for role in users_by_role
    ]
    
    return {
        "activeUsers": active_users,
        "registrationTrend": registration_trend,
        "usersByRole": users_by_role_data
    }

@router.get("/analytics/revenue", response_model=Dict[str, Any])
def get_revenue_analytics(
    db: Session = Depends(deps.get_db),
    time_range: str = Query("month", enum=["week", "month", "year"]),
    current_user: models.User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    Get revenue analytics data.
    """
    # Simplified revenue data (fallback)
    revenue_trend = []
    if time_range == "week":
        revenue_trend = [
            {"date": (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d"), "amount": 10000+i*1000}
            for i in range(7, 0, -1)
        ]
    elif time_range == "month":
        revenue_trend = [
            {"date": f"2025-{20+i}", "amount": 40000+i*5000}
            for i in range(4)
        ]
    else:  # year
        revenue_trend = [
            {"date": f"2025-{1+i:02d}", "amount": 90000+i*15000}
            for i in range(5)
        ]
    
    # Revenue by source (sample data)
    revenue_by_source = [
        {"source": "Token Purchases", "amount": 285000},
        {"source": "Subscriptions", "amount": 175000},
        {"source": "Featured Listings", "amount": 45000},
        {"source": "Other", "amount": 12000}
    ]
    
    return {
        "revenueTrend": revenue_trend,
        "revenueBySource": revenue_by_source
    }