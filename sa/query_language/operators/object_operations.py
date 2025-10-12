from __future__ import annotations
from typing import TYPE_CHECKING
from sa.query_language.types import AbsorbingNone
from sa.core.object_grouping import ObjectGrouping
from sa.query_language.argument_parser import ArgumentParser
from sa.query_language.validators import either, is_object_grouping, is_object_list
from sa.query_language.chain import Operator
from sa.core.object_list import ObjectList
from sa.query_language.query_state import QueryState

if TYPE_CHECKING:
    from sa.query_language.types import QueryType, Arguments, QueryContext

def get_by_id_operator_runner(context: ObjectList, arguments: Arguments, query_state: QueryState) -> QueryType:
    parser = ArgumentParser("get_by_id")
    parser.add_arg(str, "obj_id", "The ID to search for must be a string.")
    parser.validate_context(is_object_list, "You can only use the get_by_id operator on an ObjectList.")
    context, args = parser.parse(context, arguments, query_state)
    
    return context.get_by_id(args.obj_id)

GetByIdOperator = Operator(
    name="get_by_id",
    runner=get_by_id_operator_runner
)

def filter_by_type_operator_runner(context: ObjectList, arguments: Arguments, query_state: QueryState) -> QueryType:
    parser = ArgumentParser("filter_by_type")
    parser.add_arg(str, "type_name", "The type to filter by must be a string.")
    parser.validate_context(is_object_list, "You can only use the filter_by_type operator on an ObjectList.")
    context, args = parser.parse(context, arguments, query_state)

    # Filter needed_scopes to only include scopes with the specified type
    query_state.needed_scopes = query_state.needed_scopes.filter_type(args.type_name)

    return context.filter_by_type(args.type_name)

FilterByTypeOperator = Operator(
    name="filter_by_type",
    runner=filter_by_type_operator_runner
)

def filter_by_source_operator_runner(context: ObjectList, arguments: Arguments, query_state: QueryState) -> QueryType:
    parser = ArgumentParser("filter_by_source")
    parser.add_arg(str, "source_name", "The source to filter by must be a string.")
    parser.validate_context(either(is_object_list, is_object_grouping), "You can only use the filter_by_source operator on an ObjectList or ObjectGrouping.")
    context, args = parser.parse(context, arguments, query_state)

    if isinstance(context, ObjectGrouping):
        result = context.select_sources(args.source_name)
        if result is None:
            return AbsorbingNone
        return result
    
    filtered = context.filter_by_source(args.source_name)
    selected = [obj.select_sources(args.source_name) for obj in filtered.objects]
    selected = [obj for obj in selected if obj is not None]
    return ObjectList(selected)

FilterBySourceOperator = Operator(
    name="filter_by_source",
    runner=filter_by_source_operator_runner
)
