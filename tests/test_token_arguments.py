"""
Unit tests for the get_token_arguments function.
"""

import pytest
from sa.query_language.main import get_token_arguments, get_tokens_from_query


class TestGetTokenArguments:
    """Test cases for the get_token_arguments function."""
    
    def test_simple_two_arguments(self):
        """Test simple case with two arguments: equals(name,John)."""
        tokens = ["equals", "(", "name", ",", "John", ")"]
        expected = [["name"], ["John"]]
        result = get_token_arguments(tokens, 1)
        assert result == expected
    
    def test_multiple_complex_arguments(self):
        """Test multiple complex arguments with nested parentheses."""
        tokens = ["filter", "(", "equals", "(", "department", ",", "Engineering", ")", ",", "get_field", "(", "salary", ")", ")"]
        expected = [["equals", "(", "department", ",", "Engineering", ")"], ["get_field", "(", "salary", ")"]]
        result = get_token_arguments(tokens, 1)
        assert result == expected
    
    def test_nested_parentheses(self):
        """Test deeply nested parentheses: equals(equals(a,b),equals(c,d))."""
        tokens = ["equals", "(", "equals", "(", "a", ",", "b", ")", ",", "equals", "(", "c", ",", "d", ")", ")"]
        expected = [["equals", "(", "a", ",", "b", ")"], ["equals", "(", "c", ",", "d", ")"]]
        result = get_token_arguments(tokens, 1)
        assert result == expected
    
    def test_single_nested_argument(self):
        """Test single argument with nested content: filter(equals(name,John))."""
        tokens = ["filter", "(", "equals", "(", "name", ",", "John", ")", ")"]
        expected = [["equals", "(", "name", ",", "John", ")"]]
        result = get_token_arguments(tokens, 1)
        assert result == expected
    
    def test_empty_arguments(self):
        """Test empty parentheses: get_field()."""
        tokens = ["get_field", "(", ")"]
        expected = [[]]
        result = get_token_arguments(tokens, 1)
        assert result == expected
    
    def test_complex_nested_structure(self):
        """Test complex nested structure with multiple levels."""
        tokens = [
            "filter", "(", "equals", "(", "department", ",", "Engineering", ")", ",",
            "filter", "(", "equals", "(", "salary", ",", "50000", ")", ",",
            "equals", "(", "level", ",", "Manager", ")", ")", ")"
        ]
        expected = [
            ["equals", "(", "department", ",", "Engineering", ")"],
            ["filter", "(", "equals", "(", "salary", ",", "50000", ")", ",",
             "equals", "(", "level", ",", "Manager", ")", ")"]
        ]
        result = get_token_arguments(tokens, 1)
        assert result == expected
    
    def test_invalid_start_token(self):
        """Test that function raises error when not starting with opening parenthesis."""
        tokens = ["equals", "name", ",", "John"]
        with pytest.raises(AssertionError, match="Expected \\( at index 1, got name"):
            get_token_arguments(tokens, 1)
    
    def test_unmatched_parentheses(self):
        """Test that function raises error with unmatched parentheses."""
        tokens = ["equals", "(", "name", ",", "John"]  # Missing closing parenthesis
        with pytest.raises(AssertionError, match="Couldn't find a matching closing parenthesis"):
            get_token_arguments(tokens, 1)


class TestGetTokenArgumentsWithRealQueries:
    """Test get_token_arguments with real query strings parsed by get_tokens_from_query."""
    
    def test_equals_query(self):
        """Test: equals(name,John)."""
        query = "equals(name,John)"
        tokens = get_tokens_from_query(query)
        paren_index = tokens.index("(")
        result = get_token_arguments(tokens, paren_index)
        expected = [["name"], ["John"]]
        assert result == expected
    
    def test_filter_query(self):
        """Test: filter(equals(department,Engineering))."""
        query = "filter(equals(department,Engineering))"
        tokens = get_tokens_from_query(query)
        paren_index = tokens.index("(")
        result = get_token_arguments(tokens, paren_index)
        expected = [["equals", "(", "department", ",", "Engineering", ")"]]
        assert result == expected
    
    def test_get_field_query(self):
        """Test: get_field(manager_id)."""
        query = "get_field(manager_id)"
        tokens = get_tokens_from_query(query)
        paren_index = tokens.index("(")
        result = get_token_arguments(tokens, paren_index)
        expected = [["manager_id"]]
        assert result == expected
    
    def test_complex_filter_query(self):
        """Test: filter(equals(department,Engineering),equals(level,Manager))."""
        query = "filter(equals(department,Engineering),equals(level,Manager))"
        tokens = get_tokens_from_query(query)
        paren_index = tokens.index("(")
        result = get_token_arguments(tokens, paren_index)
        expected = [["equals", "(", "department", ",", "Engineering", ")"], ["equals", "(", "level", ",", "Manager", ")"]]
        assert result == expected


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_single_argument(self):
        """Test single argument without comma."""
        tokens = ["func", "(", "arg", ")"]
        result = get_token_arguments(tokens, 1)
        expected = [["arg"]]
        assert result == expected
    
    def test_multiple_simple_arguments(self):
        """Test multiple simple arguments: func(a,b,c)."""
        tokens = ["func", "(", "a", ",", "b", ",", "c", ")"]
        result = get_token_arguments(tokens, 1)
        expected = [["a"], ["b"], ["c"]]
        assert result == expected
    
    def test_nested_with_commas(self):
        """Test nested structure with commas at different levels."""
        tokens = ["func", "(", "a", ",", "(", "b", ",", "c", ")", ",", "d", ")"]
        result = get_token_arguments(tokens, 1)
        expected = [["a"], ["(", "b", ",", "c", ")"], ["d"]]
        assert result == expected 