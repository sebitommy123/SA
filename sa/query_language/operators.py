from __future__ import annotations
from typing import Callable, Any, TYPE_CHECKING, Optional, List, Type, Union
import re

if TYPE_CHECKING:
    from sa.query_language.types import QueryType, Arguments, QueryContext
    from sa.query_language.chain import Operator, OperatorNode, Chain
    from sa.core.object_list import ObjectList
    from sa.query_language.validators import is_valid_primitive

from sa.query_language.validators import anything, either, is_absorbing_none, is_dict, is_list, is_object_grouping, is_object_list, is_single_object_list
from sa.query_language.errors import QueryError
from sa.core.object_list import ObjectList
from sa.core.sa_object import SAObject
from sa.core.object_grouping import ObjectGrouping
from sa.core.types import SAType
from sa.core.types import is_valid_sa_type
from sa.query_language.types import AbsorbingNone, AbsorbingNoneType, QueryType, Arguments, QueryContext
from sa.query_language.chain import Operator, Chain
from sa.query_language.validators import is_valid_primitive, is_valid_querytype
from dataclasses import dataclass

DEBUG_ENABLED = False
PROFILING_ENABLED = False

class ParsedArguments:
    """Container for parsed and validated arguments."""
    
    def __init__(self, **kwargs):
        self._args = []
        self._kwargs = {}
        
        # Separate positional and keyword arguments
        for key, value in kwargs.items():
            if key.startswith('arg_'):
                # Positional argument
                index = int(key[4:])  # Extract number from 'arg_0', 'arg_1', etc.
                while len(self._args) <= index:
                    self._args.append(None)
                self._args[index] = value
            else:
                # Named argument
                self._kwargs[key] = value
    
    def __getitem__(self, index):
        """Allow indexing like args[0], args[1], etc."""
        return self._args[index]
    
    def __len__(self):
        """Allow len(args) to work."""
        return len(self._args)
    
    def __iter__(self):
        """Allow 'for arg in args' to work."""
        return iter(self._args)
    
    def __getattr__(self, name):
        """Allow access to named arguments like args.field_name."""
        if name in self._kwargs:
            return self._kwargs[name]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

class ArgumentParser:
    """Parser for validating operator arguments with a fluent builder API."""
    
    def __init__(self, operator_name: str):
        self.operator_name = operator_name
        self.argument_specs = []
        self.context_spec = None
    
    def validate_context(self, type_or_validator: Union[Type, Callable], description: str):
        if isinstance(type_or_validator, type):
            type_or_validator = lambda x: isinstance(x, type_or_validator)
            description = f"{self.operator_name} operates on {type_or_validator.__name__}"
        self.context_spec = {
            "validator": either(type_or_validator, is_absorbing_none),
            "description": description
        }
    
    def dont_validate_context(self):
        self.validate_context(lambda x: True, "Context is not validated")
    
    def add_arg(self, type_or_validator: Union[Type, Callable], name: str, description: str):
        if isinstance(type_or_validator, type):
            original_type = type_or_validator
            type_or_validator = lambda x: isinstance(x, original_type)
            description = f"Expected argument {name} to be of type {original_type.__name__}"

        self.argument_specs.append({
            'validator': either(type_or_validator, is_absorbing_none),
            'name': name,
            'description': description
        })
        return self
    
    def parse(self, context: QueryContext, arguments: Arguments, all_data: ObjectList) -> ParsedArguments:
        assert self.context_spec is not None, f"{self.operator_name} operator must validate context"
        if not self.context_spec['validator'](context):
            raise QueryError(f"{self.operator_name} operator can't operate on {type(context).__name__}. {self.context_spec['description']}")

        if len(self.argument_specs) != len(arguments):
            raise QueryError(f"{self.operator_name} operator expects {len(self.argument_specs)} arguments, got {len(arguments)}: {arguments}")
        
        # Run any chains if the validator doesn't like them
        def run_chain_if_fails_validator(arg, spec):
            if not spec['validator'](arg) and isinstance(arg, Chain):
                return arg.run(context, all_data)
            return arg
        processed_args = [run_chain_if_fails_validator(arg, spec) for arg, spec in zip(arguments, self.argument_specs)]
        
        # Build result object
        result_kwargs = {}
        for i, spec in enumerate(self.argument_specs):
            arg = processed_args[i]
            if not spec['validator'](arg):
                raise QueryError(f"{self.operator_name} operator, argument '{spec['name']}' can't be {type(arg).__name__}. {spec['description']}")
            result_kwargs[spec['name']] = arg
            
        return ParsedArguments(**result_kwargs)

