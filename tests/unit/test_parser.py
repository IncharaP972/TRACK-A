"""
Unit tests for the deterministic value parser.
Tests specific examples and edge cases.
"""

import pytest
from app.core.parser import parse_value


class TestParseValue:
    """Test parse_value function with specific examples"""
    
    def test_none_returns_none(self):
        """Test that None input returns None"""
        assert parse_value(None) is None
    
    def test_empty_string_returns_none(self):
        """Test that empty string returns None"""
        assert parse_value("") is None
        assert parse_value("   ") is None
    
    def test_na_variations_return_none(self):
        """Test that N/A variations return None"""
        assert parse_value("N/A") is None
        assert parse_value("NA") is None
        assert parse_value("NULL") is None
        assert parse_value("NONE") is None
        assert parse_value("-") is None
        # Test case insensitivity
        assert parse_value("n/a") is None
        assert parse_value("Na") is None
        assert parse_value("null") is None
    
    def test_yes_returns_one(self):
        """Test that YES returns 1.0"""
        assert parse_value("YES") == 1.0
        assert parse_value("yes") == 1.0
        assert parse_value("Yes") == 1.0
    
    def test_no_returns_zero(self):
        """Test that NO returns 0.0"""
        assert parse_value("NO") == 0.0
        assert parse_value("no") == 0.0
        assert parse_value("No") == 0.0
    
    def test_percentage_conversion(self):
        """Test percentage string conversion to decimal"""
        assert parse_value("45%") == 0.45
        assert abs(parse_value("99.9%") - 0.999) < 1e-10
        assert parse_value("100%") == 1.0
        assert parse_value("0%") == 0.0
        assert parse_value("12.5%") == 0.125
    
    def test_numbers_with_commas(self):
        """Test numbers with comma separators"""
        assert parse_value("1,234.56") == 1234.56
        assert parse_value("10,000") == 10000.0
        assert parse_value("1,000,000.99") == 1000000.99
        assert parse_value("123,456") == 123456.0
    
    def test_negative_numbers(self):
        """Test negative number parsing"""
        assert parse_value("-123") == -123.0
        assert parse_value("-1,234.56") == -1234.56
        assert parse_value("-10,000") == -10000.0
    
    def test_simple_numbers(self):
        """Test simple numeric values"""
        assert parse_value("123") == 123.0
        assert parse_value("123.45") == 123.45
        assert parse_value("0.5") == 0.5
        assert parse_value("0") == 0.0
    
    def test_unparseable_strings(self):
        """Test that unparseable values are returned as strings"""
        assert parse_value("hello") == "hello"
        assert parse_value("abc123") == "abc123"
        assert parse_value("12.34.56") == "12.34.56"
        assert parse_value("not a number") == "not a number"
    
    def test_numeric_types(self):
        """Test that numeric types are handled correctly"""
        assert parse_value(123) == 123.0
        assert parse_value(123.45) == 123.45
        assert parse_value(0) == 0.0
    
    def test_percentage_with_commas(self):
        """Test percentages with comma separators"""
        assert parse_value("1,234%") == 12.34
        assert parse_value("10,000%") == 100.0
    
    def test_negative_percentage(self):
        """Test negative percentages"""
        assert parse_value("-45%") == -0.45
        assert parse_value("-10%") == -0.10



