from __future__ import annotations
from typing import TYPE_CHECKING
from sa.core.object_grouping import ObjectGrouping
from sa.query_language.errors import QueryError
from sa.query_language.chain import Operator
from sa.core.object_list import ObjectList
from sa.query_language.query_state import QueryState

if TYPE_CHECKING:
    from sa.query_language.types import QueryType, Arguments, QueryContext

def slice_operator_runner(context: QueryContext, arguments: Arguments, query_state: QueryState) -> QueryType:
    # Handle different context types
    if isinstance(context, ObjectList):
        items = context.objects
    elif isinstance(context, list):
        items = context
    else:
        raise QueryError("You can only use the slice operator on an ObjectList or list (e.g. list[2]).")
    
    if len(arguments) == 0:
        raise QueryError("Slice operator expects at least 1 argument.")
    if len(arguments) > 3:
        raise QueryError("Slice operator expects at most 3 arguments.")

    if not all(isinstance(arg, int) or arg == "" for arg in arguments):
        raise QueryError("Slice operator arguments must be integers or empty strings.")
    
    if len(arguments) == 1 and arguments[0] == "":
        raise QueryError("Invalid slice syntax: []. Wtf do I do with this?")
    
    inside_area = ":".join([str(arg) for arg in arguments])
    str_to_eval = f"items[{inside_area}]"
    try:
        result_items = eval(str_to_eval)
    except Exception as e:
        raise QueryError(f"Error while evaluating \"[{inside_area}]\": {str(e)}", could_succeed_with_more_data=True)
    
    # Return appropriate type based on input context
    if isinstance(context, ObjectList) and not isinstance(result_items, ObjectGrouping):
        return ObjectList(result_items)
    else:
        return result_items

SliceOperator = Operator(
    name="slice",
    runner=slice_operator_runner
)