def run_all_if_possible(context: ObjectList, arguments: Arguments, all_data: ObjectList) -> list[QueryType]:
    result = []
    for arg in arguments:
        if isinstance(arg, Chain):
            # Run the chain and add the result
            result.append(arg.run(context, all_data))
        else:
            # Leave primitives as they are
            result.append(arg)
    return result

def equals_operator_runner(context: ObjectList, arguments: Arguments, all_data: ObjectList) -> QueryType:
    parser = ArgumentParser("equals")
    parser.validate_context(anything, "")
    parser.add_arg(is_valid_sa_type, "left", "Left side of equals must be a valid SA type")
    parser.add_arg(is_valid_sa_type, "right", "Right side of equals must be a valid SA type")
    args = parser.parse(context, arguments, all_data)
    
    left = args.left
    right = args.right
    
    if left is AbsorbingNone or right is AbsorbingNone:
        return AbsorbingNone

    result = left == right
    return result
EqualsOperator = Operator(
    name="equals",
    runner=equals_operator_runner
)

def regex_equals_operator_runner(context: ObjectList, arguments: Arguments, all_data: ObjectList) -> QueryType:
    parser = ArgumentParser("regex_equals")
    parser.add_arg(str, "left", "Left side of regex equals must be a string")
    parser.add_arg(str, "right", "Right side of regex equals must be a string")
    parser.validate_context(anything, "")
    args = parser.parse(context, arguments, all_data)
    
    left = args.left

    if left is AbsorbingNone or args.right is AbsorbingNone:
        return AbsorbingNone
    
    try:
        # Compile the regex pattern
        pattern = re.compile(args.right)
        # Test if the left string matches the regex pattern
        result = bool(pattern.search(left))
        return result
    except re.error as e:
        raise QueryError(f"Invalid regex pattern '{args.right}': {e}")
RegexEqualsOperator = Operator(
    name="regex_equals",
    runner=regex_equals_operator_runner
)

# show_plan operator takes on argument (a chain) and just returns it (doesn't run it)
def show_plan_operator_runner(context: ObjectList, arguments: Arguments, all_data: ObjectList) -> QueryType:
    parser = ArgumentParser("show_plan")
    parser.add_arg(Chain, "chain", "The chain to show the plan for")
    parser.validate_context(anything, "")
    args = parser.parse(context, arguments, all_data)
    return args.chain
ShowPlanOperator = Operator(
    name="show_plan",
    runner=show_plan_operator_runner
)

def and_operator_runner(context: ObjectList, arguments: Arguments, all_data: ObjectList) -> QueryType:
    parser = ArgumentParser("and")
    parser.add_arg(is_valid_sa_type, "left")
    parser.add_arg(is_valid_sa_type, "right")
    args = parser.parse(context, arguments, all_data)
    
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

def or_operator_runner(context: ObjectList, arguments: Arguments, all_data: ObjectList) -> QueryType:
    parser = ArgumentParser("or")
    parser.add_arg(is_valid_sa_type, "left")
    parser.add_arg(is_valid_sa_type, "right")
    args = parser.parse(context, arguments, all_data)
    
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

def convert_list_of_sa_objects_to_object_list_if_needed(sa_type: 'SAType') -> 'SAType':
    if isinstance(sa_type, list):
        if all(isinstance(obj, SAObject) for obj in sa_type):
            return ObjectList(sa_type)
    return sa_type

def to_json_operator_runner(context: QueryType, arguments: Arguments, all_data: ObjectList) -> QueryType:
    parser = ArgumentParser("to_json")
    parser.validate_context(is_valid_querytype)
    parser.parse(context, arguments, all_data)
    
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

def get_field_regex_operator_runner(context: QueryType, arguments: Arguments, all_data: ObjectList) -> QueryType:
    parser = ArgumentParser("get_field_regex")
    parser.add_arg(str, "field_name")
    parser.validate_context(either(is_single_object_list, is_object_grouping))
    args = parser.parse(context, arguments, all_data)

    object_grouping = context if isinstance(context, ObjectGrouping) else context.objects[0]
    
    try:
        # Compile the regex pattern
        pattern = re.compile(args.field_name)
    except re.error as e:
        raise ValueError(f"Invalid regex pattern '{args.field_name}': {e}")
    
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

