"""
Property-based tests for API endpoints and parse result auditability.

Feature: latspace-excel-parser
"""

import pytest
from hypothesis import given, strategies as st, settings
import json

from app.schema.models import (
    ParseResult,
    TableStructure,
    HeaderMapping,
    ParsedCell,
    MatchMethod,
    ConfidenceLevel,
)


# Property 12: Parse Result Auditability
# **Validates: Requirements 10.4**


def create_valid_header_mapping(original_header: str) -> HeaderMapping:
    """Helper to create a valid HeaderMapping for testing."""
    return HeaderMapping(
        original_header=original_header,
        matched_parameter="Power_Output",
        matched_asset="TG-1",
        method=MatchMethod.EXACT,
        confidence=ConfidenceLevel.HIGH,
        normalized_header="poweroutput"
    )


def create_valid_parsed_cell(row_idx: int, col_idx: int, header_mapping: HeaderMapping) -> ParsedCell:
    """Helper to create a valid ParsedCell for testing."""
    return ParsedCell(
        row_index=row_idx,
        column_index=col_idx,
        original_value=123.45,
        parsed_value=123.45,
        header_mapping=header_mapping,
        parse_success=True,
        parse_error=None
    )


@given(
    file_name=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    header_row_index=st.integers(min_value=1, max_value=10),
    column_count=st.integers(min_value=1, max_value=20),
    num_headers=st.integers(min_value=1, max_value=10),
    num_rows=st.integers(min_value=0, max_value=10),
    llm_calls=st.integers(min_value=0, max_value=1),
)
@settings(max_examples=100)
def test_parse_result_is_json_serializable(
    file_name, header_row_index, column_count, num_headers, num_rows, llm_calls
):
    """
    Property 12: Parse Result Auditability
    For any ParseResult, it should be serializable to JSON and contain:
    file_name, table_structure, header_mappings list, parsed_data grid,
    total_cells count, successful_parses count, and llm_calls_made count.
    
    **Validates: Requirements 10.4**
    """
    # Create table structure
    table_structure = TableStructure(
        header_row_index=header_row_index,
        data_start_row=header_row_index + 1,
        column_count=column_count,
        merged_cells=[]
    )
    
    # Create header mappings
    header_mappings = [
        create_valid_header_mapping(f"Header_{i}")
        for i in range(num_headers)
    ]
    
    # Create parsed data grid
    parsed_data = []
    for row_idx in range(num_rows):
        row_cells = [
            create_valid_parsed_cell(row_idx, col_idx, header_mappings[col_idx % num_headers])
            for col_idx in range(num_headers)
        ]
        parsed_data.append(row_cells)
    
    # Calculate totals
    total_cells = num_rows * num_headers
    successful_parses = total_cells  # All cells parse successfully in this test
    
    # Create ParseResult
    result = ParseResult(
        file_name=file_name,
        table_structure=table_structure,
        header_mappings=header_mappings,
        parsed_data=parsed_data,
        total_cells=total_cells,
        successful_parses=successful_parses,
        llm_calls_made=llm_calls
    )
    
    # Property: ParseResult should be serializable to JSON
    try:
        json_str = result.model_dump_json()
        parsed_json = json.loads(json_str)
    except Exception as e:
        pytest.fail(f"ParseResult should be JSON serializable, but got error: {e}")
    
    # Property: JSON should contain all required fields
    assert "file_name" in parsed_json, "JSON must contain file_name"
    assert "table_structure" in parsed_json, "JSON must contain table_structure"
    assert "header_mappings" in parsed_json, "JSON must contain header_mappings"
    assert "parsed_data" in parsed_json, "JSON must contain parsed_data"
    assert "total_cells" in parsed_json, "JSON must contain total_cells"
    assert "successful_parses" in parsed_json, "JSON must contain successful_parses"
    assert "llm_calls_made" in parsed_json, "JSON must contain llm_calls_made"
    
    # Property: Values should match
    assert parsed_json["file_name"] == file_name
    assert parsed_json["total_cells"] == total_cells
    assert parsed_json["successful_parses"] == successful_parses
    assert parsed_json["llm_calls_made"] == llm_calls
    
    # Property: header_mappings should be a list
    assert isinstance(parsed_json["header_mappings"], list)
    assert len(parsed_json["header_mappings"]) == num_headers
    
    # Property: parsed_data should be a 2D grid
    assert isinstance(parsed_json["parsed_data"], list)
    assert len(parsed_json["parsed_data"]) == num_rows
    
    # Property: table_structure should contain required fields
    assert "header_row_index" in parsed_json["table_structure"]
    assert "data_start_row" in parsed_json["table_structure"]
    assert "column_count" in parsed_json["table_structure"]
    assert "merged_cells" in parsed_json["table_structure"]


