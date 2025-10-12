from __future__ import annotations

# Import all operators from grouped modules
from sa.query_language.operators.comparison import EqualsOperator, RegexEqualsOperator
from sa.query_language.operators.logical import AndOperator, OrOperator
from sa.query_language.operators.field_operations import GetFieldOperator, HasFieldOperator, GetFieldRegexOperator
from sa.query_language.operators.list_operations import (
    FilterOperator, MapOperator, ForeachOperator, SelectOperator,
    IncludesOperator, FlattenOperator, UniqueOperator
)
from sa.query_language.operators.utility import ShowPlanOperator, ToJsonOperator, CountOperator, AnyOperator
from sa.query_language.operators.object_operations import GetByIdOperator, FilterByTypeOperator
from sa.query_language.operators.analysis import DescribeOperator, SummaryOperator
from sa.query_language.operators.slice import SliceOperator

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
    DescribeOperator,
    SummaryOperator,
    SliceOperator,
]