def get_field_operator_runner(context: QueryType, arguments: Arguments, all_data: ObjectList) -> QueryType:
    parser = ArgumentParser("get_field")
    parser.add_arg(str, "field_name", "The field to get must be a string.")
    parser.add_arg(bool, "return_none_if_missing", "Please specify whether to return None if the field is missing.")
    parser.add_arg(bool, "return_all_values", "Please specify whether to return all values for the field from all sources.")
    parser.validate_context(either(is_single_object_list, is_object_grouping, is_dict), "You can only use the get_field operator on an individual object or dicts.")
    args = parser.parse(context, arguments, all_data)

    if isinstance(context, dict):
        if not args.field_name in context:
            if args.return_none_if_missing:
                return AbsorbingNone
            raise QueryError(f"Field '{args.field_name}' not found in dict: {context}")
        return context[args.field_name]
    
    object_grouping = context if isinstance(context, ObjectGrouping) else context.objects[0]

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
    args = parser.parse(context, arguments, all_data)
    
    if isinstance(context, dict):
        return args.field_name in context
    
    object_grouping = context if isinstance(context, ObjectGrouping) else context.objects[0]
    
    return object_grouping.has_field(args.field_name)
HasFieldOperator = Operator(
    name="has_field",
    runner=has_field_operator_runner
)


def filter_operator_runner(context: ObjectList, arguments: Arguments, all_data: ObjectList) -> QueryType:
    parser = ArgumentParser("filter")
    parser.add_arg(Chain, "chain", "The filtering expression must be able to be evaluated on each object to a boolean.")
    parser.validate_context(is_object_list, "You can use the filter operator on an ObjectList.")
    args = parser.parse(context, arguments, all_data)
        
    survivors: list[ObjectGrouping] = []
    for i, grouped_object in enumerate(context.objects):
        chain_result = args.chain.run(ObjectList([grouped_object]), all_data)

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

def foreach_operator_runner(context: ObjectList, arguments: Arguments, all_data: ObjectList) -> QueryType:
    raise QueryError("Foreach operator is not implemented yet")
ForeachOperator = Operator(
    name="foreach",
    runner=foreach_operator_runner
)

def map_operator_runner(context: ObjectList, arguments: Arguments, all_data: ObjectList) -> QueryType:
    parser = ArgumentParser("map")
    parser.add_arg(Chain, "chain", "The mapping expression must be able to be evaluated on each object to a value.")
    parser.validate_context(is_object_list, "You can use the map operator on an ObjectList.")
    args = parser.parse(context, arguments, all_data)
    
    results = [args.chain.run(obj, all_data) for obj in context.objects]
    results = [res for res in results if not isinstance(res, AbsorbingNoneType)]
    if len(results) == 0:
        return []
    return ObjectList(results) if isinstance(results[0], ObjectGrouping) else results
MapOperator = Operator(
    name="map",
    runner=map_operator_runner
)

def select_operator_runner(context: ObjectList, arguments: Arguments, all_data: ObjectList) -> QueryType:
    # takes in a variable number of arguments, each a string
    # only keeps those fields of the context
    arguments = run_all_if_possible(context, arguments, all_data)

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
    
    assert False

SelectOperator = Operator(
    name="select",
    runner=select_operator_runner
)

def flatten_fully(lst):
    result = []
    for i in lst:
        if isinstance(i, list):
            result.extend(flatten_fully(i))
        else:
            result.append(i)
    return result

def includes_operator_runner(context: SAType, arguments: Arguments, all_data: ObjectList) -> QueryType:
    parser = ArgumentParser("includes")
    parser.add_arg(str, "value", "The value to search for must be a string.")
    parser.validate_context(is_list, "Includes must be called on a list.")
    args = parser.parse(context, arguments, all_data)
    
    assert not isinstance(context, dict), f"includes operator context must not be a dict, got {type(context)}: {context}"
    
    if not isinstance(context, list):
        result = args.value == context
        return result
    
    flattened = flatten_fully(context)
    
    result = args.value in flattened
    return result
IncludesOperator = Operator(
    name="includes",
    runner=includes_operator_runner
)

def flatten_operator_runner(context: SAType, arguments: Arguments, all_data: ObjectList) -> QueryType:
    parser = ArgumentParser("flatten")
    parser.validate_context(is_list, "Flatten must be called on a list.")
    parser.parse(context, arguments, all_data)
    
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