class TestParseRow:
    """Test parse_row function with header mappings"""
    
    def test_parse_row_basic(self):
        """Test basic row parsing with header mappings"""
        from app.core.parser import parse_row
        from app.schema.models import HeaderMapping, MatchMethod, ConfidenceLevel
        
        # Create sample header mappings
        mappings = [
            HeaderMapping(
                original_header="Power_Output",
                matched_parameter="Power_Output",
                method=MatchMethod.EXACT,
                confidence=ConfidenceLevel.HIGH
            ),
            HeaderMapping(
                original_header="Temperature",
                matched_parameter="Temperature",
                method=MatchMethod.EXACT,
                confidence=ConfidenceLevel.HIGH
            ),
            HeaderMapping(
                original_header="Status",
                matched_parameter="Status",
                method=MatchMethod.FUZZY,
                confidence=ConfidenceLevel.MEDIUM
            )
        ]
        
        # Parse a row with various value types
        row_values = ["1,234.56", "45%", "YES"]
        parsed_cells = parse_row(row_values, mappings, row_index=5)
        
        # Verify results
        assert len(parsed_cells) == 3
        
        # Check first cell (numeric with comma)
        assert parsed_cells[0].row_index == 5
        assert parsed_cells[0].column_index == 0
        assert parsed_cells[0].original_value == "1,234.56"
        assert parsed_cells[0].parsed_value == 1234.56
        assert parsed_cells[0].parse_success is True
        assert parsed_cells[0].parse_error is None
        assert parsed_cells[0].header_mapping.original_header == "Power_Output"
        
        # Check second cell (percentage)
        assert parsed_cells[1].column_index == 1
        assert parsed_cells[1].parsed_value == 0.45
        assert parsed_cells[1].parse_success is True
        
        # Check third cell (YES)
        assert parsed_cells[2].column_index == 2
        assert parsed_cells[2].parsed_value == 1.0
        assert parsed_cells[2].parse_success is True
    
    def test_parse_row_with_none_values(self):
        """Test row parsing with None and N/A values"""
        from app.core.parser import parse_row
        from app.schema.models import HeaderMapping, MatchMethod, ConfidenceLevel
        
        mappings = [
            HeaderMapping(
                original_header="Col1",
                method=MatchMethod.EXACT,
                confidence=ConfidenceLevel.HIGH
            ),
            HeaderMapping(
                original_header="Col2",
                method=MatchMethod.EXACT,
                confidence=ConfidenceLevel.HIGH
            ),
            HeaderMapping(
                original_header="Col3",
                method=MatchMethod.EXACT,
                confidence=ConfidenceLevel.HIGH
            )
        ]
        
        row_values = [None, "N/A", ""]
        parsed_cells = parse_row(row_values, mappings, row_index=10)
        
        # All should parse to None
        assert parsed_cells[0].parsed_value is None
        assert parsed_cells[0].parse_success is True
        assert parsed_cells[1].parsed_value is None
        assert parsed_cells[1].parse_success is True
        assert parsed_cells[2].parsed_value is None
        assert parsed_cells[2].parse_success is True
    
    def test_parse_row_with_unparseable_values(self):
        """Test row parsing with unparseable string values"""
        from app.core.parser import parse_row
        from app.schema.models import HeaderMapping, MatchMethod, ConfidenceLevel
        
        mappings = [
            HeaderMapping(
                original_header="Description",
                method=MatchMethod.LLM,
                confidence=ConfidenceLevel.MEDIUM
            ),
            HeaderMapping(
                original_header="Notes",
                method=MatchMethod.NONE,
                confidence=ConfidenceLevel.LOW
            )
        ]
        
        row_values = ["Some text", "More notes"]
        parsed_cells = parse_row(row_values, mappings, row_index=3)
        
        # Unparseable values should be returned as strings
        assert parsed_cells[0].parsed_value == "Some text"
        assert parsed_cells[0].parse_success is True
        assert parsed_cells[1].parsed_value == "More notes"
        assert parsed_cells[1].parse_success is True
    
    def test_parse_row_mismatched_lengths(self):
        """Test row parsing when values and mappings have different lengths"""
        from app.core.parser import parse_row
        from app.schema.models import HeaderMapping, MatchMethod, ConfidenceLevel
        
        # More mappings than values
        mappings = [
            HeaderMapping(
                original_header="Col1",
                method=MatchMethod.EXACT,
                confidence=ConfidenceLevel.HIGH
            ),
            HeaderMapping(
                original_header="Col2",
                method=MatchMethod.EXACT,
                confidence=ConfidenceLevel.HIGH
            ),
            HeaderMapping(
                original_header="Col3",
                method=MatchMethod.EXACT,
                confidence=ConfidenceLevel.HIGH
            )
        ]
        
        row_values = ["123", "456"]  # Only 2 values
        parsed_cells = parse_row(row_values, mappings, row_index=1)
        
        # Should create 3 cells (max of lengths)
        assert len(parsed_cells) == 3
        assert parsed_cells[0].parsed_value == 123.0
        assert parsed_cells[1].parsed_value == 456.0
        assert parsed_cells[2].parsed_value is None  # Missing value
        assert parsed_cells[2].parse_success is True
    
    def test_parse_row_more_values_than_mappings(self):
        """Test row parsing when there are more values than mappings"""
        from app.core.parser import parse_row
        from app.schema.models import HeaderMapping, MatchMethod, ConfidenceLevel
        
        mappings = [
            HeaderMapping(
                original_header="Col1",
                method=MatchMethod.EXACT,
                confidence=ConfidenceLevel.HIGH
            )
        ]
        
        row_values = ["123", "456", "789"]  # 3 values but only 1 mapping
        parsed_cells = parse_row(row_values, mappings, row_index=2)
        
        # Should create 3 cells with default mappings for extra values
        assert len(parsed_cells) == 3
        assert parsed_cells[0].parsed_value == 123.0
        assert parsed_cells[0].header_mapping.original_header == "Col1"
        assert parsed_cells[1].parsed_value == 456.0
        assert parsed_cells[1].header_mapping.original_header == "Column_1"
        assert parsed_cells[1].header_mapping.method == MatchMethod.NONE
        assert parsed_cells[2].parsed_value == 789.0
        assert parsed_cells[2].header_mapping.original_header == "Column_2"
    
    def test_parse_row_preserves_audit_trail(self):
        """Test that parse_row preserves complete audit trail"""
        from app.core.parser import parse_row
        from app.schema.models import HeaderMapping, MatchMethod, ConfidenceLevel
        
        mappings = [
            HeaderMapping(
                original_header="TG-1 Power",
                matched_parameter="Power_Output",
                matched_asset="TG-1",
                method=MatchMethod.FUZZY,
                confidence=ConfidenceLevel.MEDIUM,
                normalized_header="tg1power"
            )
        ]
        
        row_values = ["1,500.75"]
        parsed_cells = parse_row(row_values, mappings, row_index=7)
        
        cell = parsed_cells[0]
        # Verify all audit information is preserved
        assert cell.row_index == 7
        assert cell.column_index == 0
        assert cell.original_value == "1,500.75"
        assert cell.parsed_value == 1500.75
        assert cell.header_mapping.original_header == "TG-1 Power"
        assert cell.header_mapping.matched_parameter == "Power_Output"
        assert cell.header_mapping.matched_asset == "TG-1"
        assert cell.header_mapping.method == MatchMethod.FUZZY
        assert cell.header_mapping.confidence == ConfidenceLevel.MEDIUM
        assert cell.header_mapping.normalized_header == "tg1power"
        assert cell.parse_success is True
        assert cell.parse_error is None
    
    def test_parse_row_default_row_index(self):
        """Test that parse_row uses default row_index when not provided"""
        from app.core.parser import parse_row
        from app.schema.models import HeaderMapping, MatchMethod, ConfidenceLevel
        
        mappings = [
            HeaderMapping(
                original_header="Col1",
                method=MatchMethod.EXACT,
                confidence=ConfidenceLevel.HIGH
            )
        ]
        
        row_values = ["123"]
        parsed_cells = parse_row(row_values, mappings)  # No row_index provided
        
        # Should use default value of 0
        assert parsed_cells[0].row_index == 0
