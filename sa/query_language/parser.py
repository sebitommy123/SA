from typing import Optional
from .main import QueryType, Chain, OperatorNode
from .operators import EqualsOperator, RegexEqualsOperator, FilterOperator, GetFieldOperator, SelectOperator, SliceOperator, all_operators

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
    
    return tokens

def get_token_arguments(tokens: Tokens, current_token_index: int, paren_open: str, paren_close: str, argument_separator: Optional[str]) -> tuple[Tokens, int]:
    assert tokens[current_token_index] == paren_open, f"Expected {paren_open} at index {current_token_index}, got {tokens[current_token_index]}"
    current_token_index += 1
    num_open_parens = 1
    arguments: list[Tokens] = []
    current_argument: Tokens = []
    
    while current_token_index < len(tokens):
        token = tokens[current_token_index]
        
        # Check for argument separator (only at top level)
        if token == argument_separator and num_open_parens == 1:
            arguments.append(current_argument)
            current_argument = []
            current_token_index += 1
            continue
        
        # Check for parentheses
        if token == paren_open:
            num_open_parens += 1
        elif token == paren_close:
            num_open_parens -= 1
            assert num_open_parens >= 0, f"Unexpected closing parenthesis at index {current_token_index}"
            if num_open_parens == 0:
                # Add the last argument and break
                arguments.append(current_argument)
                break
        
        # Add token to current argument
        current_argument.append(token)
        current_token_index += 1
    
    assert num_open_parens == 0, f"Couldn't find a matching closing parenthesis for paren at index {current_token_index}"
    return arguments, current_token_index

def trim_tokens(tokens: Tokens) -> Tokens:
    # Remove leading whitespace tokens
    while tokens and tokens[0].isspace():
        tokens.pop(0)
    
    # Remove trailing whitespace tokens
    while tokens and tokens[-1].isspace():
        tokens.pop()
    
    return tokens


def get_parser_results(results: list[QueryType]) -> QueryType:
    if all(isinstance(result, OperatorNode) for result in results):
        return Chain(results)
    else:
        assert len(results) != 0, "Empty input?"
        assert len(results) <= 1, f"Expected 1 result, got {len(results)}"
        return results[0]


