from __future__ import annotations
from typing import TYPE_CHECKING
from sa.query_language.argument_parser import ArgumentParser
from sa.core.types import is_valid_sa_type
from sa.query_language.chain import Operator
from sa.query_language.query_state import QueryState

if TYPE_CHECKING:
    from sa.query_language.types import QueryType, Arguments, QueryContext
    from sa.core.object_list import ObjectList

def and_operator_runner(context: ObjectList, arguments: Arguments, query_state: QueryState) -> QueryType:
    parser = ArgumentParser("and")
    parser.add_arg(is_valid_sa_type, "left")
    parser.add_arg(is_valid_sa_type, "right")
    context, args = parser.parse(context, arguments, query_state)
    
    left = args.left
    right = args.right
    
    if left is None or right is None:
        return False
    
    result = bool(left) and bool(right)
    return result

AndOperator = Operator(
    name="and",
    runner=and_operator_runner
)

def or_operator_runner(context: ObjectList, arguments: Arguments, query_state: QueryState) -> QueryType:
    parser = ArgumentParser("or")
    parser.add_arg(is_valid_sa_type, "left")
    parser.add_arg(is_valid_sa_type, "right")
    context, args = parser.parse(context, arguments, query_state)
    
    left = args.left
    right = args.right
    
    if left is None or right is None:
        return False
    
    result = bool(left) or bool(right)
    return result

OrOperator = Operator(
    name="or",
    runner=or_operator_runner
)
