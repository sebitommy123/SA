
import traceback
from sa.query_language.main import Chain
from sa.query_language.object_list import ObjectList
from sa.query_language.parser import get_tokens_from_query, parse_tokens_into_querytype

def execute_query(query: str, context):
    """Execute a query string and return the result."""
    # Tokenize the query
    tokens = get_tokens_from_query(query)

    # Parse tokens into a query structure
    parsed_query = parse_tokens_into_querytype(tokens)

    if isinstance(parsed_query, Chain):
        result = parsed_query.run(context, context)
    else:
        result = parsed_query

    return result