def parse_tokens_into_querytype(tokens: Tokens) -> QueryType:
    current_state = 'start'
    string_state_quote_type = None
    string_state_string = ''
    current_token_index = 0
    results: list[QueryType] = []

    tokens = trim_tokens(tokens)

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
                assert current_token_index == 0, f"Expected * at start of query, got {token} at index {current_token_index}"
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
                    right = parse_tokens_into_querytype(tokens[current_token_index + 2:])
                    return Chain([OperatorNode(operator=EqualsOperator, arguments=[left, right])])
                elif token_after == "~":
                    # =~ operator (regex)
                    left = get_parser_results(results)
                    right = parse_tokens_into_querytype(tokens[current_token_index + 2:])
                    return Chain([OperatorNode(operator=RegexEqualsOperator, arguments=[left, right])])
                else:
                    raise ValueError(f"Expected == or =~, got just one =")
            elif token == "[":
                # Check if this is slice syntax [::] or filter syntax [|]
                operator_token_arguments, close_paren_index = get_token_arguments(tokens, current_token_index, "[", "]", "|")
                
                # Check if this looks like slice syntax (contains colons and simple numbers)
                if len(operator_token_arguments) == 1:
                    inside_tokens = operator_token_arguments[0]
                    
                    # Check if it's a single index (no colons, just a number)
                    if ":" not in inside_tokens and len(inside_tokens) == 1 and (inside_tokens[0].isdigit() or (inside_tokens[0].startswith('-') and inside_tokens[0][1:].isdigit())):
                        # Single index syntax: [0] -> [0:1], [-1] -> [-1:]
                        index = int(inside_tokens[0])
                        if index >= 0:
                            results.append(OperatorNode(operator=SliceOperator, arguments=[index, index + 1]))
                        else:
                            results.append(OperatorNode(operator=SliceOperator, arguments=[index, None]))
                        current_token_index = close_paren_index + 1
                        continue
                    
                    # Check if the content contains colons and looks like slice syntax
                    if ":" in inside_tokens:
                        # Split by colons and check if each part is a simple number or empty
                        colon_parts = []
                        current_part = []
                        for t in inside_tokens:
                            if t == ":":
                                colon_parts.append(current_part)
                                current_part = []
                            else:
                                current_part.append(t)
                        colon_parts.append(current_part)  # Add the last part
                        
                        # Check if we have at most 2 colons and each part is simple
                        if len(colon_parts) <= 3:  # 0, 1, or 2 colons
                            is_slice_syntax = True
                            for part in colon_parts:
                                if part:  # Non-empty part
                                    # Check if it's a simple number (single token that's a digit or negative number)
                                    if len(part) != 1 or not (part[0].isdigit() or (part[0].startswith('-') and part[0][1:].isdigit())):
                                        is_slice_syntax = False
                                        break
                                # Empty parts are allowed (None values)
                            
                            if is_slice_syntax:
                                # This is slice syntax, parse the arguments
                                slice_args = []
                                for part in colon_parts:
                                    if part:
                                        slice_args.append(int(part[0]))
                                    else:
                                        slice_args.append(None)
                                
                                results.append(OperatorNode(operator=SliceOperator, arguments=slice_args))
                                current_token_index = close_paren_index + 1
                                continue
                
                # If not slice syntax, treat as filter syntax
                assert len(operator_token_arguments) >= 1 and len(operator_token_arguments) <= 2, f"Expected 1 or 2 arguments, got {len(operator_token_arguments)}"
                inside_querytypes: list[QueryType] = [parse_tokens_into_querytype(inside_tokens) for inside_tokens in operator_token_arguments]
                results.append(OperatorNode(operator=FilterOperator, arguments=inside_querytypes))
                current_token_index = close_paren_index + 1
            elif token == "{":
                # This is shorthand for .select(chain, chain, chain, ...)
                operator_token_arguments, close_paren_index = get_token_arguments(tokens, current_token_index, "{", "}", ",")
                assert len(operator_token_arguments) > 0, f"Expected at least 1 argument, got {len(operator_token_arguments)}"
                inside_querytypes: list[QueryType] = [parse_tokens_into_querytype(inside_tokens) for inside_tokens in operator_token_arguments]
                results.append(OperatorNode(operator=SelectOperator, arguments=inside_querytypes))
                current_token_index = close_paren_index + 1
            elif token == "#":
                # #<id> is shorthand for [.__id__ == <id>]
                results.append(parse_tokens_into_querytype(get_tokens_from_query(
                    f"[.__id__ == '{token_after}']"
                )).operator_nodes[0])
                current_token_index += 2
            elif token == "@":
                # @<source> is shorthand for [.__source__ == <source>]
                results.append(parse_tokens_into_querytype(get_tokens_from_query(
                    f"[.__source__ == '{token_after}' | 'all']"
                )).operator_nodes[0])
                current_token_index += 2
            else:
                assert current_token_index == 0, f"Can only do syntax-free shorthand type filtering at the beginning, got {token} at index {current_token_index}"
                # Is shorthand for .filter(.get_field("__types__").includes(token))
                results.append(parse_tokens_into_querytype(get_tokens_from_query(
                    f"[.__types__.includes('{token}')]"
                )).operator_nodes[0])
                current_token_index += 1
        elif current_state == 'after_dot':
            if token_after == "(":
                operator = next((op for op in all_operators if op.name == token), None)
                assert operator, f"Invalid operator: {token}"
                operator_token_arguments, close_paren_index = get_token_arguments(tokens, current_token_index + 1, "(", ")", ",")
                if close_paren_index == current_token_index + 2:
                    parsed_arguments = []
                else:
                    parsed_arguments: list[QueryType] = [parse_tokens_into_querytype(arg) for arg in operator_token_arguments]
                results.append(OperatorNode(operator=operator, arguments=parsed_arguments))
                current_token_index = close_paren_index + 1
                current_state = 'start'
            else:
                # This is shorthand for .get_field(token)
                # e.g. .app -> .get_field("app")
                results.append(OperatorNode(operator=GetFieldOperator, arguments=[token]))
                current_token_index += 1
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
            raise ValueError(f"Invalid state: {current_state}")
        
        assert current_token_index > current_token_index_at_start, f"Token index didn't move forward from {current_token_index_at_start} to {current_token_index} for token {token} in state {current_state}"

    return get_parser_results(results)
