from __future__ import annotations
from typing import TYPE_CHECKING
import re
from sa.query_language.argument_parser import ArgumentParser
from sa.query_language.validators import either, is_single_object_list, is_object_grouping, is_dict
from sa.query_language.errors import QueryError
from sa.query_language.types import AbsorbingNone
from sa.query_language.chain import Operator
from sa.core.object_grouping import ObjectGrouping
from sa.query_language.query_state import QueryState

if TYPE_CHECKING:
    from sa.query_language.types import QueryType, Arguments, QueryContext
    from sa.core.object_list import ObjectList

def get_field_operator_runner(context: QueryType, arguments: Arguments, query_state: QueryState) -> QueryType:
    parser = ArgumentParser("get_field")
    parser.add_arg(str, "field_name", "The field to get must be a string.")
    parser.add_arg(bool, "return_none_if_missing", "Please specify whether to return None if the field is missing.")
    parser.add_arg(bool, "return_all_values", "Please specify whether to return all values for the field from all sources.")
    parser.validate_context(either(is_object_grouping, is_dict), "You can only use the get_field operator on an individual object or dicts.")
    context, args = parser.parse(context, arguments, query_state)
    
    # Filter needed_scopes to only include scopes that have the requested field
    query_state.needed_scopes = query_state.needed_scopes.filter_fields([args.field_name])

    if isinstance(context, dict):
        if not args.field_name in context:
            if args.return_none_if_missing:
                return AbsorbingNone
            raise QueryError(f"Field '{args.field_name}' not found in dict: {context}", could_succeed_with_more_data=True)
        return context[args.field_name]
    
    object_grouping = context

    if object_grouping is AbsorbingNone:
        return AbsorbingNone

    if args.return_all_values:
        return object_grouping.get_all_field_values(args.field_name, query_state)

    if not object_grouping.has_field(args.field_name):
        if args.return_none_if_missing:
            return AbsorbingNone
        raise QueryError(f"Field '{args.field_name}' not found in object: {object_grouping}", could_succeed_with_more_data=True)

    return object_grouping.get_field(args.field_name, query_state)

GetFieldOperator = Operator(
    name="get_field",
    runner=get_field_operator_runner
)

def has_field_operator_runner(context: QueryType, arguments: Arguments, query_state: QueryState) -> QueryType:
    parser = ArgumentParser("has_field")
    parser.add_arg(str, "field_name", "The field to check must be a string.")
    parser.validate_context(either(is_single_object_list, is_object_grouping, is_dict), "You can only use the has_field operator on an individual object or dicts.")
    context, args = parser.parse(context, arguments, query_state)
    
    if isinstance(context, dict):
        return args.field_name in context
    
    object_grouping = context if isinstance(context, ObjectGrouping) else context.objects[0]
    
    return object_grouping.has_field(args.field_name)

HasFieldOperator = Operator(
    name="has_field",
    runner=has_field_operator_runner
)
