from __future__ import annotations
from typing import TYPE_CHECKING
import re
from sa.query_language.argument_parser import ArgumentParser
from sa.query_language.validators import anything
from sa.core.types import is_valid_sa_type
from sa.query_language.errors import QueryError
from sa.query_language.types import AbsorbingNone, AbsorbingNoneType
from sa.query_language.chain import Operator

if TYPE_CHECKING:
    from sa.query_language.types import QueryType, Arguments, QueryContext
    from sa.core.object_list import ObjectList

def equals_operator_runner(context: ObjectList, arguments: Arguments, all_data: ObjectList) -> QueryType:
    parser = ArgumentParser("equals")
    parser.validate_context(anything, "")
    parser.add_arg(is_valid_sa_type, "left", "Left side of equals must be a valid SA type")
    parser.add_arg(is_valid_sa_type, "right", "Right side of equals must be a valid SA type")
    context, args = parser.parse(context, arguments, all_data)
    
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
    context, args = parser.parse(context, arguments, all_data)
    
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
