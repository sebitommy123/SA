from __future__ import annotations
from typing import Callable, Any, TYPE_CHECKING, Optional, List, Type, Union

if TYPE_CHECKING:
    from sa.query_language.main import QueryType, Arguments, ObjectList, Operator, OperatorNode, QueryPrimitive, Chain, is_valid_primitive

from sa.query_language.object_list import ObjectList
from sa.core.sa_object import SAObject, SAType, is_valid_sa_type
from sa.query_language.main import Operator, QueryType, Arguments, QueryPrimitive, Chain, is_valid_primitive
from dataclasses import dataclass
import inspect

# Global debug flag that can be controlled from the shell
DEBUG_ENABLED = False

def debug(*args):
    """Debug function that automatically prefixes messages with the calling function name."""
    if not DEBUG_ENABLED:
        return
        
    # Get the calling function name
    caller_frame = inspect.currentframe().f_back
    if caller_frame:
        caller_name = caller_frame.f_code.co_name
        # Clean up the function name to be more readable
        if caller_name.endswith('_operator_runner'):
            caller_name = caller_name.replace('_operator_runner', ' operator runner')
        elif caller_name.endswith('_runner'):
            caller_name = caller_name.replace('_runner', ' runner')
        
        # Print with prefix
        print(f"[{caller_name}]", *args)
    else:
        print("[unknown]", *args)

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
    
    def __init__(self):
        self.argument_specs = []
        self.allow_variable = False
        self.min_count = 0
        self.max_count = None
        self.context_spec = None
    
    def allow_variable_args(self, min_count: int = 0, max_count: Optional[int] = None):
        """Allow variable number of arguments."""
        self.allow_variable = True
        self.min_count = min_count
        self.max_count = max_count
        return self
    
    def validate_context(self, type_or_validator: Union[Type, Callable]):
        if isinstance(type_or_validator, type):
            self.context_spec = {
                "type": type_or_validator,
                "validator": None
            }
        else:
            self.context_spec = {
                "type": None,
                "validator": type_or_validator
            }
        return self
    
    def add_arg(self, type_or_validator: Union[Type, Callable], name: str, required: bool = True):
        """Add an argument specification. Can pass either a type or a validator function."""
        # Determine if it's a type or validator function
        if isinstance(type_or_validator, type):
            expected_type = type_or_validator
            validator = None
        else:
            expected_type = None
            validator = type_or_validator
        
        self.argument_specs.append({
            'type': expected_type,
            'name': name,
            'required': required,
            'validator': validator
        })
        return self
    
    def parse(self, context: QueryPrimitive, arguments: Arguments, all_data: ObjectList) -> ParsedArguments:
        """Parse and validate arguments according to the specifications."""
        # Process arguments: run chains if expected type isn't Chain but argument is Chain

        if self.context_spec is not None:
            if self.context_spec['type'] is not None:
                if not isinstance(context, self.context_spec['type']):
                    raise TypeError(f"Expected context to be of type {self.context_spec['type'].__name__}, got {type(context).__name__}: {context}")
            if self.context_spec['validator'] is not None:
                if not self.context_spec['validator'](context):
                    raise TypeError(f"Context failed validation: {context}")
        else:
            if not isinstance(context, ObjectList):
                raise TypeError(f"Expected context to be an ObjectList, got {type(context)}: {context}")

        processed_args = []
        for i, arg in enumerate(arguments):
            if i < len(self.argument_specs):
                spec = self.argument_specs[i]
                expected_type = spec['type']
                
                # If we expect something other than Chain but got a Chain, run it
                if expected_type != Chain and isinstance(arg, Chain):
                    processed_arg = arg.run(context, all_data)
                    processed_args.append(processed_arg)
                else:
                    processed_args.append(arg)
            else:
                processed_args.append(arg)
        
        if self.allow_variable:
            # Handle variable arguments
            if len(processed_args) < self.min_count:
                raise ValueError(f"Expected at least {self.min_count} arguments, got {len(processed_args)}: {processed_args}")
            if self.max_count is not None and len(processed_args) > self.max_count:
                raise ValueError(f"Expected at most {self.max_count} arguments, got {len(processed_args)}: {processed_args}")
            
            # Validate each argument using the first spec (assuming all args have same type/validator)
            if self.argument_specs:
                spec = self.argument_specs[0]
                for i, arg in enumerate(processed_args):
                    if spec['validator'] is not None:
                        if not spec['validator'](arg):
                            raise TypeError(f"Argument {i} failed validation: {arg}")
                    elif spec['type'] is not None:
                        if not isinstance(arg, spec['type']):
                            raise TypeError(f"Argument {i} must be of type {spec['type'].__name__}, got {type(arg).__name__}: {arg}")
            
            # Build result with positional arguments
            result_kwargs = {}
            for i, arg in enumerate(processed_args):
                result_kwargs[f'arg_{i}'] = arg
            return ParsedArguments(**result_kwargs)
        else:
            # Handle fixed arguments
            expected_count = len([spec for spec in self.argument_specs if spec['required']])
            if len(processed_args) < expected_count:
                raise ValueError(f"Expected at least {expected_count} arguments, got {len(processed_args)}: {processed_args}")
            if len(processed_args) > len(self.argument_specs):
                raise ValueError(f"Expected at most {len(self.argument_specs)} arguments, got {len(processed_args)}: {processed_args}")
            
            # Build result object
            result_kwargs = {}
            for i, spec in enumerate(self.argument_specs):
                if i < len(processed_args):
                    arg = processed_args[i]
                    # Validate using validator if provided, otherwise use type
                    if spec['validator'] is not None:
                        if not spec['validator'](arg):
                            raise TypeError(f"Argument '{spec['name']}' failed validation: {arg}")
                    elif spec['type'] is not None:
                        if not isinstance(arg, spec['type']):
                            raise TypeError(f"Argument '{spec['name']}' must be of type {spec['type'].__name__}, got {type(arg).__name__}: {arg}")
                    result_kwargs[spec['name']] = arg
                else:
                    # Handle optional arguments that weren't provided
                    if not spec['required']:
                        result_kwargs[spec['name']] = None
                    else:
                        # This shouldn't happen due to the count check above, but just in case
                        raise ValueError(f"Missing required argument '{spec['name']}'")
            
            return ParsedArguments(**result_kwargs)

