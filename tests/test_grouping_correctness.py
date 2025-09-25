#!/usr/bin/env python3
"""
Tests to verify that the group_by_id_types method works correctly
with various grouping scenarios.
"""

import pytest
from sa.core.sa_object import SAObject
from sa.query_language.object_list import ObjectList


class TestGroupingCorrectness:
    """Test class for verifying grouping behavior."""
    
    def test_objects_with_same_id_different_types(self):
        """Test that objects with the same ID but different types get grouped together."""
        # Create objects like in the SAP example
        obj1 = SAObject({
            "__types__": ["type_A"],
            "__id__": "obj_A",
            "__source__": "source_A",
            "name": "Object A1"
        })
        
        obj2 = SAObject({
            "__types__": ["type_A", "type_B"],
            "__id__": "obj_A",
            "__source__": "source_B", 
            "name": "Object A2"
        })
        
        obj3 = SAObject({
            "__types__": ["type_B", "type_C"],
            "__id__": "obj_A",
            "__source__": "source_C",
            "name": "Object A3"
        })
        
        obj_list = ObjectList([obj1, obj2, obj3])
        grouped_lists = obj_list.group_by_id_types()
        
        # Should have exactly one group containing all three objects
        assert len(grouped_lists) == 1, f"Expected 1 group, got {len(grouped_lists)}"
        
        group = grouped_lists[0]
        assert len(group.objects) == 3, f"Expected 3 objects in group, got {len(group.objects)}"
        
        # Verify all objects are present
        group_ids = {obj.id for obj in group.objects}
        assert group_ids == {"obj_A"}, f"Expected all objects to have id 'obj_A', got {group_ids}"
        
        # Verify all sources are present
        group_sources = {obj.source for obj in group.objects}
        assert group_sources == {"source_A", "source_B", "source_C"}, f"Expected all sources, got {group_sources}"
        
        print("✓ Objects with same ID but different types grouped correctly")
    
    def test_objects_with_different_ids_separate_groups(self):
        """Test that objects with different IDs stay in separate groups."""
        obj1 = SAObject({
            "__types__": ["type_A"],
            "__id__": "obj_A",
            "__source__": "source_A",
            "name": "Object A"
        })
        
        obj2 = SAObject({
            "__types__": ["type_A"],  # Same type as obj1
            "__id__": "obj_B",        # Different ID
            "__source__": "source_B",
            "name": "Object B"
        })
        
        obj3 = SAObject({
            "__types__": ["type_C"],
            "__id__": "obj_C",
            "__source__": "source_C",
            "name": "Object C"
        })
        
        obj_list = ObjectList([obj1, obj2, obj3])
        grouped_lists = obj_list.group_by_id_types()
        
        # Should have 3 separate groups since IDs are different
        assert len(grouped_lists) == 3, f"Expected 3 groups, got {len(grouped_lists)}"
        
        # Each group should have exactly one object
        for group in grouped_lists:
            assert len(group.objects) == 1, f"Expected 1 object per group, got {len(group.objects)}"
        
        # Verify all objects are present
        all_grouped_objects = []
        for group in grouped_lists:
            all_grouped_objects.extend(group.objects)
        
        grouped_ids = {obj.id for obj in all_grouped_objects}
        assert grouped_ids == {"obj_A", "obj_B", "obj_C"}, f"Expected all IDs, got {grouped_ids}"
        
        print("✓ Objects with different IDs kept in separate groups")
    
    def test_objects_with_different_ids_stay_separate(self):
        """Test that objects with different IDs stay in separate groups even if they share types."""
        # These objects share types but have different IDs, so they should stay separate
        
        obj1 = SAObject({
            "__types__": ["type_A"],
            "__id__": "obj_1",
            "__source__": "source_1",
            "name": "Object 1"
        })
        
        obj2 = SAObject({
            "__types__": ["type_A", "type_B"],  # Shares type_A with obj1
            "__id__": "obj_2",
            "__source__": "source_2",
            "name": "Object 2"
        })
        
        obj3 = SAObject({
            "__types__": ["type_B", "type_C"],  # Shares type_B with obj2
            "__id__": "obj_3",
            "__source__": "source_3",
            "name": "Object 3"
        })
        
        obj4 = SAObject({
            "__types__": ["type_C", "type_D"],  # Shares type_C with obj3
            "__id__": "obj_4",
            "__source__": "source_4",
            "name": "Object 4"
        })
        
        obj5 = SAObject({
            "__types__": ["type_E"],  # Completely separate
            "__id__": "obj_5",
            "__source__": "source_5",
            "name": "Object 5"
        })
        
        obj_list = ObjectList([obj1, obj2, obj3, obj4, obj5])
        grouped_lists = obj_list.group_by_id_types()
        
        # Should have 5 separate groups since all IDs are different
        assert len(grouped_lists) == 5, f"Expected 5 groups, got {len(grouped_lists)}"
        
        # Each group should have exactly one object
        for group in grouped_lists:
            assert len(group.objects) == 1, f"Expected 1 object per group, got {len(group.objects)}"
        
        # Verify all objects are present
        all_grouped_objects = []
        for group in grouped_lists:
            all_grouped_objects.extend(group.objects)
        
        grouped_ids = {obj.id for obj in all_grouped_objects}
        assert grouped_ids == {"obj_1", "obj_2", "obj_3", "obj_4", "obj_5"}, f"Expected all IDs, got {grouped_ids}"
        
        print("✓ Objects with different IDs stay separate even when sharing types")
    
    def test_empty_object_list(self):
        """Test that empty object list returns empty result."""
        obj_list = ObjectList([])
        grouped_lists = obj_list.group_by_id_types()
        
        assert len(grouped_lists) == 0, f"Expected 0 groups for empty list, got {len(grouped_lists)}"
        print("✓ Empty object list handled correctly")
    
    def test_single_object(self):
        """Test that single object creates single group."""
        obj = SAObject({
            "__types__": ["type_A"],
            "__id__": "obj_A",
            "__source__": "source_A",
            "name": "Single Object"
        })
        
        obj_list = ObjectList([obj])
        grouped_lists = obj_list.group_by_id_types()
        
        assert len(grouped_lists) == 1, f"Expected 1 group for single object, got {len(grouped_lists)}"
        assert len(grouped_lists[0].objects) == 1, f"Expected 1 object in group, got {len(grouped_lists[0].objects)}"
        assert grouped_lists[0].objects[0].id == "obj_A", "Expected correct object in group"
        
        print("✓ Single object handled correctly")
    
    def test_complex_grouping_scenario(self):
        """Test a complex scenario with multiple groups based on ID."""
        # Group 1: obj_A1, obj_A2 (same ID "obj_A")
        # Group 2: obj_B1, obj_B2, obj_B3 (same ID "obj_B") 
        # Group 3: obj_C1 (unique ID "obj_C")
        # Group 4: obj_D1, obj_D2 (same ID "obj_D")
        
        objects = [
            # Group 1 - same ID "obj_A"
            SAObject({
                "__types__": ["type_A"],
                "__id__": "obj_A",
                "__source__": "source_1",
                "name": "A1"
            }),
            SAObject({
                "__types__": ["type_A", "type_B"],
                "__id__": "obj_A",
                "__source__": "source_2",
                "name": "A2"
            }),
            
            # Group 2 - same ID "obj_B"
            SAObject({
                "__types__": ["type_C"],
                "__id__": "obj_B",
                "__source__": "source_3",
                "name": "B1"
            }),
            SAObject({
                "__types__": ["type_C", "type_D"],
                "__id__": "obj_B",
                "__source__": "source_4",
                "name": "B2"
            }),
            SAObject({
                "__types__": ["type_D"],
                "__id__": "obj_B",
                "__source__": "source_5",
                "name": "B3"
            }),
            
            # Group 3 - unique ID "obj_C"
            SAObject({
                "__types__": ["type_E"],
                "__id__": "obj_C",
                "__source__": "source_6",
                "name": "C1"
            }),
            
            # Group 4 - same ID "obj_D"
            SAObject({
                "__types__": ["type_F"],
                "__id__": "obj_D",
                "__source__": "source_7",
                "name": "D1"
            }),
            SAObject({
                "__types__": ["type_F", "type_G"],
                "__id__": "obj_D",
                "__source__": "source_8",
                "name": "D2"
            })
        ]
        
        obj_list = ObjectList(objects)
        grouped_lists = obj_list.group_by_id_types()
        
        # Should have 4 groups
        assert len(grouped_lists) == 4, f"Expected 4 groups, got {len(grouped_lists)}"
        
        # Verify all objects are present
        all_grouped_objects = []
        for group in grouped_lists:
            all_grouped_objects.extend(group.objects)
        
        assert len(all_grouped_objects) == 8, f"Expected 8 total objects, got {len(all_grouped_objects)}"
        
        # Verify grouping by ID
        group_by_id = {}
        for group in grouped_lists:
            for obj in group.objects:
                if obj.id not in group_by_id:
                    group_by_id[obj.id] = []
                group_by_id[obj.id].append(obj)
        
        # obj_A should have 2 objects
        assert len(group_by_id["obj_A"]) == 2, f"Expected 2 obj_A objects, got {len(group_by_id['obj_A'])}"
        
        # obj_B should have 3 objects
        assert len(group_by_id["obj_B"]) == 3, f"Expected 3 obj_B objects, got {len(group_by_id['obj_B'])}"
        
        # obj_C should have 1 object
        assert len(group_by_id["obj_C"]) == 1, f"Expected 1 obj_C object, got {len(group_by_id['obj_C'])}"
        
        # obj_D should have 2 objects
        assert len(group_by_id["obj_D"]) == 2, f"Expected 2 obj_D objects, got {len(group_by_id['obj_D'])}"
        
        print("✓ Complex grouping scenario handled correctly")


def test_grouping_integration():
    """Integration test that runs all grouping scenarios."""
    test_instance = TestGroupingCorrectness()
    
    test_instance.test_objects_with_same_id_different_types()
    test_instance.test_objects_with_different_ids_separate_groups()
    test_instance.test_objects_with_different_ids_stay_separate()
    test_instance.test_empty_object_list()
    test_instance.test_single_object()
    test_instance.test_complex_grouping_scenario()
    
    print("\n🎉 All grouping correctness tests passed!")


if __name__ == "__main__":
    test_grouping_integration()
