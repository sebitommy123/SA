# Operators package
from .comparison import EqualsOperator, RegexEqualsOperator
from .logical import AndOperator, OrOperator
from .field_operations import GetFieldOperator, HasFieldOperator, GetFieldRegexOperator
from .list_operations import (
    FilterOperator, MapOperator, ForeachOperator, SelectOperator,
    IncludesOperator, FlattenOperator, UniqueOperator
)
from .utility import ShowPlanOperator, ToJsonOperator, CountOperator, AnyOperator
from .object_operations import GetByIdOperator, FilterByTypeOperator, FilterBySourceOperator
from .analysis import DescribeOperator, SummaryOperator
from .slice import SliceOperator

# Export all operators in a single list
all_operators = [
    EqualsOperator,
    RegexEqualsOperator,
    AndOperator,
    OrOperator,
    GetFieldOperator,
    HasFieldOperator,
    GetFieldRegexOperator,
    FilterOperator,
    MapOperator,
    ForeachOperator,
    SelectOperator,
    IncludesOperator,
    FlattenOperator,
    UniqueOperator,
    ShowPlanOperator,
    ToJsonOperator,
    CountOperator,
    AnyOperator,
    GetByIdOperator,
    FilterByTypeOperator,
    FilterBySourceOperator,
    DescribeOperator,
    SummaryOperator,
    SliceOperator,
]
