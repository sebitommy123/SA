from __future__ import annotations
from typing import Callable, Any, TYPE_CHECKING, Optional, List, Type, Union
import re

if TYPE_CHECKING:
    from sa.query_language.types import QueryType, Arguments, QueryContext
    from sa.query_language.chain import Operator, OperatorNode, Chain
    from sa.core.object_list import ObjectList
    from sa.query_language.validators import is_valid_primitive

from sa.query_language.validators import anything, either, is_absorbing_none, is_dict, is_list, is_object_grouping, is_object_list, is_single_object_list
from sa.query_language.errors import QueryError, assert_query
from sa.core.object_list import ObjectList
from sa.core.sa_object import SAObject
from sa.core.object_grouping import ObjectGrouping
from sa.core.types import SAType
from sa.core.types import is_valid_sa_type
from sa.query_language.types import AbsorbingNone, AbsorbingNoneType, QueryType, Arguments, QueryContext
from sa.query_language.chain import Operator, Chain
from sa.query_language.validators import is_valid_primitive, is_valid_querytype
from dataclasses import dataclass

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
        assert_query(self.context_spec is not None, f"{self.operator_name} operator must validate context")
        if not self.context_spec['validator'](context):
            if isinstance(context, ObjectList) and len(context.objects) == 1 and self.context_spec['validator'](context.objects[0]):
                context = context.objects[0]
            else:
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
                if isinstance(arg, ObjectList) and len(arg.objects) == 1 and spec['validator'](arg.objects[0]):
                    arg = arg.objects[0]
                else:
                    raise QueryError(f"{self.operator_name} operator, argument '{spec['name']}' can't be {type(arg).__name__}. {spec['description']}")
            result_kwargs[spec['name']] = arg
            
        return context, ParsedArguments(**result_kwargs)

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