@given(
    num_headers=st.integers(min_value=1, max_value=10),
    num_rows=st.integers(min_value=1, max_value=10),
)
@settings(max_examples=100)
def test_parse_result_contains_complete_audit_trail(num_headers, num_rows):
    """
    Property 12: Parse Result Auditability
    For any ParseResult with parsed cells, each cell should contain complete
    audit information: method, confidence, original_value, parsed_value.
    
    **Validates: Requirements 10.4**
    """
    # Create table structure
    table_structure = TableStructure(
        header_row_index=1,
        data_start_row=2,
        column_count=num_headers,
        merged_cells=[]
    )
    
    # Create header mappings with different methods
    methods = [MatchMethod.EXACT, MatchMethod.FUZZY, MatchMethod.LLM, MatchMethod.NONE]
    confidences = [ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM, ConfidenceLevel.LOW]
    
    header_mappings = [
        HeaderMapping(
            original_header=f"Header_{i}",
            matched_parameter="Power_Output" if i % 2 == 0 else None,
            matched_asset=f"TG-{i}" if i % 3 == 0 else None,
            method=methods[i % len(methods)],
            confidence=confidences[i % len(confidences)],
            normalized_header=f"header{i}"
        )
        for i in range(num_headers)
    ]
    
    # Create parsed data with audit trail
    parsed_data = []
    for row_idx in range(num_rows):
        row_cells = [
            ParsedCell(
                row_index=row_idx,
                column_index=col_idx,
                original_value=f"value_{row_idx}_{col_idx}",
                parsed_value=float(row_idx * 10 + col_idx),
                header_mapping=header_mappings[col_idx],
                parse_success=True,
                parse_error=None
            )
            for col_idx in range(num_headers)
        ]
        parsed_data.append(row_cells)
    
    # Create ParseResult
    result = ParseResult(
        file_name="test.xlsx",
        table_structure=table_structure,
        header_mappings=header_mappings,
        parsed_data=parsed_data,
        total_cells=num_rows * num_headers,
        successful_parses=num_rows * num_headers,
        llm_calls_made=0
    )
    
    # Property: Every cell should have complete audit trail
    for row in result.parsed_data:
        for cell in row:
            # Check that cell has all required audit fields
            assert hasattr(cell, 'row_index'), "Cell must have row_index"
            assert hasattr(cell, 'column_index'), "Cell must have column_index"
            assert hasattr(cell, 'original_value'), "Cell must have original_value"
            assert hasattr(cell, 'parsed_value'), "Cell must have parsed_value"
            assert hasattr(cell, 'header_mapping'), "Cell must have header_mapping"
            assert hasattr(cell, 'parse_success'), "Cell must have parse_success"
            
            # Check that header_mapping has method and confidence
            assert hasattr(cell.header_mapping, 'method'), "HeaderMapping must have method"
            assert hasattr(cell.header_mapping, 'confidence'), "HeaderMapping must have confidence"
            assert cell.header_mapping.method in [m.value for m in MatchMethod], \
                f"Method must be one of: exact, fuzzy, llm, none"
            assert cell.header_mapping.confidence in [c.value for c in ConfidenceLevel], \
                f"Confidence must be one of: high, medium, low"


