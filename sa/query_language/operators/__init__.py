# Operators package
from sa.query_language.operators.comparison import EqualsOperator, RegexEqualsOperator
from sa.query_language.operators.logical import AndOperator, OrOperator, AddOperator
from sa.query_language.operators.field_operations import GetFieldOperator, HasFieldOperator
from sa.query_language.operators.list_operations import (
    FilterOperator, MapOperator, ForeachOperator, SelectOperator,
    IncludesOperator, FlattenOperator, UniqueOperator
)
from sa.query_language.operators.utility import ShowPlanOperator, ToJsonOperator, CountOperator, AnyOperator, TypesOperator
from sa.query_language.operators.object_operations import GetByIdOperator, FilterByTypeOperator, FilterBySourceOperator
from sa.query_language.operators.analysis import DescribeOperator, SummaryOperator
from sa.query_language.operators.slice import SliceOperator

# Export all operators in a single list
all_operators = [
    EqualsOperator,
    RegexEqualsOperator,
    AndOperator,
    OrOperator,
    AddOperator,
    GetFieldOperator,
    HasFieldOperator,
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
    TypesOperator,
]
