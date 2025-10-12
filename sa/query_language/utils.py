from __future__ import annotations
from typing import List, Any
from sa.core.sa_object import SAObject
from sa.core.object_list import ObjectList

def flatten_fully(lst):
    result = []
    for i in lst:
        if isinstance(i, list):
            result.extend(flatten_fully(i))
        else:
            result.append(i)
    return result
