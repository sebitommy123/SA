"""
Unit tests for the parse_tokens_into_querytype function.
"""

import pytest
from sa.query_language.main import parse_tokens_into_querytype, get_tokens_from_query


class TestParseTokensIntoQueryType:
    """Test cases for the parse_tokens_into_querytype function."""
    
    def test_simple_operator_call(self):
        """Test simple operator call: .equals(.get_field("name"),"John")."""
        tokens = [".", "equals", "(", ".", "get_field", "(", '"', "name", '"', ")", ",", '"', "John", '"', ")"]
        result = parse_tokens_into_querytype(tokens)
        
        assert result.operator_nodes[0].operator.name == "equals"
        assert len(result.operator_nodes[0].arguments) == 2
        # First argument should be a Chain with get_field operator
        assert isinstance(result.operator_nodes[0].arguments[0], type(result))
        assert result.operator_nodes[0].arguments[0].operator_nodes[0].operator.name == "get_field"
        # Second argument should be the string "John"
        assert result.operator_nodes[0].arguments[1] == "John"
    
    def test_get_field_operator(self):
        """Test get_field operator: .get_field("salary")."""
        tokens = [".", "get_field", "(", '"', "salary", '"', ")"]
        result = parse_tokens_into_querytype(tokens)
        
        assert result.operator_nodes[0].operator.name == "get_field"
        assert result.operator_nodes[0].arguments == ["salary"]
    
    def test_filter_operator(self):
        """Test filter operator: .filter(.equals(.get_field("department"),"Engineering"))."""
        tokens = [".", "filter", "(", ".", "equals", "(", ".", "get_field", "(", '"', "department", '"', ")", ",", '"', "Engineering", '"', ")", ")"]
        result = parse_tokens_into_querytype(tokens)
        
        assert result.operator_nodes[0].operator.name == "filter"
        # The argument should be a Chain with an equals operator
        assert isinstance(result.operator_nodes[0].arguments[0], type(result))
        assert result.operator_nodes[0].arguments[0].operator_nodes[0].operator.name == "equals"
    
    def test_nested_operators(self):
        """Test nested operators: .filter(.equals(.get_field("department"),"Engineering"),.equals(.get_field("level"),"Manager"))."""
        tokens = [".", "filter", "(", ".", "equals", "(", ".", "get_field", "(", '"', "department", '"', ")", ",", '"', "Engineering", '"', ")", ",", ".", "equals", "(", ".", "get_field", "(", '"', "level", '"', ")", ",", '"', "Manager", '"', ")", ")"]
        result = parse_tokens_into_querytype(tokens)
        
        assert result.operator_nodes[0].operator.name == "filter"
        assert len(result.operator_nodes[0].arguments) == 2
        # Both arguments should be Chains
        assert isinstance(result.operator_nodes[0].arguments[0], type(result))
        assert isinstance(result.operator_nodes[0].arguments[1], type(result))
    
    def test_integer_literal(self):
        """Test integer literal: 42."""
        tokens = ["42"]
        result = parse_tokens_into_querytype(tokens)
        
        assert result == 42
    
    def test_string_literal_single_quotes(self):
        """Test string literal with single quotes: 'hello'."""
        tokens = ["'", "h", "e", "l", "l", "o", "'"]
        result = parse_tokens_into_querytype(tokens)
        
        assert result == "hello"
    
    def test_string_literal_double_quotes(self):
        """Test string literal with double quotes: "world"."""
        tokens = ['"', "w", "o", "r", "l", "d", '"']
        result = parse_tokens_into_querytype(tokens)
        
        assert result == "world"
    
    def test_boolean_literal_true(self):
        """Test boolean literal: true."""
        tokens = ["true"]
        result = parse_tokens_into_querytype(tokens)
        
        assert result is True
    
    def test_boolean_literal_false(self):
        """Test boolean literal: false."""
        tokens = ["false"]
        result = parse_tokens_into_querytype(tokens)
        
        assert result is False
    
    def test_invalid_start_token(self):
        """Test that function raises error for invalid start token."""
        tokens = ["invalid"]
        with pytest.raises(ValueError, match="Invalid token: invalid"):
            parse_tokens_into_querytype(tokens)
    
    def test_invalid_after_dot_state(self):
        """Test that function raises error for invalid token after dot."""
        tokens = [".", "equals", "invalid"]
        with pytest.raises(ValueError, match="Invalid token: equals"):
            parse_tokens_into_querytype(tokens)
    
    def test_number_followed_by_token(self):
        """Test that function raises error when number is followed by another token."""
        tokens = ["42", "invalid"]
        with pytest.raises(AssertionError, match="Number 42 cannot be followed by invalid"):
            parse_tokens_into_querytype(tokens)
    
    def test_string_followed_by_token(self):
        """Test that function raises error when string is followed by another token."""
        tokens = ["'", "hello", "'", "invalid"]
        with pytest.raises(AssertionError, match="String hello cannot be followed by invalid"):
            parse_tokens_into_querytype(tokens)
    
    def test_boolean_followed_by_token(self):
        """Test that function raises error when boolean is followed by another token."""
        tokens = ["true", "invalid"]
        with pytest.raises(AssertionError, match="Boolean true cannot be followed by invalid"):
            parse_tokens_into_querytype(tokens)
    
    def test_invalid_operator(self):
        """Test that function raises error for invalid operator name."""
        tokens = [".", "invalid_operator", "(", "arg", ")"]
        with pytest.raises(AssertionError, match="Invalid operator: invalid_operator"):
            parse_tokens_into_querytype(tokens)


class TestParseTokensWithRealQueries:
    """Test parse_tokens_into_querytype with real query strings."""
    
    def test_real_equals_query(self):
        """Test parsing: .equals(.get_field("name"),"John")."""
        query = '.equals(.get_field("name"),"John")'
        tokens = get_tokens_from_query(query)
        result = parse_tokens_into_querytype(tokens)
        
        assert result.operator_nodes[0].operator.name == "equals"
        assert len(result.operator_nodes[0].arguments) == 2
        # First argument should be a Chain with get_field operator
        assert isinstance(result.operator_nodes[0].arguments[0], type(result))
        assert result.operator_nodes[0].arguments[0].operator_nodes[0].operator.name == "get_field"
        # Second argument should be the string "John"
        assert result.operator_nodes[0].arguments[1] == "John"
    
    def test_real_filter_query(self):
        """Test parsing: .filter(.equals(.get_field("department"),"Engineering"))."""
        query = '.filter(.equals(.get_field("department"),"Engineering"))'
        tokens = get_tokens_from_query(query)
        result = parse_tokens_into_querytype(tokens)
        
        assert result.operator_nodes[0].operator.name == "filter"
        assert isinstance(result.operator_nodes[0].arguments[0], type(result))
        assert result.operator_nodes[0].arguments[0].operator_nodes[0].operator.name == "equals"
    
    def test_real_complex_query(self):
        """Test parsing: .filter(.equals(.get_field("department"),"Engineering"),.equals(.get_field("level"),"Manager"))."""
        query = '.filter(.equals(.get_field("department"),"Engineering"),.equals(.get_field("level"),"Manager"))'
        tokens = get_tokens_from_query(query)
        result = parse_tokens_into_querytype(tokens)
        
        assert result.operator_nodes[0].operator.name == "filter"
        assert len(result.operator_nodes[0].arguments) == 2
        # Both arguments should be Chains
        assert isinstance(result.operator_nodes[0].arguments[0], type(result))
        assert isinstance(result.operator_nodes[0].arguments[1], type(result)) 