from __future__ import annotations
from typing import List, Any
from sa.core.sa_object import SAObject
from sa.core.object_list import ObjectList

def convert_list_of_sa_objects_to_object_list_if_needed(sa_type: 'SAType') -> 'SAType':
    if isinstance(sa_type, list):
        if all(isinstance(obj, SAObject) for obj in sa_type):
            return ObjectList(sa_type)
    return sa_type

def flatten_fully(lst):
    result = []
    for i in lst:
        if isinstance(i, list):
            result.extend(flatten_fully(i))
        else:
            result.append(i)
    return result
