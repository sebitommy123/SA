from dataclasses import dataclass
from typing import Optional
import sys
from sa.core.object_list import ObjectList
from sa.query_language.query_scope import Scopes
from sa.shell.provider_manager import Providers
from sa.query_language.query_state import QueryState
from sa.query_language.errors import QueryArea, QueryAreaTerms, QueryError, print_error_area, assert_query
from sa.query_language.types import QueryType
from sa.query_language.chain import Chain, OperatorNode
from sa.query_language.operators import all_operators
from sa.query_language.operators.comparison import EqualsOperator, RegexEqualsOperator
from sa.query_language.operators.logical import AndOperator, OrOperator
from sa.query_language.operators.field_operations import GetFieldOperator
from sa.query_language.operators.list_operations import ForeachOperator, FilterOperator, SelectOperator
from sa.query_language.operators.slice import SliceOperator

Tokens = list[str]


def get_tokens_from_query(query: str) -> Tokens:
    tokens = []
    current_alphanumeric = ''
    
    for i, char in enumerate(query):
        if char.isalnum() or char == '_':
            current_alphanumeric += char
        else:
            if current_alphanumeric:
                tokens.append(current_alphanumeric)
                current_alphanumeric = ''
            
            # Handle negative numbers
            if char == '-' and (i == 0 or not query[i-1].isalnum() and query[i-1] != '_' and query[i-1] != ']' and query[i-1] != ')'):
                # This is a negative sign, not a minus operator
                current_alphanumeric = '-'
            else:
                tokens.append(char)
    
    # Don't forget the last alphanumeric sequence
    if current_alphanumeric:
        tokens.append(current_alphanumeric)

    assert_query("".join(tokens) == query, f"Expected query to be the same, got {query} and {''.join(tokens)}")
    
    return tokens

def accumulate_identifier_tokens(tokens: Tokens, start_index: int, allowed_chars: str = "alnum_-") -> tuple[str, int]:
    """Accumulate consecutive tokens based on allowed character types.

    Args:
        tokens: List of tokens to scan
        start_index: Index to start scanning from
        allowed_chars: String specifying allowed character types:
            - 'alnum': alphanumeric characters
            - '_': underscore
            - '-': dash
            - '*': asterisk
            - 'alnum_-': alphanumeric + underscore + dash (default)
            - 'alnum_*': alphanumeric + underscore + asterisk
            - 'alnum_-*': alphanumeric + underscore + dash + asterisk
            - 'alnum_': alphanumeric + underscore only
            - 'alnum': alphanumeric only
            - etc.

    Returns the joined identifier string and the index after the last consumed token.
    """
    scan_index = start_index
    accumulated_tokens: list[str] = []
    
    # Parse allowed character types
    allow_alnum = 'alnum' in allowed_chars
    allow_underscore = '_' in allowed_chars
    allow_dash = '-' in allowed_chars
    allow_asterisk = '*' in allowed_chars
    allow_pound = '#' in allowed_chars
    allow_at = '@' in allowed_chars
    
    while scan_index < len(tokens):
        next_token = tokens[scan_index]
        
        # Check for dash token
        if next_token == "-" and allow_dash:
            accumulated_tokens.append(next_token)
            scan_index += 1
            continue
            
        # Check for asterisk token
        if next_token == "*" and allow_asterisk:
            accumulated_tokens.append(next_token)
            scan_index += 1
            continue

        # Check for pound token
        if next_token == "#" and allow_pound:
            accumulated_tokens.append(next_token)
            scan_index += 1
            continue

        # Check for at token
        if next_token == "@" and allow_at:
            accumulated_tokens.append(next_token)
            scan_index += 1
            continue
            
        # Check for alphanumeric token (with optional underscore)
        if next_token and allow_alnum:
            if allow_underscore:
                if all(ch.isalnum() or ch == '_' for ch in next_token):
                    accumulated_tokens.append(next_token)
                    scan_index += 1
                    continue
            else:
                if all(ch.isalnum() for ch in next_token):
                    accumulated_tokens.append(next_token)
                    scan_index += 1
                    continue
        break

    assert_query(len(accumulated_tokens) > 0, f"Expected identifier at index {start_index}")
    return ''.join(accumulated_tokens), scan_index