def unique_operator_runner(context: SAType, arguments: Arguments, all_data: ObjectList) -> QueryType:
    parser = ArgumentParser("unique")
    parser.validate_context(is_list, "Requires list")
    parser.parse(context, arguments, all_data)
    
    unique_items = list(set(context))
    
    return unique_items
UniqueOperator = Operator(
    name="unique",
    runner=unique_operator_runner
)

def count_operator_runner(context: QueryContext, arguments: Arguments, all_data: ObjectList) -> QueryType:
    parser = ArgumentParser("count")
    parser.validate_context(either(is_object_list, is_list), "Can only count ObjectList or list items")
    parser.parse(context, arguments, all_data)
    
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

def describe_operator_runner(context: QueryContext, arguments: Arguments, all_data: ObjectList) -> QueryType:
    parser = ArgumentParser("describe")
    parser.validate_context(is_valid_primitive)
    parser.parse(context, arguments, all_data)
    
    # If input is not an ObjectList, just return str() representation
    if not isinstance(context, ObjectList):
        result = str(context)
        return result
    
    # Handle ObjectList input
    
    if len(context.objects) == 0:
        return "Empty ObjectList"
    
    # Collect basic statistics
    total_count = len(context.objects)
    types = set()
    sources = set()
    
    # Analyze each object to collect types, sources, and properties
    type_properties = {}  # type -> set of properties
    type_sources = {}     # type -> set of sources
    
    for obj in context.objects:
        obj_types = obj.types  # This is a list of types
        obj_source = obj.source
        
        # Add all types from this object
        for obj_type in obj_types:
            types.add(obj_type)
            
            # Track properties for this type
            if obj_type not in type_properties:
                type_properties[obj_type] = set()
                type_sources[obj_type] = set()
            
            type_sources[obj_type].add(obj_source)
            
            # Collect all properties from this object
            for prop_name in obj.properties.keys():
                type_properties[obj_type].add(prop_name)
        
        sources.add(obj_source)
    
    # Build description string
    description_parts = []
    description_parts.append(f"ObjectList with {total_count} objects")
    
    if len(types) > 0:
        types_str = ", ".join(sorted(types))
        description_parts.append(f"Types: {types_str}")
    
    if len(sources) > 0:
        sources_str = ", ".join(sorted(sources))
        description_parts.append(f"Sources: {sources_str}")
    
    # Add schema information for each type
    for obj_type in sorted(types):
        type_count = sum(1 for obj in context.objects if obj_type in obj.types)
        type_sources_list = sorted(type_sources[obj_type])
        properties_list = sorted(type_properties[obj_type])
        
        type_info = f"\n  {obj_type} ({type_count} objects)"
        if type_sources_list:
            type_info += f" from sources: {', '.join(type_sources_list)}"
        
        if properties_list:
            type_info += f"\n    Properties: {', '.join(properties_list)}"
        else:
            type_info += "\n    No properties"
        
        description_parts.append(type_info)
    
    result = "\n".join(description_parts)
    return result
DescribeOperator = Operator(
    name="describe",
    runner=describe_operator_runner
)

