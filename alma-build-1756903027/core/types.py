"""
Shared type definitions for the SA framework.
This module breaks circular dependencies by centralizing type definitions.
"""

from __future__ import annotations
from typing import Union, TYPE_CHECKING

if TYPE_CHECKING:
    from sa.query_language.object_list import ObjectList

# Core type definitions
SATypePrimitive = Union[str, int, bool, float, None, list['SATypePrimitive'], dict[str, 'SATypePrimitive']]

# Forward reference for the main type union
SAType = 'SAType'  # Will be defined after all classes are available

# Type aliases for query language
QueryPrimitive = Union['ObjectList', 'SAType']
QueryType = Union[QueryPrimitive, 'Chain']
Arguments = list[QueryType]
