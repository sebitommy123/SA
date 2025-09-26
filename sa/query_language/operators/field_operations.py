from __future__ import annotations
from typing import TYPE_CHECKING
import re
from sa.query_language.argument_parser import ArgumentParser
from sa.query_language.validators import either, is_single_object_list, is_object_grouping, is_dict
from sa.query_language.errors import QueryError
from sa.query_language.types import AbsorbingNone
from sa.query_language.chain import Operator
from sa.query_language.utils import convert_list_of_sa_objects_to_object_list_if_needed
from sa.core.object_grouping import ObjectGrouping

if TYPE_CHECKING:
    from sa.query_language.types import QueryType, Arguments, QueryContext
    from sa.core.object_list import ObjectList

def get_field_operator_runner(context: QueryType, arguments: Arguments, all_data: ObjectList) -> QueryType:
    parser = ArgumentParser("get_field")
    parser.add_arg(str, "field_name", "The field to get must be a string.")
    parser.add_arg(bool, "return_none_if_missing", "Please specify whether to return None if the field is missing.")
    parser.add_arg(bool, "return_all_values", "Please specify whether to return all values for the field from all sources.")
    parser.validate_context(either(is_object_grouping, is_dict), "You can only use the get_field operator on an individual object or dicts.")
    context, args = parser.parse(context, arguments, all_data)

    if isinstance(context, dict):
        if not args.field_name in context:
            if args.return_none_if_missing:
                return AbsorbingNone
            raise QueryError(f"Field '{args.field_name}' not found in dict: {context}")
        return context[args.field_name]
    
    object_grouping = context

    if object_grouping is AbsorbingNone:
        return AbsorbingNone

    if args.return_all_values:
        return object_grouping.get_all_field_values(args.field_name, all_data)

    if not object_grouping.has_field(args.field_name):
        if args.return_none_if_missing:
            return AbsorbingNone
        raise QueryError(f"Field '{args.field_name}' not found in object: {object_grouping}")

    return object_grouping.get_field(args.field_name, all_data)

GetFieldOperator = Operator(
    name="get_field",
    runner=get_field_operator_runner
)

def has_field_operator_runner(context: QueryType, arguments: Arguments, all_data: ObjectList) -> QueryType:
    parser = ArgumentParser("has_field")
    parser.add_arg(str, "field_name", "The field to check must be a string.")
    parser.validate_context(either(is_single_object_list, is_object_grouping, is_dict), "You can only use the has_field operator on an individual object or dicts.")
    context, args = parser.parse(context, arguments, all_data)
    
    if isinstance(context, dict):
        return args.field_name in context
    
    object_grouping = context if isinstance(context, ObjectGrouping) else context.objects[0]
    
    return object_grouping.has_field(args.field_name)

HasFieldOperator = Operator(
    name="has_field",
    runner=has_field_operator_runner
)

def get_field_regex_operator_runner(context: QueryType, arguments: Arguments, all_data: ObjectList) -> QueryType:
    parser = ArgumentParser("get_field_regex")
    parser.add_arg(str, "field_name")
    parser.validate_context(either(is_single_object_list, is_object_grouping))
    context, args = parser.parse(context, arguments, all_data)

    object_grouping = context if isinstance(context, ObjectGrouping) else context.objects[0]
    
    try:
        # Compile the regex pattern
        pattern = re.compile(args.field_name)
    except re.error as e:
        raise QueryError(f"Invalid regex pattern '{args.field_name}': {e}")
    
    result = []
    for obj in context.objects:
        matching_fields = []
        for field_name in obj.properties.keys():
            if pattern.search(field_name):
                field_value = obj.get_field(field_name, all_data)
                field_value = convert_list_of_sa_objects_to_object_list_if_needed(field_value)
                matching_fields.append((field_name, field_value))
        
        if matching_fields:
            # If multiple fields match, return a dict with field names as keys
            field_dict = {name: value for name, value in matching_fields}
            result.append(field_dict)
    
    result = convert_list_of_sa_objects_to_object_list_if_needed(result)

    if len(result) == 1:
        return result[0]
    if len(result) == 0:
        return None
    
    return result

GetFieldRegexOperator = Operator(
    name="get_field_regex",
    runner=get_field_regex_operator_runner
)