def summary_operator_runner(context: QueryContext, arguments: Arguments, all_data: ObjectList) -> QueryType:
    parser = ArgumentParser("summary")
    parser.validate_context(is_valid_primitive)
    parser.parse(context, arguments, all_data)
    
    # If input is not an ObjectList, just return str() representation
    if not isinstance(context, ObjectList):
        result = str(context)
        return result
    
    # Handle ObjectList input
    
    if len(context.objects) == 0:
        return "Empty ObjectList"
    
    # Collect basic statistics
    total_count = len(context.objects)
    types = set()
    sources = set()
    
    # Analyze each object to collect types, sources, and properties
    type_properties = {}  # type -> set of properties
    type_sources = {}     # type -> set of sources
    property_values = {}  # property -> list of values (for variance calculation)
    
    for obj in context.objects:
        obj_types = obj.types  # This is a list of types
        obj_source = obj.source
        
        # Add all types from this object
        for obj_type in obj_types:
            types.add(obj_type)
            
            # Track properties for this type
            if obj_type not in type_properties:
                type_properties[obj_type] = set()
                type_sources[obj_type] = set()
            
            type_sources[obj_type].add(obj_source)
            
            # Collect all properties from this object
            for prop_name in obj.properties.keys():
                type_properties[obj_type].add(prop_name)
        
        sources.add(obj_source)
        
        # Collect property values for variance calculation
        for prop_name, prop_value in obj.properties.items():
            if prop_name not in property_values:
                property_values[prop_name] = []
            property_values[prop_name].append(prop_value)
    
    # Calculate variance for each property (using unique value count as proxy for variance)
    property_variance = {}
    for prop_name, values in property_values.items():
        # Count unique values as a measure of variance
        unique_values = len(set(str(v) for v in values))
        property_variance[prop_name] = unique_values
    
    # Build description string
    description_parts = []
    description_parts.append(f"ObjectList with {total_count} objects")
    
    if len(types) > 0:
        types_str = ", ".join(sorted(types))
        description_parts.append(f"Types: {types_str}")
    
    if len(sources) > 0:
        sources_str = ", ".join(sorted(sources))
        description_parts.append(f"Sources: {sources_str}")
    
    # Add schema information for each type
    for obj_type in sorted(types):
        type_count = sum(1 for obj in context.objects if obj_type in obj.types)
        type_sources_list = sorted(type_sources[obj_type])
        properties_list = sorted(type_properties[obj_type])
        
        type_info = f"\n  {obj_type} ({type_count} objects)"
        if type_sources_list:
            type_info += f" from sources: {', '.join(type_sources_list)}"
        
        if properties_list:
            # If more than 15 properties, show only the 15 with most variance
            if len(properties_list) > 15:
                # Get properties for this type and their variance scores
                type_property_variance = []
                for prop in properties_list:
                    if prop in property_variance:
                        type_property_variance.append((prop, property_variance[prop]))
                
                # Sort by variance (descending) and take top 15
                type_property_variance.sort(key=lambda x: x[1], reverse=True)
                top_properties = [prop for prop, _ in type_property_variance[:15]]
                type_info += f"\n    Properties ({len(properties_list)} total, showing 15 most variable): {', '.join(top_properties)}"
            else:
                type_info += f"\n    Properties: {', '.join(properties_list)}"
        else:
            type_info += "\n    No properties"
        
        description_parts.append(type_info)
    
    result = "\n".join(description_parts)
    return result

SummaryOperator = Operator(
    name="summary",
    runner=summary_operator_runner
)

def slice_operator_runner(context: QueryContext, arguments: Arguments, all_data: ObjectList) -> QueryType:
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
        raise QueryError(f"Error while evaluating \"[{inside_area}]\": {str(e)}")
    
    # Return appropriate type based on input context
    if isinstance(context, ObjectList) and not isinstance(result_items, ObjectGrouping):
        return ObjectList(result_items)
    else:
        return result_items

SliceOperator = Operator(
    name="slice",
    runner=slice_operator_runner
)

def any_operator_runner(context: QueryContext, arguments: Arguments, all_data: ObjectList) -> QueryType:
    parser = ArgumentParser("any")
    parser.validate_context(is_valid_primitive)
    parser.parse(context, arguments, all_data)
    
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

def get_by_id_operator_runner(context: ObjectList, arguments: Arguments, all_data: ObjectList) -> QueryType:
    parser = ArgumentParser("get_by_id")
    parser.add_arg(str, "obj_id", "The ID to search for must be a string.")
    parser.validate_context(is_object_list, "You can only use the get_by_id operator on an ObjectList.")
    args = parser.parse(context, arguments, all_data)
    
    return context.get_by_id(args.obj_id)
GetByIdOperator = Operator(
    name="get_by_id",
    runner=get_by_id_operator_runner
)

def filter_by_type_operator_runner(context: ObjectList, arguments: Arguments, all_data: ObjectList) -> QueryType:
    parser = ArgumentParser("filter_by_type")
    parser.add_arg(str, "type_name", "The type to filter by must be a string.")
    parser.validate_context(is_object_list, "You can only use the filter_by_type operator on an ObjectList.")
    args = parser.parse(context, arguments, all_data)
    
    return context.filter_by_type(args.type_name)

FilterByTypeOperator = Operator(
    name="filter_by_type",
    runner=filter_by_type_operator_runner
)

all_operators = [
    EqualsOperator,
    RegexEqualsOperator,
    AndOperator,
    OrOperator,
    GetFieldOperator,
    FilterOperator,
    SelectOperator,
    IncludesOperator,
    FlattenOperator,
    UniqueOperator,
    CountOperator,
    DescribeOperator,
    SummaryOperator,
    SliceOperator,
    ToJsonOperator,
    AnyOperator,
    HasFieldOperator,
    ShowPlanOperator,
    GetByIdOperator,
    FilterByTypeOperator,
    MapOperator,
    ForeachOperator
]