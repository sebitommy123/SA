#!/usr/bin/env python3
"""
Debug script to identify performance bottlenecks in group_by_id_types.
"""

import time
import cProfile
from SA.sa.core.object_grouping import group_objects
from sa.core.sa_object import SAObject
from sa.query_language.object_list import ObjectList

def create_test_objects(n):
    """Create n test objects."""
    objects = []
    for i in range(n):
        objects.append(SAObject({
            "__types__": [f"Type{i % 10}"],  # 10 different types
            "__id__": f"obj_{i}",
            "__source__": f"source_{i % 5}",  # 5 different sources
            "value": i
        }))
    return objects

def profile_grouping(n):
    """Profile the grouping operation."""
    print(f"\n=== Profiling {n} objects ===")
    
    objects = create_test_objects(n)
    obj_list = ObjectList(group_objects(objects))
    
    # Profile the grouping operation
    profiler = cProfile.Profile()
    profiler.enable()
    
    start_time = time.time()
    grouped_lists = obj_list.group_by_id_types()
    end_time = time.time()
    
    profiler.disable()
    
    duration = end_time - start_time
    print(f"Time: {duration:.4f}s")
    print(f"Rate: {n/duration:.0f} objects/second")
    print(f"Groups: {len(grouped_lists)}")
    
    # Print top 10 most time-consuming functions
    import pstats
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)
    
    return duration

if __name__ == "__main__":
    # Test different sizes
    sizes = [100, 500, 1000, 2000]
    
    for size in sizes:
        profile_grouping(size)
