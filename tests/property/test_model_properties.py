"""
Property-based tests for Pydantic model validation.

Feature: latspace-excel-parser
"""

import pytest
from hypothesis import given, strategies as st
from pydantic import ValidationError

from app.schema.models import (
    HeaderMapping,
    ParsedCell,
    TableStructure,
    ParseResult,
    LLMMatchRequest,
    LLMMatchResponse,
    MatchMethod,
    ConfidenceLevel,
)


# Property 15: Pydantic Model Validation
# **Validates: Requirements 11.5**


@given(
    original_header=st.one_of(
        st.just(""),  # Empty string
        st.just("   "),  # Whitespace only
    )
)
def test_header_mapping_rejects_empty_original_header(original_header):
    """
    Property 15: Pydantic Model Validation
    For any invalid data passed to HeaderMapping with empty original_header,
    validation should raise ValidationError.
    
    **Validates: Requirements 11.5**
    """
    with pytest.raises(ValidationError) as exc_info:
        HeaderMapping(
            original_header=original_header,
            method=MatchMethod.EXACT,
            confidence=ConfidenceLevel.HIGH,
        )
    
    # Verify ValidationError contains details about the constraint violation
    assert "original_header" in str(exc_info.value)


@given(
    matched_field=st.one_of(
        st.just(""),  # Empty string
        st.just("   "),  # Whitespace only
    )
)
def test_header_mapping_rejects_empty_matched_fields(matched_field):
    """
    Property 15: Pydantic Model Validation
    For any invalid data passed to HeaderMapping with empty matched_parameter or matched_asset,
    validation should raise ValidationError.
    
    **Validates: Requirements 11.5**
    """
    with pytest.raises(ValidationError) as exc_info:
        HeaderMapping(
            original_header="Valid Header",
            matched_parameter=matched_field,
            method=MatchMethod.EXACT,
            confidence=ConfidenceLevel.HIGH,
        )
    
    assert "matched" in str(exc_info.value).lower()


@given(
    row_index=st.integers(max_value=-1),
    column_index=st.integers(max_value=-1),
)
def test_parsed_cell_rejects_negative_indices(row_index, column_index):
    """
    Property 15: Pydantic Model Validation
    For any invalid data passed to ParsedCell with negative indices,
    validation should raise ValidationError.
    
    **Validates: Requirements 11.5**
    """
    header_mapping = HeaderMapping(
        original_header="Test Header",
        method=MatchMethod.EXACT,
        confidence=ConfidenceLevel.HIGH,
    )
    
    with pytest.raises(ValidationError) as exc_info:
        ParsedCell(
            row_index=row_index,
            column_index=column_index,
            original_value="test",
            header_mapping=header_mapping,
        )
    
    error_str = str(exc_info.value)
    assert "row_index" in error_str or "column_index" in error_str


@given(
    header_row_index=st.integers(max_value=0),
    data_start_row=st.integers(max_value=0),
    column_count=st.integers(max_value=0),
)
def test_table_structure_rejects_non_positive_values(
    header_row_index, data_start_row, column_count
):
    """
    Property 15: Pydantic Model Validation
    For any invalid data passed to TableStructure with non-positive values,
    validation should raise ValidationError.
    
    **Validates: Requirements 11.5**
    """
    with pytest.raises(ValidationError) as exc_info:
        TableStructure(
            header_row_index=header_row_index,
            data_start_row=data_start_row,
            column_count=column_count,
        )
    
    error_str = str(exc_info.value)
    assert any(
        field in error_str
        for field in ["header_row_index", "data_start_row", "column_count"]
    )


@given(
    header_row_index=st.integers(min_value=2, max_value=100),
    offset=st.integers(min_value=0, max_value=10),
)
def test_table_structure_rejects_invalid_data_start_row(header_row_index, offset):
    """
    Property 15: Pydantic Model Validation
    For any invalid data passed to TableStructure where data_start_row <= header_row_index,
    validation should raise ValidationError.
    
    **Validates: Requirements 11.5**
    """
    # data_start_row must be > header_row_index
    # Generate invalid data_start_row that is <= header_row_index
    invalid_data_start_row = header_row_index - offset
    
    with pytest.raises(ValidationError) as exc_info:
        TableStructure(
            header_row_index=header_row_index,
            data_start_row=invalid_data_start_row,
            column_count=5,
        )
    
    assert "data_start_row" in str(exc_info.value)