def get_token_arguments(current_area: QueryArea, tokens: Tokens, current_token_index: int, paren_open: str, paren_close: str, argument_separator: Optional[str]) -> tuple[list[Tokens], int, list[QueryArea]]:
    assert_query(tokens[current_token_index] == paren_open, f"Expected {paren_open} at index {current_token_index}, got {tokens[current_token_index]}")
    current_token_index += 1
    num_open_parens = 1
    arguments: list[Tokens] = []
    argument_areas: list[QueryArea] = []
    current_argument: Tokens = []
    current_area = current_area[current_token_index:current_token_index]
    
    while current_token_index < len(tokens):
        token = tokens[current_token_index]
        
        # Check for argument separator (only at top level)
        if token == argument_separator and num_open_parens == 1:
            arguments.append(current_argument)
            argument_areas.append(current_area)
            current_token_index += 1
            current_argument = []
            current_area = current_area[current_token_index:current_token_index]
            continue
        
        # Check for parentheses
        if token == paren_open:
            num_open_parens += 1
        elif token == paren_close:
            num_open_parens -= 1
            assert_query(num_open_parens >= 0, f"Unexpected closing parenthesis at index {current_token_index}")
            if num_open_parens == 0:
                # Add the last argument and break
                arguments.append(current_argument)
                argument_areas.append(current_area)
                break
        
        # Add token to current argument
        current_argument.append(token)
        current_token_index += 1
        current_area.end_index += 1
    
    assert_query(num_open_parens == 0, f"Couldn't find a matching closing parenthesis for paren at index {current_token_index}")
    return arguments, current_token_index, argument_areas

def trim_tokens(tokens: Tokens, area: QueryArea) -> tuple[Tokens, QueryArea]:
    area = area.clone()
    assert_query(area.terms == QueryAreaTerms.TOKEN, f"Expected TOKEN area, got {area.terms}")
    # Remove leading whitespace tokens
    while tokens and tokens[0].isspace():
        tokens.pop(0)
        area.start_index += 1
    
    # Remove trailing whitespace tokens
    while tokens and tokens[-1].isspace():
        tokens.pop()
        area.end_index -= 1
    return tokens, area


def get_parser_results(results: list[QueryType]) -> QueryType:
    if all(isinstance(result, OperatorNode) for result in results):
        return Chain(results)
    else:
        assert_query(len(results) != 0, "Empty input?")
        assert_query(len(results) <= 1, f"Expected 1 result, got {len(results)}")
        return results[0]


