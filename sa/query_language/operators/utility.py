from __future__ import annotations
from typing import TYPE_CHECKING
from sa.query_language.argument_parser import ArgumentParser
from sa.query_language.validators import anything, is_valid_querytype, is_valid_primitive, either, is_object_list, is_list
from sa.query_language.chain import Operator, Chain
from sa.core.sa_object import SAObject
from sa.core.object_list import ObjectList
from sa.query_language.query_state import QueryState

if TYPE_CHECKING:
    from sa.query_language.types import QueryType, Arguments, QueryContext
    from sa.core.object_list import ObjectList

def show_plan_operator_runner(context: ObjectList, arguments: Arguments, query_state: QueryState) -> QueryType:
    parser = ArgumentParser("show_plan")
    parser.add_arg(Chain, "chain", "The chain to show the plan for")
    parser.validate_context(anything, "")
    context, args = parser.parse(context, arguments, query_state)
    return f"Chain({args.chain}) {query_state.needed_scopes}"

ShowPlanOperator = Operator(
    name="show_plan",
    runner=show_plan_operator_runner
)

def to_json_operator_runner(context: QueryType, arguments: Arguments, query_state: QueryState) -> QueryType:
    parser = ArgumentParser("to_json")
    parser.validate_context(is_valid_querytype)
    context, args = parser.parse(context, arguments, query_state)
    
    if isinstance(context, SAObject):
        return context.json
    elif isinstance(context, ObjectList):
        return [obj.json for obj in context.objects]
    else:
        return context

ToJsonOperator = Operator(
    name="to_json",
    runner=to_json_operator_runner
)

def count_operator_runner(context: QueryContext, arguments: Arguments, query_state: QueryState) -> QueryType:
    parser = ArgumentParser("count")
    parser.validate_context(either(is_object_list, is_list), "Can only count ObjectList or list items")
    context, args = parser.parse(context, arguments, query_state)
    
    if isinstance(context, ObjectList):
        count = len(context.objects)
        return count
    
    if isinstance(context, list):
        count = len(context)
        return count

CountOperator = Operator(
    name="count",
    runner=count_operator_runner
)

def any_operator_runner(context: QueryContext, arguments: Arguments, query_state: QueryState) -> QueryType:
    parser = ArgumentParser("any")
    parser.validate_context(is_valid_primitive)
    context, args = parser.parse(context, arguments, query_state)
    
    if isinstance(context, ObjectList):
        result = len(context.objects) > 0
        return result
    
    if isinstance(context, list):
        result = len(context) > 0
        return result
    
    # For primitive types, consider them as "any" if they're not None/empty
    result = bool(context)
    return result

AnyOperator = Operator(
    name="any",
    runner=any_operator_runner
)


def types_operator_runner(context: QueryContext, arguments: Arguments, query_state: QueryState) -> QueryType:
    # just returns all the types in the context, deduplicated
    # context should be an ObjectList
    parser = ArgumentParser("types")
    parser.validate_context(is_object_list, "Can only use types operator on an ObjectList")
    context, args = parser.parse(context, arguments, query_state)
    
    context: ObjectList = context
    return list(context.types)

TypesOperator = Operator(
    name="types",
    runner=types_operator_runner
)

