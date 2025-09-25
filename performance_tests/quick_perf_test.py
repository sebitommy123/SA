#!/usr/bin/env python3
"""Quick performance test with larger datasets."""

import time
from SA.sa.core.object_grouping import group_objects
from sa.core.sa_object import SAObject
from sa.query_language.object_list import ObjectList

def create_objects(n):
    objects = []
    for i in range(n):
        objects.append(SAObject({
            "__types__": [f"Type{i % 10}"],
            "__id__": f"obj_{i}",
            "__source__": f"source_{i % 5}",
            "value": i
        }))
    return objects

def test_performance(n):
    objects = create_objects(n)
    obj_list = ObjectList(group_objects(objects))
    
    start = time.time()
    grouped = obj_list.group_by_id_types()
    end = time.time()
    
    duration = end - start
    rate = n / duration
    
    print(f"{n:5d} objects: {duration:.4f}s ({rate:6.0f} objects/sec) -> {len(grouped)} groups")

if __name__ == "__main__":
    sizes = [100, 500, 1000, 2000, 5000, 10000]
    for size in sizes:
        test_performance(size)
