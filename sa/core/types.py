"""
Shared type definitions for the SA framework.
This module breaks circular dependencies by centralizing type definitions.
"""

from __future__ import annotations
from typing import Union

from sa.core.sa_types import SATypeCustom

# Core type definitions
SATypePrimitive = Union[str, int, bool, float, None, list['SATypePrimitive'], dict[str, 'SATypePrimitive']]

# Forward reference for the main type union
SAType = Union[SATypeCustom, SATypePrimitive]

def is_valid_sa_type_primitive(t: any) -> bool:
    if isinstance(t, str) or isinstance(t, int) or isinstance(t, bool) or isinstance(t, float):
        return True
    if isinstance(t, list):
        return all(is_valid_sa_type(i) for i in t)
    if isinstance(t, dict):
        return all(is_valid_sa_type(i) for i in t.values())
    if t is None:
        return True
    return False

def is_valid_sa_type(t: any) -> bool:
    if is_valid_sa_type_primitive(t):
        return True
    # Import here to avoid circular import issues
    if isinstance(t, SATypeCustom):
        return True
    return False