def parse_tokens_into_querytype(all_tokens: Tokens, tokens: Tokens, area: QueryArea) -> QueryType:
    current_state = 'start'
    string_state_quote_type = None
    string_state_string = ''
    current_token_index = 0
    results: list[QueryType] = []

    assert_query(area.terms == QueryAreaTerms.TOKEN, f"Expected TOKEN area, got {area.terms}")
    tokens, area = trim_tokens(tokens, area)

    try:
        while current_token_index < len(tokens):
            current_token_index_at_start = current_token_index
            token = tokens[current_token_index]
            token_after = tokens[current_token_index + 1] if current_token_index + 1 < len(tokens) else None
            
            # Skip whitespace tokens when not in string state
            if current_state != 'string' and token.isspace():
                current_token_index += 1
                continue
                
            if current_state == 'start':
                if token == "*":
                    assert_query(current_token_index == 0, f"Expected * at start of query, got {token} at index {current_token_index}")
                    current_token_index += 1
                elif token == ".":
                    current_state = 'after_dot'
                    current_token_index += 1
                elif token.isdigit():
                    results.append(int(token))
                    current_token_index += 1
                elif token == '"' or token == "'":
                    string_state_quote_type = token
                    current_state = 'string'
                    current_token_index += 1
                elif token == "true" or token == "false":
                    results.append(token == "true")
                    current_token_index += 1
                elif token == "=":
                    if token_after == "=":
                        # == operator
                        left = get_parser_results(results)
                        right = parse_tokens_into_querytype(all_tokens, tokens[current_token_index + 2:], area[current_token_index + 2:])
                        return Chain([OperatorNode(operator=EqualsOperator, arguments=[left, right], area=area)])
                    elif token_after == "~":
                        # =~ operator (regex)
                        left = get_parser_results(results)
                        right = parse_tokens_into_querytype(all_tokens, tokens[current_token_index + 2:], area[current_token_index + 2:])
                        return Chain([OperatorNode(operator=RegexEqualsOperator, arguments=[left, right], area=area)])
                    else:
                        raise QueryError(f"Expected == or =~, got just one =")
                elif token == "&":
                    if token_after == "&":
                        # && operator
                        left = get_parser_results(results)
                        right = parse_tokens_into_querytype(all_tokens, tokens[current_token_index + 2:], area[current_token_index + 2:])
                        return Chain([OperatorNode(operator=AndOperator, arguments=[left, right])], area=area)
                    else:
                        raise QueryError(f"Expected &&, got just one &")
                elif token == "|":
                    if token_after == "|":
                        # || operator
                        left = get_parser_results(results)
                        right = parse_tokens_into_querytype(all_tokens, tokens[current_token_index + 2:], area[current_token_index + 2:])
                        return Chain([OperatorNode(operator=OrOperator, arguments=[left, right])], area=area)
                    else:
                        raise QueryError(f"Expected ||, got just one |")
                elif token == "[":
                    if token_after == "[":
                        operator_token_arguments, close_paren_index, argument_areas = get_token_arguments(area, tokens, current_token_index+1, "[", "]", ",")
                        token_after_close_paren = tokens[close_paren_index + 1] if close_paren_index + 1 < len(tokens) else None
                        if token_after_close_paren != "]":
                            raise QueryError(f"Expected ]], got ]{token_after_close_paren}")
                        new_area = area[current_token_index:close_paren_index+2]
                        inside_querytypes: list[QueryType] = [parse_tokens_into_querytype(all_tokens, inside_tokens, arg_area) for inside_tokens, arg_area in zip(operator_token_arguments, argument_areas)]
                        results.append(OperatorNode(operator=SelectOperator, arguments=inside_querytypes, area=new_area))
                        current_token_index = close_paren_index + 2
                    else:
                        # Check if this is slice syntax [::] or filter syntax [|]
                        operator_token_arguments, close_paren_index, argument_areas = get_token_arguments(area, tokens, current_token_index, "[", "]", None)
                        new_area = area[current_token_index:close_paren_index+1]

                        if len(operator_token_arguments) == 0:
                            raise QueryError("Empty brackets are meaningless, e.g. []. Wtf do I do with this?")
                        
                        # Check if this looks like slice syntax (contains colons and simple numbers)
                        is_slice_syntax = False
                        if len(operator_token_arguments) == 1:
                            potential_parts = "".join(operator_token_arguments[0]).split(":")
                            is_slice_syntax = all(part.isdigit() or part == "" for part in potential_parts) and (1 <= len(potential_parts) <= 3)
                            
                        if is_slice_syntax:
                            arguments = [int(part) if part.isdigit() else "" for part in potential_parts]
                            results.append(OperatorNode(operator=SliceOperator, arguments=arguments, area=new_area))
                            current_token_index = close_paren_index + 1
                        else:
                            assert_query(len(operator_token_arguments) >= 1 and len(operator_token_arguments) <= 2, f"Expected 1 or 2 arguments, got {len(operator_token_arguments)}")
                            inside_querytypes: list[QueryType] = [parse_tokens_into_querytype(all_tokens, inside_tokens, arg_area) for inside_tokens, arg_area in zip(operator_token_arguments, argument_areas)]
                            results.append(OperatorNode(operator=FilterOperator, arguments=inside_querytypes, area=new_area))
                            current_token_index = close_paren_index + 1
                elif token == "{":
                    # This is shorthand for .select(chain, chain, chain, ...)
                    operator_token_arguments, close_paren_index, argument_areas = get_token_arguments(area, tokens, current_token_index, "{", "}", ",")
                    new_area = area[current_token_index:close_paren_index+1]
                    assert_query(len(operator_token_arguments) > 0, f"Expected at least 1 argument, got {len(operator_token_arguments)}")
                    inside_querytypes: list[QueryType] = [parse_tokens_into_querytype(all_tokens, inside_tokens, arg_area) for inside_tokens, arg_area in zip(operator_token_arguments, argument_areas)]
                    results.append(OperatorNode(operator=ForeachOperator, arguments=inside_querytypes, area=new_area))
                    current_token_index = close_paren_index + 1
                elif token == "#":
                    # #<id> is shorthand for [.__id__ == <id>]
                    accumulated_id, scan_index = accumulate_identifier_tokens(tokens, current_token_index + 1, "alnum_-*")
                    if "*" in accumulated_id:
                        accumulated_id = accumulated_id.replace("*", ".*")
                        accumulated_id = f"^{accumulated_id}$"
                        results.append(parse_query_into_querytype(
                            f"[.__id__ =~ '{accumulated_id}']"
                        ).operator_nodes[0])
                    else:
                        results.append(parse_query_into_querytype(
                            f".get_by_id('{accumulated_id}')"
                        ).operator_nodes[0])
                    current_token_index = scan_index
                elif token == "@":
                    # @<source> is shorthand for [.__source__ == <source>]
                    accumulated_source, scan_index = accumulate_identifier_tokens(tokens, current_token_index + 1, "alnum_-")
                    results.append(parse_query_into_querytype(
                        f".filter_by_source('{accumulated_source}')"
                    ).operator_nodes[0])
                    current_token_index = scan_index
                else:
                    assert_query(current_token_index == 0, f"Can only do syntax-free shorthand type filtering at the beginning, got {token} at index {current_token_index}")
                    # Accumulate type tokens to support hyphenated types
                    accumulated_type, scan_index = accumulate_identifier_tokens(tokens, current_token_index)
                    # Is shorthand for .filter(.get_field("__types__").includes(token))
                    results.append(parse_query_into_querytype(
                        f".filter_by_type('{accumulated_type}')"
                    ).operator_nodes[0])
                    current_token_index = scan_index
            elif current_state == 'after_dot':
                if token_after == "(":
                    operator = next((op for op in all_operators if op.name == token), None)
                    assert_query(operator, f"Invalid operator: {token}")
                    operator_token_arguments, close_paren_index, argument_areas = get_token_arguments(area, tokens, current_token_index + 1, "(", ")", ",")
                    new_area = area[current_token_index:close_paren_index+1]
                    if close_paren_index == current_token_index + 2:
                        parsed_arguments = []
                    else:
                        parsed_arguments: list[QueryType] = [parse_tokens_into_querytype(all_tokens, arg, arg_area) for arg, arg_area in zip(operator_token_arguments, argument_areas)]
                    results.append(OperatorNode(operator=operator, arguments=parsed_arguments, area=new_area))
                    current_token_index = close_paren_index + 1
                    current_state = 'start'
                else:
                    # This is shorthand for .get_field(token)
                    # e.g. .app -> .get_field("app")
                    # Accumulate identifier tokens to support hyphenated field names
                    if token == "#":
                        field = "__id__"
                        next_index = current_token_index + 1
                    elif token == "@":
                        field = "__source__"
                        next_index = current_token_index + 1
                    else:
                        accumulated_field, next_index = accumulate_identifier_tokens(tokens, current_token_index, "alnum_-*")
                        # Convert * to .* for regex wildcard matching
                        field = accumulated_field.replace("*", ".*")

                    return_none_if_missing = True
                    if len(tokens) > next_index and tokens[next_index] == "!":
                        return_none_if_missing = False
                        next_index += 1
                    
                    return_all_values = False
                    if len(tokens) > next_index + 1 and tokens[next_index] == "[" and tokens[next_index + 1] == "]":
                        return_all_values = True
                        next_index += 2

                    new_area = area[current_token_index-1:next_index]
                    results.append(OperatorNode(operator=GetFieldOperator, arguments=[field, return_none_if_missing, return_all_values], area=new_area))
                    current_token_index = next_index
                    current_state = 'start'
            elif current_state == 'string':
                if token == string_state_quote_type:
                    results.append(string_state_string)
                    current_token_index += 1
                    current_state = 'start'
                else:
                    string_state_string += token
                    current_token_index += 1
            else:
                raise QueryError(f"Invalid state: {current_state}")
            
            assert_query(current_token_index > current_token_index_at_start, f"Token index didn't move forward from {current_token_index_at_start} to {current_token_index} for token {token} in state {current_state}")
    except Exception as e:
        print("While parsing this area:")
        print_error_area(area)
        raise e

    return get_parser_results(results)

