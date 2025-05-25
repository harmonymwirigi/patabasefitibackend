# File: debug_property_location.py
# Debug script to check property location data and fix issues

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine
from app import models
import json

def debug_property_locations():
    """Debug property location data"""
    db = SessionLocal()
    
    try:
        print("=== Property Location Debug Report ===\n")
        
        # Get all properties
        properties = db.query(models.Property).all()
        print(f"Total properties in database: {len(properties)}\n")
        
        # Check location data
        with_coords = 0
        without_coords = 0
        invalid_coords = 0
        
        print("Property Location Analysis:")
        print("-" * 50)
        
        for prop in properties:
            print(f"Property ID {prop.id}: {prop.title}")
            print(f"  Address: {prop.address}, {prop.city}")
            print(f"  Latitude: {prop.latitude}")
            print(f"  Longitude: {prop.longitude}")
            
            # Check coordinate status
            if prop.latitude is not None and prop.longitude is not None:
                try:
                    lat, lng = float(prop.latitude), float(prop.longitude)
                    
                    # Check if within Kenya bounds
                    if -5.0 <= lat <= 5.0 and 33.5 <= lng <= 42.0:
                        with_coords += 1
                        print(f"  Status: ✓ Valid coordinates")
                    else:
                        invalid_coords += 1
                        print(f"  Status: ⚠️  Coordinates outside Kenya bounds")
                        
                except (ValueError, TypeError):
                    invalid_coords += 1
                    print(f"  Status: ❌ Invalid coordinate format")
            else:
                without_coords += 1
                print(f"  Status: ❌ Missing coordinates")
            
            # Check JSON fields
            try:
                if hasattr(prop, 'amenities') and prop.amenities:
                    if isinstance(prop.amenities, str):
                        amenities = json.loads(prop.amenities)
                        print(f"  Amenities: {len(amenities)} items")
                    else:
                        print(f"  Amenities: {len(prop.amenities)} items")
                else:
                    print(f"  Amenities: None")
            except Exception as e:
                print(f"  Amenities: ❌ JSON parsing error: {e}")
            
            print()
        
        print("Summary:")
        print(f"Properties with valid coordinates: {with_coords}")
        print(f"Properties without coordinates: {without_coords}")
        print(f"Properties with invalid coordinates: {invalid_coords}")
        print()
        
        # Check for properties that might need geocoding
        if without_coords > 0:
            print("Properties that need geocoding:")
            props_without_coords = db.query(models.Property).filter(
                models.Property.latitude.is_(None) | 
                models.Property.longitude.is_(None)
            ).all()
            
            for prop in props_without_coords:
                print(f"  - Property {prop.id}: {prop.address}, {prop.city}")
        
    except Exception as e:
        print(f"Error during debug: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def fix_property_json_fields():
    """Fix any malformed JSON fields in properties"""
    db = SessionLocal()
    
    try:
        print("=== Fixing Property JSON Fields ===\n")
        
        properties = db.query(models.Property).all()
        fixed_count = 0
        
        for prop in properties:
            needs_update = False
            
            # Fix amenities field
            if prop.amenities:
                try:
                    if isinstance(prop.amenities, str):
                        json.loads(prop.amenities)  # Test if valid JSON
                except json.JSONDecodeError:
                    print(f"Fixing amenities for property {prop.id}")
                    prop.amenities = '[]'
                    needs_update = True
            else:
                prop.amenities = '[]'
                needs_update = True
            
            # Fix engagement_metrics field
            if prop.engagement_metrics:
                try:
                    if isinstance(prop.engagement_metrics, str):
                        json.loads(prop.engagement_metrics)
                except json.JSONDecodeError:
                    print(f"Fixing engagement_metrics for property {prop.id}")
                    prop.engagement_metrics = '{"view_count": 0, "favorite_count": 0, "contact_count": 0}'
                    needs_update = True
            else:
                prop.engagement_metrics = '{"view_count": 0, "favorite_count": 0, "contact_count": 0}'
                needs_update = True
            
            # Fix other JSON fields
            json_fields = {
                'lease_terms': '{}',
                'auto_verification_settings': '{"enabled": true, "frequency_days": 7}',
                'featured_status': '{"is_featured": false}'
            }
            
            for field, default_value in json_fields.items():
                field_value = getattr(prop, field, None)
                if field_value:
                    try:
                        if isinstance(field_value, str):
                            json.loads(field_value)
                    except json.JSONDecodeError:
                        print(f"Fixing {field} for property {prop.id}")
                        setattr(prop, field, default_value)
                        needs_update = True
                else:
                    setattr(prop, field, default_value)
                    needs_update = True
            
            if needs_update:
                db.add(prop)
                fixed_count += 1
        
        if fixed_count > 0:
            db.commit()
            print(f"Fixed {fixed_count} properties")
        else:
            print("No properties needed fixing")
            
    except Exception as e:
        db.rollback()
        print(f"Error fixing properties: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def test_property_retrieval():
    """Test retrieving properties to see where errors occur"""
    db = SessionLocal()
    
    try:
        print("=== Testing Property Retrieval ===\n")
        
        properties = db.query(models.Property).all()
        
        for prop in properties:
            try:
                print(f"Testing property {prop.id}: {prop.title}")
                
                # Test coordinate access
                lat = prop.latitude
                lng = prop.longitude
                print(f"  Coordinates: {lat}, {lng}")
                
                # Test JSON field access
                if hasattr(prop, 'get_amenities_json'):
                    amenities = prop.get_amenities_json()
                    print(f"  Amenities (method): {len(amenities)} items")
                else:
                    # Manual parsing
                    if prop.amenities:
                        try:
                            amenities = json.loads(prop.amenities) if isinstance(prop.amenities, str) else prop.amenities
                            print(f"  Amenities (manual): {len(amenities)} items")
                        except:
                            print(f"  Amenities: ❌ Parsing failed")
                    else:
                        print(f"  Amenities: None")
                
                # Test images
                images = db.query(models.PropertyImage).filter(
                    models.PropertyImage.property_id == prop.id
                ).all()
                print(f"  Images: {len(images)} found")
                
                print(f"  Status: ✓ Retrieved successfully")
                
            except Exception as e:
                print(f"  Status: ❌ Error: {e}")
                import traceback
                traceback.print_exc()
            
            print()
            
    except Exception as e:
        print(f"Error during testing: {e}")
    finally:
        db.close()

def check_context_issues():
    """Check for potential React context issues in the data"""
    db = SessionLocal()
    
    try:
        print("=== Checking for Data Issues that Could Cause React Errors ===\n")
        
        # Check for properties with location data that might cause rendering issues
        properties = db.query(models.Property).all()
        
        issues_found = 0
        
        for prop in properties:
            property_issues = []
            
            # Check for null/undefined values that might cause React issues
            if prop.title is None or prop.title == "":
                property_issues.append("Missing title")
            
            if prop.address is None or prop.address == "":
                property_issues.append("Missing address")
            
            if prop.city is None or prop.city == "":
                property_issues.append("Missing city")
            
            # Check for invalid coordinate types
            if prop.latitude is not None:
                try:
                    float(prop.latitude)
                except:
                    property_issues.append("Invalid latitude type")
            
            if prop.longitude is not None:
                try:
                    float(prop.longitude)
                except:
                    property_issues.append("Invalid longitude type")
            
            # Check JSON fields for malformed data
            json_fields = ['amenities', 'lease_terms', 'engagement_metrics', 'auto_verification_settings', 'featured_status']
            for field in json_fields:
                field_value = getattr(prop, field, None)
                if field_value and isinstance(field_value, str):
                    try:
                        json.loads(field_value)
                    except json.JSONDecodeError:
                        property_issues.append(f"Malformed JSON in {field}")
            
            if property_issues:
                issues_found += 1
                print(f"Property {prop.id} has issues:")
                for issue in property_issues:
                    print(f"  - {issue}")
                print()
        
        if issues_found == 0:
            print("No data issues found that would cause React context errors.")
        else:
            print(f"Found {issues_found} properties with potential issues.")
            
    except Exception as e:
        print(f"Error during checking: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("Property Location Debug Tool")
    print("===========================\n")
    
    while True:
        print("Choose an option:")
        print("1. Debug property locations")
        print("2. Fix JSON fields")
        print("3. Test property retrieval")
        print("4. Check for context issues")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == "1":
            debug_property_locations()
        elif choice == "2":
            fix_property_json_fields()
        elif choice == "3":
            test_property_retrieval()
        elif choice == "4":
            check_context_issues()
        elif choice == "5":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")
        
        print("\n" + "="*50 + "\n")