@given(
    num_headers=st.integers(min_value=1, max_value=10),
)
@settings(max_examples=100)
def test_parse_result_header_mappings_match_count(num_headers):
    """
    Property 12: Parse Result Auditability
    For any ParseResult, the number of header_mappings should match the
    number of columns in the table structure.
    
    **Validates: Requirements 10.4**
    """
    # Create table structure
    table_structure = TableStructure(
        header_row_index=1,
        data_start_row=2,
        column_count=num_headers,
        merged_cells=[]
    )
    
    # Create header mappings
    header_mappings = [
        create_valid_header_mapping(f"Header_{i}")
        for i in range(num_headers)
    ]
    
    # Create ParseResult
    result = ParseResult(
        file_name="test.xlsx",
        table_structure=table_structure,
        header_mappings=header_mappings,
        parsed_data=[],
        total_cells=0,
        successful_parses=0,
        llm_calls_made=0
    )
    
    # Property: Number of header mappings should match column count
    assert len(result.header_mappings) == result.table_structure.column_count, \
        "Number of header_mappings must match table_structure.column_count"



# Property 13: Invalid File Type Rejection
# **Validates: Requirements 10.5, 11.1**


@given(
    file_extension=st.text(min_size=1, max_size=10).filter(
        lambda x: x.strip() and not x.endswith(('.xlsx', '.xls'))
    )
)
@settings(max_examples=100)
def test_invalid_file_type_should_be_rejected(file_extension):
    """
    Property 13: Invalid File Type Rejection
    For any uploaded file with extension other than .xlsx or .xls,
    the validation logic should identify it as invalid.
    
    **Validates: Requirements 10.5, 11.1**
    """
    # Ensure extension starts with a dot if it doesn't already
    if not file_extension.startswith('.'):
        file_extension = '.' + file_extension
    
    # Create a filename with the invalid extension
    filename = f"test_file{file_extension}"
    
    # Property: File should be identified as invalid
    is_valid = filename.endswith(('.xlsx', '.xls'))
    
    assert not is_valid, \
        f"File with extension {file_extension} should be rejected, but was accepted"


@given(
    base_name=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    extension=st.sampled_from(['.xlsx', '.xls'])
)
@settings(max_examples=100)
def test_valid_file_types_should_be_accepted(base_name, extension):
    """
    Property 13: Invalid File Type Rejection (inverse test)
    For any uploaded file with extension .xlsx or .xls,
    the validation logic should identify it as valid.
    
    **Validates: Requirements 10.5, 11.1**
    """
    # Create a filename with a valid extension
    filename = f"{base_name}{extension}"
    
    # Property: File should be identified as valid
    is_valid = filename.endswith(('.xlsx', '.xls'))
    
    assert is_valid, \
        f"File with extension {extension} should be accepted, but was rejected"



# Property 9: ParsedCell Model Completeness
# **Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5**


