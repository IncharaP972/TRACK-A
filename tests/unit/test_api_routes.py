"""
Unit tests for API endpoints.

Tests the /parse endpoint with various scenarios including:
- Valid Excel files
- Invalid file types
- Corrupted Excel files
- Error responses
"""

import pytest
from fastapi.testclient import TestClient
from io import BytesIO
import openpyxl
from unittest.mock import patch, MagicMock

from app.main import app
from app.schema.models import MatchMethod, ConfidenceLevel


# Create test client - use fixture to avoid initialization issues
@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


def create_test_excel_file() -> BytesIO:
    """Create a simple test Excel file in memory."""
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    
    # Add headers
    sheet['A1'] = 'Power_Output'
    sheet['B1'] = 'Temperature'
    sheet['C1'] = 'TG-1 Efficiency'
    
    # Add data rows
    sheet['A2'] = 1234.56
    sheet['B2'] = 450
    sheet['C2'] = '85%'
    
    sheet['A3'] = 2345.67
    sheet['B3'] = 475
    sheet['C3'] = '87%'
    
    # Save to BytesIO
    excel_file = BytesIO()
    workbook.save(excel_file)
    excel_file.seek(0)
    
    return excel_file


def test_root_endpoint(client):
    """Test the root endpoint returns API information."""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "description" in data
    assert data["name"] == "LatSpace Intelligent Excel Parser"


