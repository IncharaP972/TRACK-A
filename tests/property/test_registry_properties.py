"""
Property-based tests for Registry Manager asset extraction.

Feature: latspace-excel-parser
"""

import pytest
from hypothesis import given, strategies as st

from app.registry.data import RegistryManager


# Property 3: Asset Pattern Extraction Completeness
# **Validates: Requirements 2.5, 5.1, 5.2, 5.3, 5.4, 5.5**


# Strategy to generate valid asset identifiers
@st.composite
def valid_asset_identifier(draw):
    r"""
    Generate valid asset identifiers matching the registry patterns.
    
    Patterns supported:
    - AFBC[-_]?\d+
    - TG[-_]?\d+
    - ESP[-_]?\d+
    - APH[-_]?\d+
    - FD[-_]?FAN[-_]?\d+
    - ID[-_]?FAN[-_]?\d+
    - PA[-_]?FAN[-_]?\d+
    - BOILER[-_]?\d+
    - TURBINE[-_]?\d+
    - GENERATOR[-_]?\d+
    - CONDENSER[-_]?\d+
    - ECONOMIZER[-_]?\d+
    """
    # Choose an asset type
    asset_types = [
        "AFBC", "TG", "ESP", "APH", "BOILER", "TURBINE", 
        "GENERATOR", "CONDENSER", "ECONOMIZER"
    ]
    fan_types = ["FD_FAN", "ID_FAN", "PA_FAN"]
    
    asset_type = draw(st.sampled_from(asset_types + fan_types))
    
    # Choose separator (none, dash, or underscore)
    separator = draw(st.sampled_from(["", "-", "_"]))
    
    # Generate asset number (1-99)
    asset_number = draw(st.integers(min_value=1, max_value=99))
    
    # Build the identifier
    if asset_type in fan_types:
        # Handle fan types specially (e.g., FD_FAN, ID_FAN)
        base = asset_type.replace("_", separator) if separator else asset_type.replace("_", "")
        identifier = f"{base}{separator}{asset_number}"
    else:
        identifier = f"{asset_type}{separator}{asset_number}"
    
    # Vary the case
    case_variation = draw(st.sampled_from(["upper", "lower", "mixed"]))
    if case_variation == "lower":
        identifier = identifier.lower()
    elif case_variation == "mixed":
        # Mix case randomly
        identifier = "".join(
            c.upper() if draw(st.booleans()) else c.lower() 
            for c in identifier
        )
    
    return identifier, asset_type


@given(
    asset_data=valid_asset_identifier(),
    prefix=st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs")), max_size=20),
    suffix=st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs")), max_size=20),
)
def test_asset_pattern_extraction_completeness(asset_data, prefix, suffix):
    """
    Property 3: Asset Pattern Extraction Completeness
    
    For any header containing a valid asset identifier pattern (e.g., "AFBC-1", "TG-2"),
    the Tier 2 matcher should extract the asset identifier correctly.
    
    This test generates headers with valid asset identifiers embedded in various contexts
    (with prefixes and suffixes) and verifies that extract_asset finds them.
    
    **Validates: Requirements 2.5, 5.1, 5.2, 5.3, 5.4, 5.5**
    """
    identifier, expected_asset_type = asset_data
    
    # Create header with asset identifier embedded
    header = f"{prefix} {identifier} {suffix}".strip()
    
    # Skip if the header is empty or just the identifier
    if not header or header == identifier:
        header = identifier
    
    # Initialize registry
    registry = RegistryManager()
    
    # Extract asset from header
    result = registry.extract_asset(header)
    
    # Verify extraction succeeded
    assert result is not None, f"Failed to extract asset from header: '{header}'"
    
    extracted_type, extracted_id = result
    
    # Verify the extracted asset type matches expected
    # Note: For fan types, the pattern name includes _FAN
    assert extracted_type == expected_asset_type, (
        f"Expected asset type '{expected_asset_type}' but got '{extracted_type}' "
        f"from header: '{header}'"
    )
    
    # Verify the extracted identifier is present in the header
    assert extracted_id.upper() in header.upper(), (
        f"Extracted identifier '{extracted_id}' not found in header: '{header}'"
    )
    
    # Verify the extracted identifier matches the pattern
    # The extracted ID should contain the asset type and number
    normalized_id = extracted_id.upper().replace("-", "").replace("_", "")
    normalized_expected = identifier.upper().replace("-", "").replace("_", "")
    
    assert normalized_id == normalized_expected, (
        f"Extracted identifier '{extracted_id}' doesn't match expected '{identifier}' "
        f"from header: '{header}'"
    )


@given(
    asset_data=valid_asset_identifier(),
)
def test_asset_extraction_returns_correct_format(asset_data):
    """
    Property 3: Asset Pattern Extraction Completeness
    
    Verify that extract_asset returns a tuple of (asset_type, asset_identifier)
    when a valid asset pattern is found.
    
    **Validates: Requirements 5.2**
    """
    identifier, expected_asset_type = asset_data
    
    registry = RegistryManager()
    result = registry.extract_asset(identifier)
    
    # Verify result is a tuple
    assert isinstance(result, tuple), f"Expected tuple, got {type(result)}"
    assert len(result) == 2, f"Expected tuple of length 2, got {len(result)}"
    
    asset_type, asset_id = result
    
    # Verify types
    assert isinstance(asset_type, str), f"Asset type should be string, got {type(asset_type)}"
    assert isinstance(asset_id, str), f"Asset ID should be string, got {type(asset_id)}"
    
    # Verify asset type is from registry
    assert asset_type in registry.assets, (
        f"Asset type '{asset_type}' not found in registry"
    )


@given(
    asset_data=valid_asset_identifier(),
    context_words=st.lists(
        st.sampled_from([
            "Power", "Temperature", "Efficiency", "Output", "Input",
            "Pressure", "Flow", "Rate", "Level", "Status"
        ]),
        min_size=0,
        max_size=3
    )
)
def test_asset_extraction_with_parameter_context(asset_data, context_words):
    """
    Property 3: Asset Pattern Extraction Completeness
    
    Verify that asset extraction works when the header contains both
    asset identifiers and parameter context (e.g., "Power TG1", "TG-1 Temperature").
    
    This validates Requirement 5.3: combining asset with parameter context.
    
    **Validates: Requirements 5.3**
    """
    identifier, expected_asset_type = asset_data
    
    # Build header with parameter context
    context = " ".join(context_words)
    
    # Test both orderings: parameter before asset and asset before parameter
    headers = [
        f"{context} {identifier}".strip(),
        f"{identifier} {context}".strip(),
    ]
    
    registry = RegistryManager()
    
    for header in headers:
        if not header:
            continue
            
        result = registry.extract_asset(header)
        
        assert result is not None, (
            f"Failed to extract asset from header with context: '{header}'"
        )
        
        extracted_type, extracted_id = result
        assert extracted_type == expected_asset_type, (
            f"Expected '{expected_asset_type}' but got '{extracted_type}' "
            f"from header: '{header}'"
        )
