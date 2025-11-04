from __future__ import annotations
from typing import TYPE_CHECKING
from sa.query_language.debug import debugger
from sa.query_language.scopes import Scopes, chain_to_condition
from sa.query_language.argument_parser import ArgumentParser, run_all_if_possible
from sa.query_language.validators import is_object_list, is_list, either, is_object_grouping, is_dict, is_string
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

def filter_operator_runner(context: QueryContext, arguments: Arguments, query_state: QueryState) -> QueryType:
    parser = ArgumentParser("filter")
    parser.add_arg(Chain, "chain", "The filtering expression must be able to be evaluated on each object to a boolean.")
    parser.validate_context(either(is_object_list, is_list), "You can use the filter operator on an ObjectList or a regular list.")
    context, args = parser.parse(context, arguments, query_state)

    condition = chain_to_condition(args.chain)
    if condition:
        query_state.needed_scopes = query_state.needed_scopes.add_condition(condition)
    
    if context is AbsorbingNone:
        return AbsorbingNone

    debugger.start_part("FILTER", "Filtering objects")
    
    if isinstance(context, ObjectList):
        survivors: list[ObjectGrouping] = []
        for i, grouped_object in enumerate(context.objects):
            new_state = QueryState.setup(query_state.providers)
            chain_result = args.chain.run(ObjectList([grouped_object]), new_state)
            # query_state.staged_scopes.scopes.update(new_state.final_needed_scopes)
            # TODO: Implement once we have proper named contexts

            if isinstance(chain_result, AbsorbingNoneType):
                continue

            if not isinstance(chain_result, bool):
                debugger.end_part("Filtering objects")
                raise QueryError(f"Filter expression for {grouped_object} result must be a boolean, got {type(chain_result).__name__}: {chain_result}")
            
            if chain_result:
                survivors.append(grouped_object)
        
        debugger.end_part("Filtering objects")
        # Pass parent cache - ObjectList will automatically filter it down
        return ObjectList(survivors, cache=context._cache)
    else:  # Regular Python list
        survivors = []
        for item in context:
            new_state = QueryState.setup(query_state.providers)
            chain_result = args.chain.run(item, new_state)

            if isinstance(chain_result, AbsorbingNoneType):
                continue

            if not isinstance(chain_result, bool):
                debugger.end_part("Filtering objects")
                raise QueryError(f"Filter expression for {item} result must be a boolean, got {type(chain_result).__name__}: {chain_result}")
            
            if chain_result:
                survivors.append(item)
        
        debugger.end_part("Filtering objects")
        return survivors

FilterOperator = Operator(
    name="filter",
    runner=filter_operator_runner
)

def map_operator_runner(context: QueryContext, arguments: Arguments, query_state: QueryState) -> QueryType:
    parser = ArgumentParser("map")
    parser.add_arg(Chain, "chain", "The mapping expression must be able to be evaluated on each object to a value.")
    parser.validate_context(either(is_object_list, is_list), "You can use the map operator on an ObjectList or a regular list.")
    context, args = parser.parse(context, arguments, query_state)
    
    if isinstance(context, ObjectList):
        results = [args.chain.run(obj, QueryState.setup(query_state.providers)) for obj in context.objects]
        # TODO: Implement once we have proper named contexts
        results = [res for res in results if not isinstance(res, AbsorbingNoneType)]
        if len(results) == 0:
            return []
        if isinstance(results[0], ObjectGrouping):
            # Check if results are the same objects (identity check) or new ones
            # If they're the same, we can reuse cache; otherwise we can't
            if len(results) == len(context.objects) and all(r is obj for r, obj in zip(results, context.objects)):
                # Same objects, pass parent cache - ObjectList will automatically filter it down
                return ObjectList(results, cache=context._cache)
            else:
                # New/modified objects, can't reuse cache
                return ObjectList(results)
        return results
    else:  # Regular Python list
        results = [args.chain.run(item, QueryState.setup(query_state.providers)) for item in context]
        results = [res for res in results if not isinstance(res, AbsorbingNoneType)]
        return results

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
        return context.select_fields(set(arguments))
    
    if isinstance(context, ObjectList):
        # Note: select_fields creates new ObjectGrouping instances, so we can't directly reuse cache
        # But we can still create a filtered cache for the original objects for potential future use
        selected_objects = [obj.select_fields(set(arguments)) for obj in context.objects]
        # Since select_fields creates new objects, we can't reuse the cache directly
        return ObjectList(selected_objects)

SelectOperator = Operator(
    name="select",
    runner=select_operator_runner
)

def includes_operator_runner(context: SAType, arguments: Arguments, query_state: QueryState) -> QueryType:
    parser = ArgumentParser("includes")
    parser.add_arg(str, "value", "The value to search for must be a string.")
    parser.validate_context(either(is_list, is_string), "Includes must be called on a list or string.")
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
