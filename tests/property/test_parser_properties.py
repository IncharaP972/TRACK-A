"""
Property-based tests for the deterministic value parser.

Feature: latspace-excel-parser
"""

import re
import pytest
from hypothesis import given, strategies as st
from app.core.parser import parse_value


# Property 6: Numeric Value Parsing with Commas
# **Validates: Requirements 8.1**


@given(
    # Generate floats with reasonable precision
    value=st.floats(
        min_value=1000.0,
        max_value=999999999.99,
        allow_nan=False,
        allow_infinity=False,
    ),
)
def test_numeric_parsing_with_commas(value):
    """
    Property 6: Numeric Value Parsing with Commas
    For any string representing a number with comma separators (e.g., "1,234.56", "10,000"),
    parsing should remove commas and return the correct numeric value.
    
    **Validates: Requirements 8.1**
    """
    # Format the value with commas
    # Use Python's format to add commas
    formatted_str = f"{value:,.2f}" if value % 1 != 0 else f"{int(value):,}"
    
    # Parse the formatted string
    result = parse_value(formatted_str)
    
    # Verify the result matches the expected value (with small tolerance for float precision)
    assert result is not None, f"parse_value returned None for '{formatted_str}'"
    assert isinstance(result, float), f"parse_value did not return float for '{formatted_str}'"
    
    # For integers, expect exact match
    if value % 1 == 0:
        expected = float(int(value))
        assert result == expected, \
            f"parse_value({formatted_str}) = {result}, expected {expected}"
    else:
        # For decimals, allow small tolerance due to float formatting
        expected = round(value, 2)
        assert abs(result - expected) < 1e-6, \
            f"parse_value({formatted_str}) = {result}, expected {expected}"


@given(
    # Generate positive integers with commas
    value=st.integers(min_value=1000, max_value=999999999),
)
def test_numeric_parsing_integer_with_commas(value):
    """
    Property 6: Numeric Value Parsing with Commas (Integer variant)
    For any integer string with comma separators, parsing should return the correct numeric value.
    
    **Validates: Requirements 8.1**
    """
    # Format with commas
    formatted_str = f"{value:,}"
    expected_value = float(value)
    
    # Parse the formatted string
    result = parse_value(formatted_str)
    
    # Verify the result
    assert result == expected_value, \
        f"parse_value({formatted_str}) = {result}, expected {expected_value}"


@given(
    # Generate negative integers with commas
    value=st.integers(min_value=-999999999, max_value=-1000),
)
def test_numeric_parsing_negative_with_commas(value):
    """
    Property 6: Numeric Value Parsing with Commas (Negative variant)
    For any negative number string with comma separators, parsing should return the correct numeric value.
    
    **Validates: Requirements 8.1**
    """
    # Format with commas (Python's format adds commas after the negative sign)
    formatted_str = f"{value:,}"
    expected_value = float(value)
    
    # Parse the formatted string
    result = parse_value(formatted_str)
    
    # Verify the result
    assert result == expected_value, \
        f"parse_value({formatted_str}) = {result}, expected {expected_value}"



# Property 7: Percentage Conversion
# **Validates: Requirements 8.2**


@given(
    # Generate realistic percentage values from 0 to 100 with decimals
    # Avoid very small values that would be formatted in scientific notation
    percentage=st.floats(
        min_value=0.001,
        max_value=100.0,
        allow_nan=False,
        allow_infinity=False,
    ).filter(lambda x: abs(x) >= 0.001),  # Filter out values too close to zero
)
def test_percentage_conversion(percentage):
    """
    Property 7: Percentage Conversion
    For any string in percentage format (e.g., "45%", "99.9%"),
    parsing should return the decimal equivalent (0.45, 0.999).
    
    **Validates: Requirements 8.2**
    """
    # Format as percentage string (avoid scientific notation)
    percentage_str = f"{percentage:.6f}%".rstrip('0').rstrip('.')
    if '.' not in percentage_str.replace('%', ''):
        percentage_str = percentage_str.replace('%', '') + '%'
    
    # Expected decimal value
    expected_decimal = percentage / 100.0
    
    # Parse the percentage string
    result = parse_value(percentage_str)
    
    # Verify the result
    assert result is not None, f"parse_value returned None for '{percentage_str}'"
    assert isinstance(result, float), f"parse_value did not return float for '{percentage_str}'"
    # Use a more reasonable tolerance for float precision after string formatting
    assert abs(result - expected_decimal) < 1e-6, \
        f"parse_value({percentage_str}) = {result}, expected {expected_decimal}"


