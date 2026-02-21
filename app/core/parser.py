"""
Deterministic value parser for Excel cell values.
NO LLM usage - only regex and string processing.
"""

import re
from typing import Any, Optional, Union, List
from app.schema.models import ParsedCell, HeaderMapping


def parse_value(value: Any) -> Optional[Union[float, str]]:
    """
    Deterministically parse Excel cell values.
    
    Handles:
    - None and empty strings → None
    - N/A variations (N/A, NA, NULL, NONE, -) → None
    - YES → 1.0, NO → 0.0
    - Percentages: "45%" → 0.45
    - Numbers with commas: "1,234.56" → 1234.56
    - Negative numbers
    - Unparseable values → returned as strings
    
    Args:
        value: The cell value to parse
        
    Returns:
        Parsed value as float, string, or None
    """
    # Handle None and empty string
    if value is None or value == "":
        return None
    
    # Convert to string for processing
    str_value = str(value).strip()
    
    # Handle empty string after stripping
    if not str_value:
        return None
    
    # Handle N/A variations (case-insensitive)
    if str_value.upper() in ["N/A", "NA", "NULL", "NONE", "-"]:
        return None
    
    # Handle boolean YES/NO (case-insensitive)
    if str_value.upper() == "YES":
        return 1.0
    if str_value.upper() == "NO":
        return 0.0
    
    # Handle percentages: "45%" → 0.45
    # Pattern matches: optional negative, digits with optional commas, optional decimal, followed by %
    percent_match = re.match(r'^(-?[\d,]+\.?\d*)\s*%$', str_value)
    if percent_match:
        numeric_part = percent_match.group(1).replace(',', '')
        try:
            return float(numeric_part) / 100.0
        except ValueError:
            return str_value
    
    # Handle negative numbers with commas: "-1,234.56" → -1234.56
    negative_match = re.match(r'^-[\d,]+\.?\d*$', str_value)
    if negative_match:
        try:
            return float(str_value.replace(',', ''))
        except ValueError:
            return str_value
    
    # Handle positive numbers with commas: "1,234.56" → 1234.56
    numeric_match = re.match(r'^[\d,]+\.?\d*$', str_value)
    if numeric_match:
        try:
            return float(str_value.replace(',', ''))
        except ValueError:
            return str_value
    
    # If no pattern matches, return as string
    return str_value


def parse_row(row_values: List[Any], header_mappings: List[HeaderMapping], row_index: int = 0) -> List[ParsedCell]:
    """
    Parse an entire row of values with header context.
    
    Creates a ParsedCell for each value with complete audit trail.
    Handles parsing exceptions gracefully by setting parse_success=False
    and preserving the original value.
    
    Args:
        row_values: List of cell values from the Excel row
        header_mappings: List of HeaderMapping objects for each column
        row_index: The row index in the Excel file (default: 0, should be set by caller)
        
    Returns:
        List of ParsedCell objects with parsed values and audit information
        
    Requirements:
        - 9.1: Create ParsedCell model for each processed cell
        - 9.4: Include original value and parsed value
        - 11.4: Handle parsing exceptions gracefully
    """
    parsed_cells = []
    
    # Ensure we have the same number of values and mappings
    # If not, pad with None values or truncate
    max_len = max(len(row_values), len(header_mappings))
    
    for col_idx in range(max_len):
        # Get value and mapping, using None if index is out of range
        value = row_values[col_idx] if col_idx < len(row_values) else None
        mapping = header_mappings[col_idx] if col_idx < len(header_mappings) else None
        
        # If no mapping exists, create a default one
        if mapping is None:
            from app.schema.models import MatchMethod, ConfidenceLevel
            mapping = HeaderMapping(
                original_header=f"Column_{col_idx}",
                method=MatchMethod.NONE,
                confidence=ConfidenceLevel.LOW
            )
        
        try:
            # Parse the value using the deterministic parser
            parsed = parse_value(value)
            
            # Create ParsedCell with successful parse
            cell = ParsedCell(
                row_index=row_index,
                column_index=col_idx,
                original_value=value,
                parsed_value=parsed,
                header_mapping=mapping,
                parse_success=True,
                parse_error=None
            )
        except Exception as e:
            # Handle parsing exceptions gracefully
            # Preserve original value and record the error
            cell = ParsedCell(
                row_index=row_index,
                column_index=col_idx,
                original_value=value,
                parsed_value=None,
                header_mapping=mapping,
                parse_success=False,
                parse_error=str(e)
            )
        
        parsed_cells.append(cell)
    
    return parsed_cells
