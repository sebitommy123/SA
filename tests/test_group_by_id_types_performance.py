#!/usr/bin/env python3
"""
Performance tests for the group_by_id_types method.

This test validates that the optimized group_by_id_types method performs
efficiently with large datasets (~1000 items) and maintains correct behavior.
"""

import time
import pytest
from sa.core.sa_object import SAObject
from sa.query_language.object_list import ObjectList


class TestGroupByIdTypesPerformance:
    """Test class for group_by_id_types performance validation."""
    
    def create_large_dataset(self, num_objects: int = 1000) -> list[SAObject]:
        """Create a large dataset for performance testing."""
        objects = []
        
        # Create objects with various id_types to test different grouping scenarios
        for i in range(num_objects):
            # Create objects with overlapping id_types to test worst-case scenario
            types = []
            if i % 2 == 0:
                types.append("TypeA")
            if i % 3 == 0:
                types.append("TypeB") 
            if i % 5 == 0:
                types.append("TypeC")
            if i % 7 == 0:
                types.append("TypeD")
            if i % 11 == 0:
                types.append("TypeE")
            
            # Ensure every object has at least one type
            if not types:
                types = ["TypeF"]
            
            # Create some objects with the same ID but different types to test grouping
            if i % 13 == 0 and i > 0:
                # Use the same ID as a previous object to create grouping opportunities
                base_id = f"shared_id_{i // 13}"
            else:
                base_id = f"obj_{i}"
                
            objects.append(SAObject({
                "__types__": types,
                "__id__": base_id,
                "__source__": f"source_{i % 20}",  # 20 different sources
                "value": i,
                "name": f"Object_{i}"
            }))
        
        return objects
    
    def test_performance_with_1000_objects(self):
        """Test that group_by_id_types performs well with 1000 objects."""
        print("\n=== Performance Test: 1000 Objects ===")
        
        # Create dataset
        objects = self.create_large_dataset(1000)
        obj_list = ObjectList(objects)
        
        print(f"Created {len(objects)} objects")
        
        # Time the grouping operation
        start_time = time.time()
        grouped_lists = obj_list.group_by_id_types()
        end_time = time.time()
        
        duration = end_time - start_time
        
        print(f"Grouped {len(objects)} objects into {len(grouped_lists)} groups")
        print(f"Execution time: {duration:.4f} seconds")
        
        # Performance assertion - should complete within reasonable time
        # With optimizations, 1000 objects should complete very quickly
        max_acceptable_time = 0.1  # 0.1 seconds for 1000 objects
        assert duration < max_acceptable_time, (
            f"Grouping took {duration:.4f}s, expected < {max_acceptable_time}s. "
            f"This suggests the optimization may not be working properly."
        )
        
        # Verify correctness
        self._verify_grouping_correctness(objects, grouped_lists)
        
        print("✓ Performance test passed!")
    
    def test_performance_with_5000_objects(self):
        """Test performance with an even larger dataset."""
        print("\n=== Performance Test: 5000 Objects ===")
        
        # Create larger dataset
        objects = self.create_large_dataset(5000)
        obj_list = ObjectList(objects)
        
        print(f"Created {len(objects)} objects")
        
        # Time the grouping operation
        start_time = time.time()
        grouped_lists = obj_list.group_by_id_types()
        end_time = time.time()
        
        duration = end_time - start_time
        
        print(f"Grouped {len(objects)} objects into {len(grouped_lists)} groups")
        print(f"Execution time: {duration:.4f} seconds")
        
        # More generous threshold for larger dataset
        max_acceptable_time = 1.0  # 1 second for 5000 objects
        assert duration < max_acceptable_time, (
            f"Grouping took {duration:.4f}s, expected < {max_acceptable_time}s. "
            f"This suggests the optimization may not be working properly."
        )
        
        # Verify correctness
        self._verify_grouping_correctness(objects, grouped_lists)
        
        print("✓ Large dataset performance test passed!")
    
    def test_grouping_correctness_with_overlapping_ids(self):
        """Test that grouping works correctly with objects that share IDs."""
        print("\n=== Correctness Test: Overlapping IDs ===")
        
        # Create objects with shared IDs to test grouping behavior
        objects = [
            # Group 1: Two objects with same ID, sharing one type
            SAObject({
                "__types__": ["User", "Person"],
                "__id__": "user1",
                "__source__": "db1",
                "name": "Alice"
            }),
            SAObject({
                "__types__": ["User"],
                "__id__": "user1",
                "__source__": "db2",  # Different source
                "name": "Alice"
            }),
            # Group 2: Two objects with same ID, sharing one type
            SAObject({
                "__types__": ["Admin", "Manager"],
                "__id__": "user2",
                "__source__": "db1",
                "name": "Bob"
            }),
            SAObject({
                "__types__": ["Manager"],
                "__id__": "user2",
                "__source__": "db3",  # Different source
                "name": "Bob"
            }),
            # Group 3: Single object with unique ID
            SAObject({
                "__types__": ["Guest"],
                "__id__": "user3",
                "__source__": "db1",
                "name": "Charlie"
            })
        ]
        
        obj_list = ObjectList(objects)
        grouped_lists = obj_list.group_by_id_types()
        
        print(f"Grouped {len(objects)} objects into {len(grouped_lists)} groups")
        
        # Should have 3 groups: user1, user2, user3
        assert len(grouped_lists) == 3, f"Expected 3 groups, got {len(grouped_lists)}"
        
        # Verify each group contains the correct objects
        group_ids = [set(obj.id for obj in group.objects) for group in grouped_lists]
        expected_groups = [{"user1"}, {"user2"}, {"user3"}]
        
        for expected_group in expected_groups:
            assert expected_group in group_ids, f"Expected group {expected_group} not found in {group_ids}"
        
        print("✓ Correctness test passed!")
    
    def test_memory_efficiency(self):
        """Test that the algorithm doesn't use excessive memory."""
        print("\n=== Memory Efficiency Test ===")
        
        # Create a moderately large dataset
        objects = self.create_large_dataset(2000)
        obj_list = ObjectList(objects)
        
        # Measure memory usage before and after (rough estimate)
        import sys
        
        # Get initial memory usage
        initial_memory = sys.getsizeof(obj_list.objects)
        
        # Perform grouping
        start_time = time.time()
        grouped_lists = obj_list.group_by_id_types()
        end_time = time.time()
        
        # Get final memory usage
        final_memory = sys.getsizeof(grouped_lists) + sum(sys.getsizeof(group.objects) for group in grouped_lists)
        
        duration = end_time - start_time
        
        print(f"Initial memory: ~{initial_memory / 1024:.1f} KB")
        print(f"Final memory: ~{final_memory / 1024:.1f} KB")
        print(f"Memory overhead: ~{(final_memory - initial_memory) / 1024:.1f} KB")
        print(f"Execution time: {duration:.4f} seconds")
        
        # Verify correctness
        self._verify_grouping_correctness(objects, grouped_lists)
        
        # Memory usage should be reasonable (not more than 15x the input size)
        # Note: Python's sys.getsizeof doesn't account for all nested objects,
        # so we use a more generous threshold
        memory_ratio = final_memory / initial_memory
        assert memory_ratio < 15.0, f"Memory usage ratio {memory_ratio:.1f}x is too high"
        
        print("✓ Memory efficiency test passed!")
    
    def _verify_grouping_correctness(self, original_objects: list[SAObject], grouped_lists: list[ObjectList]):
        """Verify that grouping is correct."""
        # All original objects should be included exactly once
        all_grouped_objects = []
        for group in grouped_lists:
            all_grouped_objects.extend(group.objects)
        
        original_ids = {obj.id for obj in original_objects}
        grouped_ids = {obj.id for obj in all_grouped_objects}
        
        assert original_ids == grouped_ids, "All objects should be included in exactly one group"
        
        # Objects in the same group should share at least one (id, type) combination
        for group in grouped_lists:
            if len(group.objects) > 1:
                # Get all id_types for objects in this group
                group_id_types = set()
                for obj in group.objects:
                    group_id_types.update(obj.id_types)
                
                # Check that there's at least one shared id_type
                shared_id_types = set.intersection(*[obj.id_types for obj in group.objects])
                assert len(shared_id_types) > 0, f"Objects in group should share at least one (id, type) combination: {[obj.id for obj in group.objects]}"
        
        print(f"✓ Correctness verified: {len(original_objects)} objects grouped into {len(grouped_lists)} groups")


def test_performance_benchmark():
    """Standalone performance benchmark test."""
    test_instance = TestGroupByIdTypesPerformance()
    
    # Run the main performance test
    test_instance.test_performance_with_1000_objects()
    
    # Run correctness test
    test_instance.test_grouping_correctness_with_overlapping_ids()
    
    print("\n🎉 All performance tests completed successfully!")


if __name__ == "__main__":
    # Run the benchmark when executed directly
    test_performance_benchmark()