def run_all_if_possible(context: ObjectList, arguments: Arguments, all_data: ObjectList) -> list[QueryPrimitive]:
    result = []
    for arg in arguments:
        if isinstance(arg, Chain):
            # Run the chain and add the result
            result.append(arg.run(context, all_data))
        else:
            # Leave primitives as they are
            result.append(arg)
    return result

def deduplicate_if_list(item: SAType) -> Optional[SAType]:
    assert is_valid_sa_type(item), f"deduplicate_if_list item must be a valid SA type, got {type(item)}: {item}"
    if isinstance(item, list):
        if len(set(item)) != 1:
            return None
        return item[0]
    return item

def equals_operator_runner(context: ObjectList, arguments: Arguments, all_data: ObjectList) -> QueryType:
    parser = ArgumentParser()
    parser.add_arg(is_valid_sa_type, "left")
    parser.add_arg(is_valid_sa_type, "right")
    args = parser.parse(context, arguments, all_data)
    
    debug("context objects count:", len(context.objects))
    debug("left:", args.left)
    debug("right:", args.right)
    
    left = deduplicate_if_list(args.left)
    right = deduplicate_if_list(args.right) 
    
    debug("deduplicated left:", left)
    debug("deduplicated right:", right)
    
    if left is None or right is None:
        debug("one or both sides are None, returning False")
        return False
    
    result = left == right
    debug("comparison result:", result)
    return result
EqualsOperator = Operator(
    name="equals",
    runner=equals_operator_runner
)