@given(
    file_name=st.one_of(
        st.just(""),  # Empty string
        st.just("   "),  # Whitespace only
    )
)
def test_parse_result_rejects_empty_file_name(file_name):
    """
    Property 15: Pydantic Model Validation
    For any invalid data passed to ParseResult with empty file_name,
    validation should raise ValidationError.
    
    **Validates: Requirements 11.5**
    """
    table_structure = TableStructure(
        header_row_index=1,
        data_start_row=2,
        column_count=5,
    )
    
    with pytest.raises(ValidationError) as exc_info:
        ParseResult(
            file_name=file_name,
            table_structure=table_structure,
            header_mappings=[],
            parsed_data=[],
            total_cells=0,
            successful_parses=0,
            llm_calls_made=0,
        )
    
    assert "file_name" in str(exc_info.value)


@given(
    total_cells=st.integers(min_value=0, max_value=100),
    successful_parses=st.integers(min_value=101, max_value=200),
)
def test_parse_result_rejects_successful_parses_exceeding_total(
    total_cells, successful_parses
):
    """
    Property 15: Pydantic Model Validation
    For any invalid data passed to ParseResult where successful_parses > total_cells,
    validation should raise ValidationError.
    
    **Validates: Requirements 11.5**
    """
    table_structure = TableStructure(
        header_row_index=1,
        data_start_row=2,
        column_count=5,
    )
    
    with pytest.raises(ValidationError) as exc_info:
        ParseResult(
            file_name="test.xlsx",
            table_structure=table_structure,
            header_mappings=[],
            parsed_data=[],
            total_cells=total_cells,
            successful_parses=successful_parses,
            llm_calls_made=0,
        )
    
    assert "successful_parses" in str(exc_info.value)


@given(
    count=st.integers(max_value=-1),
)
def test_parse_result_rejects_negative_counts(count):
    """
    Property 15: Pydantic Model Validation
    For any invalid data passed to ParseResult with negative counts,
    validation should raise ValidationError.
    
    **Validates: Requirements 11.5**
    """
    table_structure = TableStructure(
        header_row_index=1,
        data_start_row=2,
        column_count=5,
    )
    
    with pytest.raises(ValidationError) as exc_info:
        ParseResult(
            file_name="test.xlsx",
            table_structure=table_structure,
            header_mappings=[],
            parsed_data=[],
            total_cells=count,
            successful_parses=0,
            llm_calls_made=0,
        )
    
    error_str = str(exc_info.value)
    assert "total_cells" in error_str or "successful_parses" in error_str or "llm_calls_made" in error_str


def test_llm_match_request_rejects_empty_lists():
    """
    Property 15: Pydantic Model Validation
    For any invalid data passed to LLMMatchRequest with empty lists,
    validation should raise ValidationError.
    
    **Validates: Requirements 11.5**
    """
    with pytest.raises(ValidationError) as exc_info:
        LLMMatchRequest(
            unmapped_headers=[],
            registry_parameters=["param1"],
            registry_assets=["asset1"],
        )
    
    assert "unmapped_headers" in str(exc_info.value)


def test_llm_match_response_rejects_non_llm_method():
    """
    Property 15: Pydantic Model Validation
    For any invalid data passed to LLMMatchResponse with non-LLM method mappings,
    validation should raise ValidationError.
    
    **Validates: Requirements 11.5**
    """
    invalid_mapping = HeaderMapping(
        original_header="Test Header",
        method=MatchMethod.EXACT,  # Should be LLM
        confidence=ConfidenceLevel.HIGH,
    )
    
    with pytest.raises(ValidationError) as exc_info:
        LLMMatchResponse(mappings=[invalid_mapping])
    
    assert "method" in str(exc_info.value) or "llm" in str(exc_info.value).lower()