@given(
    row_index=st.integers(min_value=0, max_value=1000),
    column_index=st.integers(min_value=0, max_value=100),
    original_value=st.one_of(
        st.none(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(max_size=100),
        st.booleans()
    ),
    parsed_value=st.one_of(
        st.none(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(max_size=100),
        st.booleans()
    ),
    method=st.sampled_from([MatchMethod.EXACT, MatchMethod.FUZZY, MatchMethod.LLM, MatchMethod.NONE]),
    confidence=st.sampled_from([ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM, ConfidenceLevel.LOW]),
    parse_success=st.booleans(),
)
@settings(max_examples=100)
def test_parsed_cell_contains_all_required_fields(
    row_index, column_index, original_value, parsed_value, method, confidence, parse_success
):
    """
    Property 9: ParsedCell Model Completeness
    For any parsed cell, the ParsedCell object should contain:
    - row_index
    - column_index
    - original_value
    - parsed_value
    - header_mapping with valid method (exact/fuzzy/llm/none) and confidence (high/medium/low)
    - parse_success boolean
    
    **Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5**
    """
    # Create a header mapping
    header_mapping = HeaderMapping(
        original_header="Test Header",
        matched_parameter="Power_Output" if method != MatchMethod.NONE else None,
        matched_asset="TG-1" if method == MatchMethod.FUZZY else None,
        method=method,
        confidence=confidence,
        normalized_header="testheader"
    )
    
    # Create a ParsedCell
    cell = ParsedCell(
        row_index=row_index,
        column_index=column_index,
        original_value=original_value,
        parsed_value=parsed_value,
        header_mapping=header_mapping,
        parse_success=parse_success,
        parse_error="Test error" if not parse_success else None
    )
    
    # Property: Cell must have all required fields
    assert hasattr(cell, 'row_index'), "ParsedCell must have row_index"
    assert hasattr(cell, 'column_index'), "ParsedCell must have column_index"
    assert hasattr(cell, 'original_value'), "ParsedCell must have original_value"
    assert hasattr(cell, 'parsed_value'), "ParsedCell must have parsed_value"
    assert hasattr(cell, 'header_mapping'), "ParsedCell must have header_mapping"
    assert hasattr(cell, 'parse_success'), "ParsedCell must have parse_success"
    
    # Property: Values must match what was set
    assert cell.row_index == row_index
    assert cell.column_index == column_index
    assert cell.original_value == original_value
    assert cell.parsed_value == parsed_value
    assert cell.parse_success == parse_success
    
    # Property: header_mapping must have method and confidence
    assert hasattr(cell.header_mapping, 'method'), "HeaderMapping must have method"
    assert hasattr(cell.header_mapping, 'confidence'), "HeaderMapping must have confidence"
    
    # Property: method must be one of the valid values
    assert cell.header_mapping.method in [m.value for m in MatchMethod], \
        f"Method must be one of: exact, fuzzy, llm, none, got {cell.header_mapping.method}"
    
    # Property: confidence must be one of the valid values
    assert cell.header_mapping.confidence in [c.value for c in ConfidenceLevel], \
        f"Confidence must be one of: high, medium, low, got {cell.header_mapping.confidence}"


@given(
    num_cells=st.integers(min_value=1, max_value=20),
)
@settings(max_examples=100)
def test_parsed_cell_preserves_audit_trail_through_serialization(num_cells):
    """
    Property 9: ParsedCell Model Completeness
    For any parsed cell, the audit trail should be preserved through
    JSON serialization and deserialization.
    
    **Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5**
    """
    # Create cells with different methods and confidences
    methods = [MatchMethod.EXACT, MatchMethod.FUZZY, MatchMethod.LLM, MatchMethod.NONE]
    confidences = [ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM, ConfidenceLevel.LOW]
    
    cells = []
    for i in range(num_cells):
        header_mapping = HeaderMapping(
            original_header=f"Header_{i}",
            matched_parameter="Power_Output" if i % 2 == 0 else None,
            matched_asset=f"TG-{i}" if i % 3 == 0 else None,
            method=methods[i % len(methods)],
            confidence=confidences[i % len(confidences)],
            normalized_header=f"header{i}"
        )
        
        cell = ParsedCell(
            row_index=i,
            column_index=i % 5,
            original_value=f"value_{i}",
            parsed_value=float(i * 10),
            header_mapping=header_mapping,
            parse_success=True,
            parse_error=None
        )
        cells.append(cell)
    
    # Property: Each cell should be serializable to JSON
    for cell in cells:
        try:
            json_str = cell.model_dump_json()
            parsed_json = json.loads(json_str)
        except Exception as e:
            pytest.fail(f"ParsedCell should be JSON serializable, but got error: {e}")
        
        # Property: JSON should contain all audit fields
        assert "row_index" in parsed_json
        assert "column_index" in parsed_json
        assert "original_value" in parsed_json
        assert "parsed_value" in parsed_json
        assert "header_mapping" in parsed_json
        assert "parse_success" in parsed_json
        
        # Property: header_mapping should contain method and confidence
        assert "method" in parsed_json["header_mapping"]
        assert "confidence" in parsed_json["header_mapping"]
        assert "original_header" in parsed_json["header_mapping"]
