from __future__ import annotations
from typing import TYPE_CHECKING
from sa.query_language.query_scope import chain_to_condition
from sa.query_language.argument_parser import ArgumentParser, run_all_if_possible
from sa.query_language.validators import is_object_list, is_list, either, is_object_grouping, is_dict
from sa.query_language.errors import QueryError, assert_query
from sa.query_language.types import AbsorbingNone, AbsorbingNoneType
from sa.query_language.chain import Operator, Chain
from sa.query_language.utils import flatten_fully
from sa.core.object_list import ObjectList
from sa.core.object_grouping import ObjectGrouping
from sa.core.types import SAType
from sa.query_language.query_state import QueryState

if TYPE_CHECKING:
    from sa.query_language.types import QueryType, Arguments, QueryContext

def filter_operator_runner(context: ObjectList, arguments: Arguments, query_state: QueryState) -> QueryType:
    parser = ArgumentParser("filter")
    parser.add_arg(Chain, "chain", "The filtering expression must be able to be evaluated on each object to a boolean.")
    parser.validate_context(is_object_list, "You can use the filter operator on an ObjectList.")
    context, args = parser.parse(context, arguments, query_state)

    condition = chain_to_condition(args.chain)
    if condition:
        query_state.needed_scopes = query_state.needed_scopes.add_condition(condition)
    
    if context is AbsorbingNone:
        return AbsorbingNone
        
    survivors: list[ObjectGrouping] = []
    for i, grouped_object in enumerate(context.objects):
        chain_result = args.chain.run(ObjectList([grouped_object]), query_state)

        if isinstance(chain_result, AbsorbingNoneType):
            continue

        if not isinstance(chain_result, bool):
            raise QueryError(f"Filter expression for {grouped_object} result must be a boolean, got {type(chain_result).__name__}: {chain_result}")
        
        if chain_result:
            survivors.append(grouped_object)
    
    return ObjectList(survivors)

FilterOperator = Operator(
    name="filter",
    runner=filter_operator_runner
)

def map_operator_runner(context: ObjectList, arguments: Arguments, query_state: QueryState) -> QueryType:
    parser = ArgumentParser("map")
    parser.add_arg(Chain, "chain", "The mapping expression must be able to be evaluated on each object to a value.")
    parser.validate_context(is_object_list, "You can use the map operator on an ObjectList.")
    context, args = parser.parse(context, arguments, query_state)
    
    results = [args.chain.run(obj, query_state) for obj in context.objects]
    results = [res for res in results if not isinstance(res, AbsorbingNoneType)]
    if len(results) == 0:
        return []
    return ObjectList(results) if isinstance(results[0], ObjectGrouping) else results

MapOperator = Operator(
    name="map",
    runner=map_operator_runner
)

def foreach_operator_runner(context: ObjectList, arguments: Arguments, query_state: QueryState) -> QueryType:
    raise QueryError("Foreach operator is not implemented yet")

ForeachOperator = Operator(
    name="foreach",
    runner=foreach_operator_runner
)

def select_operator_runner(context: ObjectList, arguments: Arguments, query_state: QueryState) -> QueryType:
    # takes in a variable number of arguments, each a string
    # only keeps those fields of the context
    arguments = run_all_if_possible(context, arguments, query_state)

    context_validator = either(
        is_object_grouping,
        is_object_list,
        is_dict,
    )
    if not context_validator(context):
        raise QueryError(f"Select must be called on an ObjectList, ObjectGrouping, or dict, got {type(context)}: {context}")
    
    # validate arguments
    for arg in arguments:
        if not isinstance(arg, str):
            raise QueryError(f"Select arguments must be strings, got {type(arg)}: {arg}")
    
    # Filter needed_scopes to only include scopes that have the selected fields
    query_state.needed_scopes = query_state.needed_scopes.filter_fields(arguments)

    if isinstance(context, dict):
        return {
            k: v for k, v in context.items() if k in arguments
        }
    
    if isinstance(context, ObjectGrouping):
        return context.select_fields(arguments)
    
    if isinstance(context, ObjectList):
        return ObjectList([
            obj.select_fields(arguments) for obj in context.objects
        ])
    
    raise QueryError("Unexpected context type in select operator")

SelectOperator = Operator(
    name="select",
    runner=select_operator_runner
)

def includes_operator_runner(context: SAType, arguments: Arguments, query_state: QueryState) -> QueryType:
    parser = ArgumentParser("includes")
    parser.add_arg(str, "value", "The value to search for must be a string.")
    parser.validate_context(is_list, "Includes must be called on a list.")
    context, args = parser.parse(context, arguments, query_state)
    return args.value in context

IncludesOperator = Operator(
    name="includes",
    runner=includes_operator_runner
)

def flatten_operator_runner(context: SAType, arguments: Arguments, query_state: QueryState) -> QueryType:
    parser = ArgumentParser("flatten")
    parser.validate_context(is_list, "Flatten must be called on a list.")
    context, args = parser.parse(context, arguments, query_state)
    
    if len(context) == 0:
        return []
    
    if not all(isinstance(item, list) for item in context):
        return context
    
    result = [item for sublist in context for item in sublist]
    return result

FlattenOperator = Operator(
    name="flatten",
    runner=flatten_operator_runner
)

def unique_operator_runner(context: SAType, arguments: Arguments, query_state: QueryState) -> QueryType:
    parser = ArgumentParser("unique")
    parser.validate_context(is_list, "Requires list")
    context, args = parser.parse(context, arguments, query_state)
    
    unique_items = list(set(context))
    
    return unique_items

UniqueOperator = Operator(
    name="unique",
    runner=unique_operator_runner
)