@given(
    # Generate negative percentages
    percentage=st.floats(
        min_value=-100.0,
        max_value=-0.01,
        allow_nan=False,
        allow_infinity=False,
    ),
)
def test_percentage_conversion_negative(percentage):
    """
    Property 7: Percentage Conversion (Negative variant)
    For any negative percentage string, parsing should return the correct decimal equivalent.
    
    **Validates: Requirements 8.2**
    """
    # Format as percentage string
    percentage_str = f"{percentage}%"
    
    # Expected decimal value
    expected_decimal = percentage / 100.0
    
    # Parse the percentage string
    result = parse_value(percentage_str)
    
    # Verify the result
    assert result is not None, f"parse_value returned None for '{percentage_str}'"
    assert isinstance(result, float), f"parse_value did not return float for '{percentage_str}'"
    assert abs(result - expected_decimal) < 1e-9, \
        f"parse_value({percentage_str}) = {result}, expected {expected_decimal}"


@given(
    # Generate large percentages (over 100%)
    percentage=st.floats(
        min_value=100.01,
        max_value=10000.0,
        allow_nan=False,
        allow_infinity=False,
    ),
)
def test_percentage_conversion_over_100(percentage):
    """
    Property 7: Percentage Conversion (Over 100% variant)
    For any percentage string over 100%, parsing should return the correct decimal equivalent.
    
    **Validates: Requirements 8.2**
    """
    # Format as percentage string
    percentage_str = f"{percentage}%"
    
    # Expected decimal value
    expected_decimal = percentage / 100.0
    
    # Parse the percentage string
    result = parse_value(percentage_str)
    
    # Verify the result
    assert result is not None, f"parse_value returned None for '{percentage_str}'"
    assert isinstance(result, float), f"parse_value did not return float for '{percentage_str}'"
    assert abs(result - expected_decimal) < 1e-6, \
        f"parse_value({percentage_str}) = {result}, expected {expected_decimal}"


@given(
    # Generate integer percentages
    percentage=st.integers(min_value=0, max_value=100),
)
def test_percentage_conversion_integers(percentage):
    """
    Property 7: Percentage Conversion (Integer variant)
    For any integer percentage string, parsing should return the correct decimal equivalent.
    
    **Validates: Requirements 8.2**
    """
    # Format as percentage string
    percentage_str = f"{percentage}%"
    
    # Expected decimal value
    expected_decimal = percentage / 100.0
    
    # Parse the percentage string
    result = parse_value(percentage_str)
    
    # Verify the result
    assert result == expected_decimal, \
        f"parse_value({percentage_str}) = {result}, expected {expected_decimal}"



# Property 8: N/A Value Normalization
# **Validates: Requirements 8.5**


@given(
    # Generate N/A variations with different cases and whitespace
    na_variant=st.sampled_from(["N/A", "NA", "NULL", "NONE", "-"]),
    prefix_whitespace=st.text(alphabet=' \t', max_size=3),
    suffix_whitespace=st.text(alphabet=' \t', max_size=3),
    case_transform=st.sampled_from(['lower', 'upper', 'title', 'mixed']),
)
def test_na_normalization(na_variant, prefix_whitespace, suffix_whitespace, case_transform):
    """
    Property 8: N/A Value Normalization
    For any string representing missing data (N/A, NA, NULL, NONE, -, or empty string),
    parsing should return None.
    
    **Validates: Requirements 8.5**
    """
    # Apply case transformation
    if case_transform == 'lower':
        na_str = na_variant.lower()
    elif case_transform == 'upper':
        na_str = na_variant.upper()
    elif case_transform == 'title':
        na_str = na_variant.title()
    else:  # mixed
        # Create mixed case by alternating
        na_str = ''.join(c.upper() if i % 2 == 0 else c.lower() 
                        for i, c in enumerate(na_variant))
    
    # Add whitespace
    na_str_with_whitespace = prefix_whitespace + na_str + suffix_whitespace
    
    # Parse the N/A string
    result = parse_value(na_str_with_whitespace)
    
    # Verify the result is None
    assert result is None, \
        f"parse_value('{na_str_with_whitespace}') = {result}, expected None"


