
from typing import Callable
from sa.core.object_list import ObjectList
from sa.core.object_grouping import ObjectGrouping
from sa.query_language.types import AbsorbingNoneType, QueryType

def is_single_object_list(qt: QueryType):
    return isinstance(qt, ObjectList) and len(qt.objects) == 1

def either(*funcs: Callable[[QueryType], bool]):
    return lambda qt: any(func(qt) for func in funcs)

def is_object_grouping(qt: QueryType):
    return isinstance(qt, ObjectGrouping)

def is_dict(qt: QueryType):
    return isinstance(qt, dict)

def is_list(qt: QueryType):
    return isinstance(qt, list)

def is_string(qt: QueryType):
    return isinstance(qt, str)

def is_object_list(qt: QueryType):
    return isinstance(qt, ObjectList)

def anything(qt: QueryType):
    return True

def is_absorbing_none(qt: QueryType):
    return isinstance(qt, AbsorbingNoneType)

def is_valid_primitive(t: any) -> bool:
    # Import here to avoid circular import
    from sa.core.types import is_valid_sa_type
    from sa.core.object_list import ObjectList
    return is_valid_sa_type(t) or isinstance(t, ObjectList)

def is_valid_querytype(t: any) -> bool:
    from sa.query_language.chain import Chain
    return is_valid_primitive(t) or isinstance(t, Chain)
