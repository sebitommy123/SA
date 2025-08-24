"""
Unit tests for the get_tokens_from_query function.
"""

import pytest
from sa.query_language.parser import get_tokens_from_query


@pytest.mark.parametrize(
	"input_query,expected_tokens",
	[
		# Simple queries
		("filter equals name John", ["filter", "equals", "name", "John"]),
		("get_field salary", ["get_field", "salary"]),
		("equals 5 5", ["equals", "5", "5"]),
		# Queries with special characters
		("filter(equals(name,John))", ["filter", "(", "equals", "(", "name", ",", "John", ")", ")"]),
		("get_field.salary", ["get_field", ".", "salary"]),
		("equals:5:5", ["equals", ":", "5", ":", "5"]),
		# Complex queries
		("filter(equals(department,Engineering))", ["filter", "(", "equals", "(", "department", ",", "Engineering", ")", ")"]),
		("get_field manager_id", ["get_field", "manager_id"]),
		# Edge cases
		("", []),
		("   ", []),
		("a", ["a"]),
		("123", ["123"]),
		("abc123", ["abc123"]),
		("a b c", ["a", "b", "c"]),
		("a,b,c", ["a", ",", "b", ",", "c"]),
		("a+b-c", ["a", "+", "b", "-", "c"]),
	],
)

def test_tokenizer(input_query, expected_tokens):
	actual_tokens = get_tokens_from_query(input_query)
	assert actual_tokens == expected_tokens 