@given(
    # Generate empty strings with various whitespace
    whitespace=st.text(alphabet=' \t\n\r', max_size=5),
)
def test_na_normalization_empty_strings(whitespace):
    """
    Property 8: N/A Value Normalization (Empty string variant)
    For any empty string or whitespace-only string, parsing should return None.
    
    **Validates: Requirements 8.5**
    """
    # Parse the whitespace string
    result = parse_value(whitespace)
    
    # Verify the result is None
    assert result is None, \
        f"parse_value('{repr(whitespace)}') = {result}, expected None"


def test_na_normalization_none_input():
    """
    Property 8: N/A Value Normalization (None input variant)
    For None input, parsing should return None.
    
    **Validates: Requirements 8.5**
    """
    result = parse_value(None)
    assert result is None, "parse_value(None) should return None"



# Property 14: Unparseable Value Preservation
# **Validates: Requirements 11.4**


@given(
    # Generate strings that don't match any parseable pattern
    # Avoid strings that could be parsed as numbers, percentages, or N/A values
    text=st.text(
        alphabet=st.characters(blacklist_categories=('Cs',)),  # Exclude surrogates
        min_size=1,
        max_size=50
    ).filter(
        lambda s: (
            s.strip() and  # Not empty after stripping
            s.strip().upper() not in ["N/A", "NA", "NULL", "NONE", "-", "YES", "NO"] and  # Not N/A or YES/NO
            not re.match(r'^-?[\d,]+\.?\d*$', s.strip()) and  # Not a number
            not re.match(r'^-?[\d,]+\.?\d*\s*%$', s.strip())  # Not a percentage
        )
    ),
)
def test_unparseable_value_preservation(text):
    """
    Property 14: Unparseable Value Preservation
    For any cell value that cannot be parsed to a numeric type,
    the parser should preserve the original value as a string.
    
    **Validates: Requirements 11.4**
    """
    # Parse the unparseable text
    result = parse_value(text)
    
    # Verify the result is a string (the original value preserved)
    assert result is not None, f"parse_value should not return None for unparseable text '{text}'"
    assert isinstance(result, str), \
        f"parse_value('{text}') = {result} (type: {type(result)}), expected string"
    # The result should be the stripped version of the input
    assert result == text.strip(), \
        f"parse_value('{text}') = '{result}', expected '{text.strip()}'"


@given(
    # Generate strings with multiple decimal points (invalid numbers)
    parts=st.lists(st.integers(min_value=0, max_value=999), min_size=3, max_size=5),
)
def test_unparseable_value_preservation_invalid_numbers(parts):
    """
    Property 14: Unparseable Value Preservation (Invalid number variant)
    For any string that looks like a number but has invalid format (e.g., multiple decimal points),
    the parser should preserve it as a string.
    
    **Validates: Requirements 11.4**
    """
    # Create an invalid number with multiple decimal points
    invalid_number = '.'.join(str(p) for p in parts)
    
    # Parse the invalid number
    result = parse_value(invalid_number)
    
    # Verify the result is a string
    assert isinstance(result, str), \
        f"parse_value('{invalid_number}') should return string for invalid number format"
    assert result == invalid_number, \
        f"parse_value('{invalid_number}') = '{result}', expected '{invalid_number}'"


@given(
    # Generate text with letters and numbers mixed
    text=st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')),
        min_size=2,
        max_size=20
    ).filter(
        lambda s: (
            any(c.isalpha() for c in s) and  # Has at least one letter
            any(c.isdigit() for c in s) and  # Has at least one digit
            s.strip().upper() not in ["N/A", "NA", "NULL", "NONE", "YES", "NO"]  # Not special values
        )
    ),
)
def test_unparseable_value_preservation_alphanumeric(text):
    """
    Property 14: Unparseable Value Preservation (Alphanumeric variant)
    For any alphanumeric string that cannot be parsed as a number,
    the parser should preserve it as a string.
    
    **Validates: Requirements 11.4**
    """
    # Parse the alphanumeric text
    result = parse_value(text)
    
    # Verify the result is a string
    assert isinstance(result, str), \
        f"parse_value('{text}') should return string for alphanumeric text"
    assert result == text.strip(), \
        f"parse_value('{text}') = '{result}', expected '{text.strip()}'"