def test_health_check_endpoint(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_parse_endpoint_with_valid_excel_file(client):
    """
    Test /parse endpoint with a valid Excel file.
    
    Requirements: 10.1
    """
    # Create test Excel file
    excel_file = create_test_excel_file()
    
    # Upload file
    response = client.post(
        "/api/parse",
        files={"file": ("test.xlsx", excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    
    # Verify ParseResult structure
    assert "file_name" in data
    assert data["file_name"] == "test.xlsx"
    
    assert "table_structure" in data
    assert "header_row_index" in data["table_structure"]
    assert "data_start_row" in data["table_structure"]
    assert "column_count" in data["table_structure"]
    
    assert "header_mappings" in data
    assert isinstance(data["header_mappings"], list)
    assert len(data["header_mappings"]) > 0
    
    assert "parsed_data" in data
    assert isinstance(data["parsed_data"], list)
    
    assert "total_cells" in data
    assert "successful_parses" in data
    assert "llm_calls_made" in data
    
    # Verify at least one header was matched
    exact_matches = [m for m in data["header_mappings"] if m["method"] == "exact"]
    assert len(exact_matches) > 0, "Should have at least one exact match"


def test_parse_endpoint_with_invalid_file_type(client):
    """
    Test /parse endpoint with invalid file type.
    Should return HTTP 400 error.
    
    Requirements: 10.5, 11.1
    """
    # Create a fake text file
    text_file = BytesIO(b"This is not an Excel file")
    
    # Upload file with .txt extension
    response = client.post(
        "/api/parse",
        files={"file": ("test.txt", text_file, "text/plain")}
    )
    
    # Check response
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Excel" in data["detail"] or "xlsx" in data["detail"] or "xls" in data["detail"]


def test_parse_endpoint_with_pdf_file(client):
    """
    Test /parse endpoint with PDF file.
    Should return HTTP 400 error.
    
    Requirements: 10.5, 11.1
    """
    # Create a fake PDF file
    pdf_file = BytesIO(b"%PDF-1.4 fake pdf content")
    
    # Upload file with .pdf extension
    response = client.post(
        "/api/parse",
        files={"file": ("test.pdf", pdf_file, "application/pdf")}
    )
    
    # Check response
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Excel" in data["detail"] or "xlsx" in data["detail"] or "xls" in data["detail"]


def test_parse_endpoint_with_empty_file(client):
    """
    Test /parse endpoint with empty file.
    Should return HTTP 400 error.
    
    Requirements: 11.1
    """
    # Create empty file
    empty_file = BytesIO(b"")
    
    # Upload empty file
    response = client.post(
        "/api/parse",
        files={"file": ("test.xlsx", empty_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    )
    
    # Check response
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "empty" in data["detail"].lower()


def test_parse_endpoint_with_corrupted_excel_file(client):
    """
    Test /parse endpoint with corrupted Excel file.
    Should return HTTP 400 error.
    
    Requirements: 11.1
    """
    # Create corrupted Excel file (just random bytes)
    corrupted_file = BytesIO(b"PK\x03\x04corrupted data that looks like zip but isn't valid Excel")
    
    # Upload corrupted file
    response = client.post(
        "/api/parse",
        files={"file": ("test.xlsx", corrupted_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    )
    
    # Check response - should be 400 or 500
    assert response.status_code in [400, 500]
    data = response.json()
    assert "detail" in data


def test_parse_endpoint_without_file(client):
    """
    Test /parse endpoint without uploading a file.
    Should return HTTP 422 error (validation error).
    """
    # Make request without file
    response = client.post("/api/parse")
    
    # Check response
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_parse_endpoint_header_mappings_have_audit_trail(client):
    """
    Test that header mappings in the response contain complete audit trail.
    
    Requirements: 9.2, 9.3
    """
    # Create test Excel file
    excel_file = create_test_excel_file()
    
    # Upload file
    response = client.post(
        "/api/parse",
        files={"file": ("test.xlsx", excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check each header mapping has required fields
    for mapping in data["header_mappings"]:
        assert "original_header" in mapping
        assert "method" in mapping
        assert "confidence" in mapping
        
        # Method should be one of the valid values
        assert mapping["method"] in ["exact", "fuzzy", "llm", "none"]
        
        # Confidence should be one of the valid values
        assert mapping["confidence"] in ["high", "medium", "low"]


def test_parse_endpoint_parsed_cells_have_audit_trail(client):
    """
    Test that parsed cells in the response contain complete audit trail.
    
    Requirements: 9.1, 9.4, 9.5
    """
    # Create test Excel file
    excel_file = create_test_excel_file()
    
    # Upload file
    response = client.post(
        "/api/parse",
        files={"file": ("test.xlsx", excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check parsed data structure
    assert len(data["parsed_data"]) > 0, "Should have at least one data row"
    
    # Check first row of parsed data
    first_row = data["parsed_data"][0]
    assert len(first_row) > 0, "First row should have at least one cell"
    
    # Check first cell has all required fields
    first_cell = first_row[0]
    assert "row_index" in first_cell
    assert "column_index" in first_cell
    assert "original_value" in first_cell
    assert "parsed_value" in first_cell
    assert "header_mapping" in first_cell
    assert "parse_success" in first_cell
    
    # Check header_mapping in cell
    assert "method" in first_cell["header_mapping"]
    assert "confidence" in first_cell["header_mapping"]


def test_parse_endpoint_counts_are_accurate(client):
    """
    Test that total_cells and successful_parses counts are accurate.
    
    Requirements: 10.4
    """
    # Create test Excel file
    excel_file = create_test_excel_file()
    
    # Upload file
    response = client.post(
        "/api/parse",
        files={"file": ("test.xlsx", excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Calculate expected counts
    num_rows = len(data["parsed_data"])
    num_cols = len(data["parsed_data"][0]) if num_rows > 0 else 0
    expected_total = num_rows * num_cols
    
    # Verify counts
    assert data["total_cells"] == expected_total
    assert data["successful_parses"] <= data["total_cells"]
    assert data["successful_parses"] >= 0


def test_parse_endpoint_llm_calls_count(client):
    """
    Test that llm_calls_made is either 0 or 1 (batch call).
    
    Requirements: 3.4, 6.1
    """
    # Create test Excel file
    excel_file = create_test_excel_file()
    
    # Upload file
    response = client.post(
        "/api/parse",
        files={"file": ("test.xlsx", excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # LLM calls should be 0 or 1 (single batch call per file)
    assert data["llm_calls_made"] in [0, 1], \
        "LLM calls should be 0 (no unmapped headers) or 1 (single batch call)"


def test_parse_endpoint_with_xls_extension(client):
    """
    Test /parse endpoint accepts .xls extension.
    
    Requirements: 10.5
    """
    # Create test Excel file
    excel_file = create_test_excel_file()
    
    # Upload file with .xls extension
    response = client.post(
        "/api/parse",
        files={"file": ("test.xls", excel_file, "application/vnd.ms-excel")}
    )
    
    # Should accept .xls files
    assert response.status_code == 200
    data = response.json()
    assert data["file_name"] == "test.xls"