def parse_query_into_querytype(query: str) -> QueryType:
    tokens = get_tokens_from_query(query)
    result = None
    try:
        result = parse_tokens_into_querytype(tokens, tokens, QueryArea(0, len(tokens), QueryAreaTerms.TOKEN, tokens))
    except Exception as e:
        raise e
    return result

def run_query(query: str, query_state: QueryState) -> QueryType:
    try:
        parsed_query = parse_query_into_querytype(query)
        if isinstance(parsed_query, Chain):
            result = parsed_query.run(query_state.all_data, query_state)
        else:
            result = parsed_query
    except QueryError as e:
        result = f"Error: {str(e)}"
    except Exception as e:
        raise e
    return result

def execute_query(query: str, providers: Providers) -> tuple[QueryType, QueryState]:
    providers.all_data.reset()
    query_state = QueryState.setup(providers)
    return run_query(query, query_state), query_state

def execute_query_fully(query: str, providers: Providers) -> QueryType:
    # Keep executing the query
    while True:
        result, final_query_state = execute_query(query, providers)
        missing_scopes = final_query_state.final_needed_scopes.minus_scopes(providers.downloaded_scopes)

        # Stop once executing the query doesn't return any missing scopes
        if not missing_scopes.scopes:
            break

        # Each time, download all the missing scopes
        for scope in missing_scopes.scopes:
            providers.download_scope(scope, final_query_state.id_types)

        # If any of the missing scopes can't be downloaded, we can't execute the query
        still_missing_scopes = final_query_state.final_needed_scopes.minus_scopes(providers.downloaded_scopes)
        if still_missing_scopes.scopes:
            return f"Error: Failed to download all scopes: {still_missing_scopes}"
    
    return result
