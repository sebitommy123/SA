from typing import Optional
from .main import QueryType, Chain, OperatorNode
from .operators import EqualsOperator, FilterOperator, GetFieldOperator, SelectOperator, all_operators

Tokens = list[str]

def get_tokens_from_query(query: str) -> Tokens:
    tokens = []
    current_alphanumeric = ''
    
    for char in query:
        if char.isalnum() or char == '_':
            current_alphanumeric += char
        else:
            if current_alphanumeric:
                tokens.append(current_alphanumeric)
                current_alphanumeric = ''
            tokens.append(char)
    
    # Don't forget the last alphanumeric sequence
    if current_alphanumeric:
        tokens.append(current_alphanumeric)
    
    return tokens

def accumulate_identifier_tokens(tokens: Tokens, start_index: int) -> tuple[str, int]:
    """Accumulate consecutive tokens that are alphanumeric, underscore, or dash.

    Returns the joined identifier string and the index after the last consumed token.
    """
    scan_index = start_index
    accumulated_tokens: list[str] = []
    while scan_index < len(tokens):
        next_token = tokens[scan_index]
        if next_token == "-":
            accumulated_tokens.append(next_token)
            scan_index += 1
            continue
        if next_token and all(ch.isalnum() or ch == '_' for ch in next_token):
            accumulated_tokens.append(next_token)
            scan_index += 1
            continue
        break

    assert len(accumulated_tokens) > 0, f"Expected identifier at index {start_index}"
    return ''.join(accumulated_tokens), scan_index

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
                assert token_after == "=", f"Expected ==, got just one ="
                left = get_parser_results(results)
                right = parse_tokens_into_querytype(tokens[current_token_index + 2:])
                return Chain([OperatorNode(operator=EqualsOperator, arguments=[left, right])])
            elif token == "[":
                # This is shorthand for .filter(chain)
                operator_token_arguments, close_paren_index = get_token_arguments(tokens, current_token_index, "[", "]", "|")
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
                accumulated_id, scan_index = accumulate_identifier_tokens(tokens, current_token_index + 1)
                results.append(parse_tokens_into_querytype(get_tokens_from_query(
                    f"[.__id__ == '{accumulated_id}']"
                )).operator_nodes[0])
                current_token_index = scan_index
            elif token == "@":
                # @<source> is shorthand for [.__source__ == <source>]
                accumulated_source, scan_index = accumulate_identifier_tokens(tokens, current_token_index + 1)
                results.append(parse_tokens_into_querytype(get_tokens_from_query(
                    f"[.__source__ == '{accumulated_source}' | 'all']"
                )).operator_nodes[0])
                current_token_index = scan_index
            else:
                assert current_token_index == 0, f"Can only do syntax-free shorthand type filtering at the beginning, got {token} at index {current_token_index}"
                # Accumulate type tokens to support hyphenated types
                accumulated_type, scan_index = accumulate_identifier_tokens(tokens, current_token_index)
                # Is shorthand for .filter(.get_field("__types__").includes(token))
                results.append(parse_tokens_into_querytype(get_tokens_from_query(
                    f"[.__types__.includes('{accumulated_type}')]"
                )).operator_nodes[0])
                current_token_index = scan_index
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
