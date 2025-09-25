from typing import Union
from sa.core.object_list import ObjectList
from sa.core.types import SAType
from sa.core.object_grouping import ObjectGrouping
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .chain import Chain

# It's similar to NoneType, but "absorbs" any operators, remaining unchanged.
# All operators must be able to tolerate AbsorbingNone as context and as inputs.
class AbsorbingNoneType:
    def __repr__(self):
        return "AbsorbingNone"
    def __str__(self):
        return "AbsorbingNone"
AbsorbingNone = AbsorbingNoneType()

# Type alias for query types
QueryContext = Union['ObjectList', 'SAType', 'ObjectGrouping', AbsorbingNone]
QueryType = Union[QueryContext, 'Chain']
Arguments = list['QueryType']

def query_type_to_string(qt: 'QueryType') -> str:
    if isinstance(qt, str):
        return f'"{qt}"'
    return str(qt)