def get_field_operator_runner(context: ObjectList, arguments: Arguments, all_data: ObjectList) -> QueryType:
    parser = ArgumentParser()
    parser.add_arg(str, "field_name")
    args = parser.parse(context, arguments, all_data)
    
    debug("context objects count:", len(context.objects))
    debug("field name:", args.field_name)
    
    result = []
    for obj in context.objects:
        if obj.has_field(args.field_name):
            field_value = obj.get_field(args.field_name, all_data)
            debug(f"object {obj.id} has field '{args.field_name}':", field_value)
            result.append(field_value)
        else:
            debug(f"object {obj.id} missing field '{args.field_name}'")
    
    debug("total results found:", len(result))
    
    if len(result) == 1:
        debug("single result, returning:", result[0])
        return result[0]
    if len(result) == 0:
        debug("no results found, returning None")
        return None
    
    debug("multiple results, returning list:", result)
    return result
GetFieldOperator = Operator(
    name="get_field",
    runner=get_field_operator_runner
)

def filter_operator_runner(context: ObjectList, arguments: Arguments, all_data: ObjectList) -> QueryType:
    parser = ArgumentParser()
    parser.add_arg(Chain, "chain")
    parser.add_arg(str, "mode", required=False)
    args = parser.parse(context, arguments, all_data)
    
    debug("starting filter operation")
    debug("context has", len(context.objects), "objects")
    debug("filter chain:", args.chain)
    debug("filter mode:", args.mode)
    if args.mode == None or args.mode == "grouped":
        grouped_context = context.group_by_id_types()
    elif args.mode == "all":
        grouped_context = [ObjectList([obj]) for obj in context.objects]
    debug("grouped context into", len(grouped_context), "groups")
    
    survivors: list[SAObject] = []
    for i, object_list in enumerate(grouped_context):
        debug(f"processing group {i+1}/{len(grouped_context)} with {len(object_list.objects)} objects")
        chain_result = args.chain.run(object_list, all_data)
        debug(f"chain result for group {i+1}:", chain_result)
        
        assert isinstance(chain_result, bool), f"Filter operator chain result must be a boolean, got {type(chain_result)}: {chain_result}"
        if chain_result:
            debug(f"group {i+1} passed filter, adding {len(object_list.objects)} objects")
            survivors.extend(object_list.objects)
        else:
            debug(f"group {i+1} failed filter, skipping")
    
    debug("filter complete, survivors:", len(survivors))
    return ObjectList(survivors)
FilterOperator = Operator(
    name="filter",
    runner=filter_operator_runner
)

def select_operator_runner(context: ObjectList, arguments: Arguments, all_data: ObjectList) -> QueryType:
    parser = ArgumentParser()
    parser.allow_variable_args(min_count=1)
    parser.add_arg(Chain, "chain")  # This spec will be used to validate all arguments
    args = parser.parse(context, arguments, all_data)
    
    debug("starting select operation")
    debug("context has", len(context.objects), "objects")
    debug("select chains count:", len(args))
    
    # Custom validation: all inputs must be Chains that start with get_field operators
    for i, chain in enumerate(args):
        debug(f"validating chain {i+1}:", chain)
        assert isinstance(chain, Chain), f"Select operator argument {i} must be a chain, got {type(chain)}: {chain}"
        assert len(chain.operator_nodes) > 0, f"Not enough operator nodes in chain {i}: {chain}"
        assert chain.operator_nodes[0].operator == GetFieldOperator, f"Select operator argument {i} must start with a get_field operator, got {chain.operator_nodes[0].operator}"
        debug(f"chain {i+1} validation passed")
    
    result: list[SAObject] = []
    for i, object in enumerate(context.objects):
        debug(f"processing object {i+1}/{len(context.objects)}: {object.id}")
        new_object = object.empty_copy()
        taken_field_names: set[str] = set()
        for j, chain in enumerate(args):
            field_value = chain.run(ObjectList([object]), all_data)
            if field_value is None:
                continue
            get_field_operator: OperatorNode = chain.operator_nodes[0]
            field_name = get_field_operator.arguments[0]
            field_name_to_use = field_name
            next_number_to_use = 2
            while field_name_to_use in taken_field_names:
                field_name_to_use = f"{field_name}_{next_number_to_use}"
                next_number_to_use += 1
            taken_field_names.add(field_name_to_use)
            debug(f"  chain {j+1} extracted field '{field_name}':", field_value)
            new_object.set_field(field_name_to_use, field_value)
        result.append(new_object)
        debug(f"created new object with {len(new_object.properties)} properties")
    
    debug("select complete, created", len(result), "objects")
    return ObjectList(result)
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
    parser = ArgumentParser()
    parser.add_arg(str, "value")
    parser.validate_context(is_valid_sa_type)
    args = parser.parse(context, arguments, all_data)
    
    debug("starting includes operation")
    debug("context:", context)
    debug("searching for value:", args.value)
    debug("context type:", type(context).__name__)
    
    assert not isinstance(context, dict), f"includes operator context must not be a dict, got {type(context)}: {context}"
    
    if not isinstance(context, list):
        debug("context is not a list, doing direct comparison")
        result = args.value == context
        debug("direct comparison result:", result)
        return result
    
    debug("context is a list, flattening and searching")
    flattened = flatten_fully(context)
    debug("flattened context:", flattened)
    
    result = args.value in flattened
    debug("inclusion check result:", result)
    return result
