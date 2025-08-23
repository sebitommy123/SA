#!/usr/bin/env python3
"""
Test the get_tokens_from_query function to ensure it works correctly.
"""

from sa.query_language.main import get_tokens_from_query

def test_tokenizer():
    """Test various query inputs to ensure proper tokenization."""
    
    test_cases = [
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
    ]
    
    print("🧪 Testing get_tokens_from_query function...")
    print("=" * 50)
    
    all_passed = True
    
    for i, (input_query, expected_tokens) in enumerate(test_cases, 1):
        try:
            actual_tokens = get_tokens_from_query(input_query)
            
            if actual_tokens == expected_tokens:
                print(f"✅ Test {i}: PASSED")
                print(f"   Input: '{input_query}'")
                print(f"   Output: {actual_tokens}")
            else:
                print(f"❌ Test {i}: FAILED")
                print(f"   Input: '{input_query}'")
                print(f"   Expected: {expected_tokens}")
                print(f"   Got:      {actual_tokens}")
                all_passed = False
            
            print()
            
        except Exception as e:
            print(f"💥 Test {i}: ERROR")
            print(f"   Input: '{input_query}'")
            print(f"   Error: {e}")
            print()
            all_passed = False
    
    if all_passed:
        print("🎉 All tests passed! The tokenizer is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above.")
    
    return all_passed

if __name__ == "__main__":
    test_tokenizer() 