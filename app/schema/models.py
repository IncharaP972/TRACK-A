"""
Pydantic v2 data models for the LatSpace Intelligent Excel Parser.

This module defines all data structures used throughout the system,
including enums, header mappings, parsed cells, table structures,
and parse results. All models include field validators for data integrity.

Note: Currently using Pydantic v1 syntax for compatibility.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Literal, List, Dict, Any, Union
from enum import Enum


class MatchMethod(str, Enum):
    """Method used for header matching"""
    EXACT = "exact"
    FUZZY = "fuzzy"
    LLM = "llm"
    NONE = "none"


class ConfidenceLevel(str, Enum):
    """Confidence level for header matching"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class HeaderMapping(BaseModel):
    """Represents a mapping from Excel header to registry entry"""
    original_header: str
    matched_parameter: Optional[str] = None
    matched_asset: Optional[str] = None
    method: MatchMethod
    confidence: ConfidenceLevel
    normalized_header: Optional[str] = None

    @validator('original_header')
    def validate_original_header(cls, v: str) -> str:
        """Ensure original_header is not empty"""
        if not v or not v.strip():
            raise ValueError("original_header cannot be empty")
        return v

    @validator('matched_parameter', 'matched_asset')
    def validate_matched_fields(cls, v: Optional[str]) -> Optional[str]:
        """Ensure matched fields are not empty strings if provided"""
        if v is not None and not v.strip():
            raise ValueError("matched fields cannot be empty strings")
        return v


class ParsedCell(BaseModel):
    """Represents a single parsed cell with audit trail"""
    row_index: int
    column_index: int
    original_value: Any
    parsed_value: Optional[Union[float, str, bool]] = None
    header_mapping: HeaderMapping
    parse_success: bool = True
    parse_error: Optional[str] = None

    @validator('row_index', 'column_index')
    def validate_indices(cls, v: int) -> int:
        """Ensure indices are non-negative"""
        if v < 0:
            raise ValueError("row_index and column_index must be non-negative")
        return v


class TableStructure(BaseModel):
    """Represents detected table structure in Excel file"""
    header_row_index: int
    data_start_row: int
    column_count: int
    merged_cells: List[Dict[str, int]] = Field(default_factory=list)

    @validator('header_row_index', 'data_start_row', 'column_count')
    def validate_positive_values(cls, v: int) -> int:
        """Ensure structural indices are positive"""
        if v < 1:
            raise ValueError("header_row_index, data_start_row, and column_count must be >= 1")
        return v

    @validator('data_start_row')
    def validate_data_start_row(cls, v: int, values) -> int:
        """Ensure data_start_row is after header_row_index"""
        if 'header_row_index' in values and v <= values['header_row_index']:
            raise ValueError("data_start_row must be greater than header_row_index")
        return v


class ParseResult(BaseModel):
    """Complete parsing result for an Excel file"""
    file_name: str
    table_structure: TableStructure
    header_mappings: List[HeaderMapping]
    parsed_data: List[List[ParsedCell]]
    total_cells: int
    successful_parses: int
    llm_calls_made: int

    @validator('file_name')
    def validate_file_name(cls, v: str) -> str:
        """Ensure file_name is not empty"""
        if not v or not v.strip():
            raise ValueError("file_name cannot be empty")
        return v

    @validator('total_cells', 'successful_parses', 'llm_calls_made')
    def validate_counts(cls, v: int) -> int:
        """Ensure counts are non-negative"""
        if v < 0:
            raise ValueError("counts must be non-negative")
        return v

    @validator('successful_parses')
    def validate_successful_parses(cls, v: int, values) -> int:
        """Ensure successful_parses does not exceed total_cells"""
        if 'total_cells' in values and v > values['total_cells']:
            raise ValueError("successful_parses cannot exceed total_cells")
        return v


class LLMMatchRequest(BaseModel):
    """Structured request for LLM semantic matching"""
    unmapped_headers: List[str]
    registry_parameters: List[str]
    registry_assets: List[str]

    @validator('unmapped_headers', 'registry_parameters', 'registry_assets')
    def validate_non_empty_lists(cls, v: List[str]) -> List[str]:
        """Ensure lists are not empty"""
        if not v:
            raise ValueError("lists cannot be empty")
        return v


class LLMMatchResponse(BaseModel):
    """Structured response from LLM semantic matching"""
    mappings: List[HeaderMapping]

    @validator('mappings')
    def validate_mappings(cls, v: List[HeaderMapping]) -> List[HeaderMapping]:
        """Ensure all mappings use LLM method"""
        for mapping in v:
            if mapping.method != MatchMethod.LLM:
                raise ValueError("all mappings in LLMMatchResponse must have method='llm'")
        return v
