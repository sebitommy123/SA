#!/usr/bin/env python3
"""Test script to debug overlapping objects."""

from mock_provider import create_overlapping_objects, get_provider_data

print("Testing overlapping objects creation...")
print("=" * 50)

# Test 1: Create overlapping objects
overlapping = create_overlapping_objects()
print(f"Created {len(overlapping['overlapping_employees'])} overlapping employees")
print(f"Created {len(overlapping['overlapping_products'])} overlapping products")
print(f"Created {len(overlapping['overlapping_customers'])} overlapping customers")
print(f"Created {len(overlapping['overlapping_documents'])} overlapping documents")

print("\nOverlapping employee IDs:")
for emp in overlapping['overlapping_employees']:
    print(f"  {emp['__id__']} -> {emp['__source__']}")

print("\n" + "=" * 50)

# Test 2: Get provider data
print("Getting provider data...")
try:
    provider_data = get_provider_data()
    
    print("\nProvider object counts:")
    for provider_name, objects in provider_data.items():
        print(f"  {provider_name}: {len(objects)} objects")
        
        # Check for overlapping objects
        overlap_ids = [obj['__id__'] for obj in objects if 'overlap' in obj['__id__']]
        if overlap_ids:
            print(f"    Overlapping IDs: {overlap_ids}")
        else:
            print(f"    No overlapping IDs found")
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc() 