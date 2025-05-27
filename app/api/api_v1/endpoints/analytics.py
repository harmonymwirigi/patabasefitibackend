# backend/app/api/api_v1/endpoints/analytics.py
# Analytics endpoints for property owners and admins

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from datetime import datetime, timedelta

from app import crud, models
from app.api import deps

router = APIRouter()

@router.get("/owner", response_model=Dict[str, Any])
def get_owner_analytics(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
    time_range: str = Query("30", description="Time range in days"),
    property_type: Optional[str] = Query(None, description="Filter by property type")
) -> Any:
    """
    Get comprehensive analytics for property owner.
    """
    try:
        # Calculate date range
        days = int(time_range)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Base query for owner's properties
        properties_query = db.query(models.Property).filter(
            models.Property.owner_id == current_user.id
        )
        
        # Apply property type filter if specified
        if property_type and property_type != "all":
            properties_query = properties_query.filter(
                models.Property.property_type == property_type
            )
        
        # Get all properties
        all_properties = properties_query.all()
        
        # Basic property counts
        total_properties = len(all_properties)
        available_properties = len([p for p in all_properties if p.availability_status == "available"])
        rented_properties = len([p for p in all_properties if p.availability_status == "rented"])
        verified_properties = len([p for p in all_properties if p.verification_status == "verified"])
        
        # Count pending verifications
        pending_verifications = db.query(models.Verification).join(
            models.Property
        ).filter(
            models.Property.owner_id == current_user.id,
            models.Verification.status == "pending"
        ).count()
        
        # Calculate engagement metrics
        total_views = 0
        total_favorites = 0
        total_contacts = 0
        
        for property_obj in all_properties:
            # Get engagement metrics from JSON field
            metrics = property_obj.get_engagement_metrics_json()
            total_views += metrics.get("view_count", 0)
            total_favorites += metrics.get("favorite_count", 0)
            total_contacts += metrics.get("contact_count", 0)
        
        # Calculate average rent
        if total_properties > 0:
            total_rent = sum(p.rent_amount for p in all_properties)
            average_rent = total_rent / total_properties
        else:
            average_rent = 0
        
        # Find top performing property
        top_performing_property = None
        if all_properties:
            max_engagement = 0
            for property_obj in all_properties:
                metrics = property_obj.get_engagement_metrics_json()
                total_engagement = (
                    metrics.get("view_count", 0) + 
                    metrics.get("favorite_count", 0) * 2 + 
                    metrics.get("contact_count", 0) * 3
                )
                if total_engagement > max_engagement:
                    max_engagement = total_engagement
                    top_performing_property = {
                        "id": property_obj.id,
                        "title": property_obj.title,
                        "views": metrics.get("view_count", 0),
                        "favorites": metrics.get("favorite_count", 0),
                        "contacts": metrics.get("contact_count", 0)
                    }
        
        # Generate recent activity (mock data for now)
        recent_activity = []
        for property_obj in all_properties[-5:]:  # Last 5 properties
            metrics = property_obj.get_engagement_metrics_json()
            if metrics.get("view_count", 0) > 0:
                recent_activity.append({
                    "type": "view",
                    "description": f"Property viewed {metrics.get('view_count', 0)} times",
                    "propertyTitle": property_obj.title,
                    "timeAgo": "2 hours ago",
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        # Generate views over time (mock data with trend)
        views_over_time = []
        for i in range(min(days, 30)):  # Show up to 30 days
            date = datetime.utcnow() - timedelta(days=i)
            # Mock trending data
            base_views = max(0, total_views // 30 + (i % 7) * 2)
            views_over_time.append({
                "date": date.strftime("%Y-%m-%d"),
                "views": base_views,
                "favorites": max(0, base_views // 4),
                "contacts": max(0, base_views // 8)
            })
        
        views_over_time.reverse()  # Chronological order
        
        # Engagement metrics summary
        engagement_metrics = {
            "views": total_views,
            "favorites": total_favorites,
            "contacts": total_contacts
        }
        
        return {
            "totalProperties": total_properties,
            "availableProperties": available_properties,
            "rentedProperties": rented_properties,
            "verifiedProperties": verified_properties,
            "pendingVerifications": pending_verifications,
            "totalViews": total_views,
            "totalFavorites": total_favorites,
            "totalContacts": total_contacts,
            "monthlyRevenue": 0,  # To be implemented with actual revenue tracking
            "averageRent": round(average_rent, 2),
            "topPerformingProperty": top_performing_property,
            "recentActivity": recent_activity,
            "viewsOverTime": views_over_time,
            "engagementMetrics": engagement_metrics
        }
        
    except Exception as e:
        print(f"Error in get_owner_analytics: {str(e)}")
        # Return empty analytics on error
        return {
            "totalProperties": 0,
            "availableProperties": 0,
            "rentedProperties": 0,
            "verifiedProperties": 0,
            "pendingVerifications": 0,
            "totalViews": 0,
            "totalFavorites": 0,
            "totalContacts": 0,
            "monthlyRevenue": 0,
            "averageRent": 0,
            "topPerformingProperty": None,
            "recentActivity": [],
            "viewsOverTime": [],
            "engagementMetrics": {
                "views": 0,
                "favorites": 0,
                "contacts": 0
            }
        }

@router.get("/property/{property_id}", response_model=Dict[str, Any])
def get_property_insights(
    *,
    db: Session = Depends(deps.get_db),
    property_id: int,
    current_user: models.User = Depends(deps.get_current_user),
    time_range: str = Query("30", description="Time range in days")
) -> Any:
    """
    Get detailed insights for a specific property.
    """
    try:
        # Get the property and verify ownership
        property_obj = db.query(models.Property).filter(
            models.Property.id == property_id,
            models.Property.owner_id == current_user.id
        ).first()
        
        if not property_obj:
            return {"error": "Property not found or access denied"}
        
        # Get engagement metrics
        metrics = property_obj.get_engagement_metrics_json()
        
        # Calculate performance score (0-100)
        performance_score = min(100, (
            metrics.get("view_count", 0) * 1 +
            metrics.get("favorite_count", 0) * 3 +
            metrics.get("contact_count", 0) * 5
        ))
        
        # Calculate days since last verified
        days_since_verification = None
        if property_obj.last_verified:
            days_since_verification = (datetime.utcnow() - property_obj.last_verified).days
        
        return {
            "propertyId": property_obj.id,
            "title": property_obj.title,
            "performanceScore": performance_score,
            "engagementMetrics": metrics,
            "verificationStatus": property_obj.verification_status,
            "daysSinceVerification": days_since_verification,
            "availabilityStatus": property_obj.availability_status,
            "rentAmount": property_obj.rent_amount,
            "viewsThisMonth": metrics.get("view_count", 0),
            "favoritesThisMonth": metrics.get("favorite_count", 0),
            "contactsThisMonth": metrics.get("contact_count", 0),
            "suggestions": [
                "Add more high-quality photos to increase views",
                "Update property description with detailed amenities",
                "Verify property status regularly for better visibility"
            ]
        }
        
    except Exception as e:
        print(f"Error in get_property_insights: {str(e)}")
        return {"error": "Failed to load property insights"}

@router.get("/market", response_model=Dict[str, Any])
def get_market_analytics(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
    city: Optional[str] = Query(None, description="Filter by city"),
    property_type: Optional[str] = Query(None, description="Filter by property type")
) -> Any:
    """
    Get market analytics for comparative analysis.
    """
    try:
        # Base query for market data
        market_query = db.query(models.Property).filter(
            models.Property.verification_status == "verified",
            models.Property.availability_status == "available"
        )
        
        # Apply filters
        if city:
            market_query = market_query.filter(models.Property.city == city)
        if property_type and property_type != "all":
            market_query = market_query.filter(models.Property.property_type == property_type)
        
        # Get market properties
        market_properties = market_query.all()
        
        if not market_properties:
            return {
                "totalProperties": 0,
                "averageRent": 0,
                "medianRent": 0,
                "rentRange": {"min": 0, "max": 0},
                "propertyTypes": [],
                "topCities": [],
                "marketTrends": []
            }
        
        # Calculate market statistics
        rent_amounts = [p.rent_amount for p in market_properties]
        average_rent = sum(rent_amounts) / len(rent_amounts)
        median_rent = sorted(rent_amounts)[len(rent_amounts) // 2]
        
        # Property type distribution
        property_types = {}
        for prop in market_properties:
            prop_type = prop.property_type
            if prop_type not in property_types:
                property_types[prop_type] = {"count": 0, "averageRent": 0}
            property_types[prop_type]["count"] += 1
        
        # Calculate average rent per type
        for prop_type in property_types:
            type_properties = [p for p in market_properties if p.property_type == prop_type]
            if type_properties:
                property_types[prop_type]["averageRent"] = sum(p.rent_amount for p in type_properties) / len(type_properties)
        
        # Top cities by property count
        city_counts = {}
        for prop in market_properties:
            city_counts[prop.city] = city_counts.get(prop.city, 0) + 1
        
        top_cities = [
            {"city": city, "count": count}
            for city, count in sorted(city_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        
        return {
            "totalProperties": len(market_properties),
            "averageRent": round(average_rent, 2),
            "medianRent": round(median_rent, 2),
            "rentRange": {
                "min": min(rent_amounts),
                "max": max(rent_amounts)
            },
            "propertyTypes": [
                {"type": ptype, "count": data["count"], "averageRent": round(data["averageRent"], 2)}
                for ptype, data in property_types.items()
            ],
            "topCities": top_cities,
            "marketTrends": [
                {"month": "2025-01", "averageRent": average_rent * 0.95},
                {"month": "2025-02", "averageRent": average_rent * 0.97},
                {"month": "2025-03", "averageRent": average_rent * 0.99},
                {"month": "2025-04", "averageRent": average_rent * 1.01},
                {"month": "2025-05", "averageRent": average_rent}
            ]
        }
        
    except Exception as e:
        print(f"Error in get_market_analytics: {str(e)}")
        return {"error": "Failed to load market analytics"}

@router.get("/competitor/{property_id}", response_model=Dict[str, Any])
def get_competitor_analysis(
    *,
    db: Session = Depends(deps.get_db),
    property_id: int,
    current_user: models.User = Depends(deps.get_current_user)
) -> Any:
    """
    Get competitor analysis for a specific property.
    """
    try:
        # Get the target property
        target_property = db.query(models.Property).filter(
            models.Property.id == property_id,
            models.Property.owner_id == current_user.id
        ).first()
        
        if not target_property:
            return {"error": "Property not found or access denied"}
        
        # Find similar properties (same city, similar price range, same type)
        price_range = target_property.rent_amount * 0.2  # 20% price range
        
        competitors = db.query(models.Property).filter(
            models.Property.id != property_id,
            models.Property.city == target_property.city,
            models.Property.property_type == target_property.property_type,
            models.Property.rent_amount.between(
                target_property.rent_amount - price_range,
                target_property.rent_amount + price_range
            ),
            models.Property.verification_status == "verified",
            models.Property.availability_status == "available"
        ).limit(5).all()
        
        # Analyze competitors
        competitor_analysis = []
        for comp in competitors:
            comp_metrics = comp.get_engagement_metrics_json()
            competitor_analysis.append({
                "id": comp.id,
                "title": comp.title,
                "rentAmount": comp.rent_amount,
                "bedrooms": comp.bedrooms,
                "bathrooms": comp.bathrooms,
                "address": comp.address,
                "views": comp_metrics.get("view_count", 0),
                "favorites": comp_metrics.get("favorite_count", 0),
                "contacts": comp_metrics.get("contact_count", 0),
                "verificationStatus": comp.verification_status
            })
        
        # Calculate target property metrics
        target_metrics = target_property.get_engagement_metrics_json()
        
        # Generate recommendations
        recommendations = []
        if competitors:
            avg_competitor_views = sum(c["views"] for c in competitor_analysis) / len(competitor_analysis)
            if target_metrics.get("view_count", 0) < avg_competitor_views:
                recommendations.append("Your property has fewer views than similar listings. Consider updating photos and description.")
            
            avg_competitor_rent = sum(c["rentAmount"] for c in competitor_analysis) / len(competitor_analysis)
            if target_property.rent_amount > avg_competitor_rent * 1.1:
                recommendations.append("Your rent is above market average. Consider adjusting pricing for better competitiveness.")
        
        if not recommendations:
            recommendations.append("Your property is performing well compared to similar listings!")
        
        return {
            "targetProperty": {
                "id": target_property.id,
                "title": target_property.title,
                "rentAmount": target_property.rent_amount,
                "views": target_metrics.get("view_count", 0),
                "favorites": target_metrics.get("favorite_count", 0),
                "contacts": target_metrics.get("contact_count", 0)
            },
            "competitors": competitor_analysis,
            "marketPosition": {
                "priceRank": len([c for c in competitor_analysis if c["rentAmount"] < target_property.rent_amount]) + 1,
                "viewsRank": len([c for c in competitor_analysis if c["views"] > target_metrics.get("view_count", 0)]) + 1,
                "totalCompetitors": len(competitor_analysis)
            },
            "recommendations": recommendations
        }
        
    except Exception as e:
        print(f"Error in get_competitor_analysis: {str(e)}")
        return {"error": "Failed to load competitor analysis"}