IncludesOperator = Operator(
    name="includes",
    runner=includes_operator_runner
)

def flatten_operator_runner(context: SAType, arguments: Arguments, all_data: ObjectList) -> QueryType:
    parser = ArgumentParser()
    parser.validate_context(is_valid_sa_type)
    parser.parse(context, arguments, all_data)
    
    debug("starting flatten operation")
    debug("context:", context)
    debug("context type:", type(context).__name__)
    
    assert not isinstance(context, dict), f"flatten operator context must not be a dict, got {type(context)}: {context}"
    
    if not isinstance(context, list):
        debug("context is not a list, wrapping in list")
        result = [context]
        debug("result:", result)
        return result
    
    if len(context) == 0:
        debug("context is empty list, returning empty list")
        return []
    
    debug("context is list with", len(context), "items")
    if not all(isinstance(item, list) for item in context):
        debug("not all items are lists, returning as-is")
        debug("result:", context)
        return context
    
    debug("all items are lists, flattening")
    result = [item for sublist in context for item in sublist]
    debug("flattened result:", result)
    return result
FlattenOperator = Operator(
    name="flatten",
    runner=flatten_operator_runner
)

def unique_operator_runner(context: SAType, arguments: Arguments, all_data: ObjectList) -> QueryType:
    parser = ArgumentParser()
    parser.validate_context(is_valid_sa_type)
    parser.parse(context, arguments, all_data)
    
    debug("starting unique operation")
    debug("context:", context)
    debug("context type:", type(context).__name__)
    
    if not isinstance(context, list):
        debug("context is not a list, wrapping in list")
        result = [context]
        debug("result:", result)
        return result
    
    debug("context is list with", len(context), "items")
    debug("original items:", context)
    
    unique_items = list(set(context))
    debug("unique items:", unique_items)
    debug("removed", len(context) - len(unique_items), "duplicates")
    
    return unique_items
UniqueOperator = Operator(
    name="unique",
    runner=unique_operator_runner
)

def count_operator_runner(context: QueryPrimitive, arguments: Arguments, all_data: ObjectList) -> QueryType:
    parser = ArgumentParser()
    parser.validate_context(is_valid_primitive)
    parser.parse(context, arguments, all_data)
    
    debug("starting count operation")
    debug("context:", context)
    debug("context type:", type(context).__name__)
    
    if isinstance(context, ObjectList):
        count = len(context.objects)
        debug("context is ObjectList with", count, "objects")
        return count
    
    if isinstance(context, list):
        count = len(context)
        debug("context is list with", count, "items")
        return count
    
    debug("context is primitive, returning 1")
    return 1
CountOperator = Operator(
    name="count",
    runner=count_operator_runner
)

all_operators = [
    EqualsOperator,
    GetFieldOperator,
    FilterOperator,
    SelectOperator,
    IncludesOperator,
    FlattenOperator,
    UniqueOperator,
    CountOperator
]