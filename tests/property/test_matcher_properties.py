"""
Property-based tests for HeaderMatcher three-tier matching strategy.

This module contains property tests that verify universal correctness
properties of the header matching system across randomized inputs.

Test Configuration:
- Library: hypothesis
- Minimum iterations: 100 per property test
- Feature: latspace-excel-parser
"""

import pytest
from hypothesis import given, strategies as st, settings
from app.core.matcher import HeaderMatcher
from app.registry.data import RegistryManager
from app.services.llm import LLMService
from app.schema.models import MatchMethod, ConfidenceLevel
from unittest.mock import Mock, MagicMock


# Initialize registry for tests
registry = RegistryManager()


# Strategy for generating case variations
@st.composite
def case_variation_strategy(draw):
    """Generate different case variations of text."""
    variation = draw(st.sampled_from(['lower', 'upper', 'title', 'mixed']))
    return variation


# Strategy for generating whitespace
whitespace_strategy = st.text(alphabet=' \t\n', min_size=0, max_size=3)


# Strategy for generating special characters
special_chars_strategy = st.text(alphabet='_-.()', min_size=0, max_size=2)


def apply_case_variation(text: str, variation: str) -> str:
    """Apply case variation to text."""
    if variation == 'lower':
        return text.lower()
    elif variation == 'upper':
        return text.upper()
    elif variation == 'title':
        return text.title()
    elif variation == 'mixed':
        # Mix upper and lower randomly
        return ''.join(c.upper() if i % 2 == 0 else c.lower() 
                      for i, c in enumerate(text))
    return text


# Feature: latspace-excel-parser, Property 1: Tier 1 Normalization Invariance
@settings(max_examples=100)
@given(
    base_param=st.sampled_from(registry.parameters),
    case_variation=case_variation_strategy(),
    whitespace_before=whitespace_strategy,
    whitespace_after=whitespace_strategy,
    special_chars=special_chars_strategy
)
def test_tier1_normalization_invariance(
    base_param, 
    case_variation, 
    whitespace_before, 
    whitespace_after, 
    special_chars
):
    """
    **Validates: Requirements 4.1, 4.2, 4.4, 4.5**
    
    Property 1: Tier 1 Normalization Invariance
    
    For any header string and any registry parameter, if the normalized forms
    match, then variations in case, whitespace, and special characters should
    all produce the same exact match result with high confidence and method "exact".
    
    This property ensures that the normalization process is consistent and that
    headers like "Power_Output", "power output", "POWER-OUTPUT", and "  Power  Output  "
    all match to the same parameter with the same confidence level.
    """
    # Create mock LLM service (not used in Tier 1)
    mock_llm = Mock(spec=LLMService)
    matcher = HeaderMatcher(registry, mock_llm)
    
    # Create variation of parameter
    variant = apply_case_variation(base_param, case_variation)
    
    # Add whitespace and special characters
    variant = whitespace_before + variant + special_chars + whitespace_after
    
    # Match the variant using Tier 1
    result = matcher._tier1_exact_match(variant)
    
    # Verify properties
    assert result is not None, f"Failed to match variant '{variant}' of parameter '{base_param}'"
    assert result.matched_parameter == base_param, \
        f"Expected parameter '{base_param}', got '{result.matched_parameter}'"
    assert result.method == MatchMethod.EXACT, \
        f"Expected method EXACT, got {result.method}"
    assert result.confidence == ConfidenceLevel.HIGH, \
        f"Expected confidence HIGH, got {result.confidence}"
    assert result.original_header == variant, \
        f"Original header should be preserved as '{variant}'"
    assert result.normalized_header is not None, \
        "Normalized header should be set"



# Feature: latspace-excel-parser, Property 2: Three-Tier Sequential Matching
@settings(max_examples=100)
@given(
    header_type=st.sampled_from(['exact', 'fuzzy', 'llm', 'none'])
)
def test_three_tier_sequential_matching(header_type):
    """
    **Validates: Requirements 3.1, 3.2, 3.3**
    
    Property 2: Three-Tier Sequential Matching
    
    For any header, the matching process should follow this order: if Tier 1 (exact)
    succeeds, method is "exact"; else if Tier 2 (regex) succeeds, method is "fuzzy";
    else Tier 3 (LLM) is attempted with method "llm" or "none".
    
    This property ensures that the matching tiers are processed sequentially and
    that the method field correctly reflects which tier successfully matched the header.
    """
    # Create mock LLM service
    mock_llm = Mock(spec=LLMService)
    
    # Configure mock to return appropriate responses
    if header_type == 'llm':
        # Mock LLM to return a successful match
        from app.schema.models import HeaderMapping
        mock_llm.batch_match_headers.return_value = [
            HeaderMapping(
                original_header="Unknown Header",
                matched_parameter="Power_Output",
                method=MatchMethod.LLM,
                confidence=ConfidenceLevel.MEDIUM
            )
        ]
    elif header_type == 'none':
        # Mock LLM to return no match
        from app.schema.models import HeaderMapping
        mock_llm.batch_match_headers.return_value = [
            HeaderMapping(
                original_header="Unknown Header",
                matched_parameter=None,
                method=MatchMethod.NONE,
                confidence=ConfidenceLevel.LOW
            )
        ]
    
    matcher = HeaderMatcher(registry, mock_llm)
    
    # Create test headers based on type
    if header_type == 'exact':
        # Use a known parameter that will match in Tier 1
        header = "Power_Output"
        expected_method = MatchMethod.EXACT
    elif header_type == 'fuzzy':
        # Use a header with asset that will match in Tier 2
        header = "TG-1 Unknown"
        expected_method = MatchMethod.FUZZY
    elif header_type == 'llm':
        # Use a header that won't match Tier 1 or 2
        header = "Unknown Header"
        expected_method = MatchMethod.LLM
    else:  # none
        # Use a header that won't match any tier
        header = "Unknown Header"
        expected_method = MatchMethod.NONE
    
    # Match the header
    results = matcher.match_headers([header])
    
    # Verify properties
    assert len(results) == 1, "Should return exactly one mapping"
    result = results[0]
    
    assert result.method == expected_method, \
        f"Expected method {expected_method}, got {result.method}"
    
    # Verify tier precedence
    if header_type == 'exact':
        # Tier 1 should succeed, so confidence should be HIGH
        assert result.confidence == ConfidenceLevel.HIGH
        assert result.matched_parameter is not None
        # LLM should not be called for exact matches
        mock_llm.batch_match_headers.assert_not_called()
    elif header_type == 'fuzzy':
        # Tier 2 should succeed, confidence should be MEDIUM or LOW
        assert result.confidence in [ConfidenceLevel.MEDIUM, ConfidenceLevel.LOW]
        assert result.matched_asset is not None
        # LLM should not be called for fuzzy matches
        mock_llm.batch_match_headers.assert_not_called()
    elif header_type in ['llm', 'none']:
        # Tier 3 should be called
        mock_llm.batch_match_headers.assert_called_once()



# Feature: latspace-excel-parser, Property 4: Single LLM Batch Call Per File
@settings(max_examples=100)
@given(
    num_unmapped=st.integers(min_value=1, max_value=20)
)
def test_single_llm_batch_call_per_file(num_unmapped):
    """
    **Validates: Requirements 3.4, 6.1**
    
    Property 4: Single LLM Batch Call Per File
    
    For any set of headers that fail Tier 1 and Tier 2 matching, all unmapped
    headers should be processed in exactly one LLM API call, regardless of the
    number of unmapped headers.
    
    This property ensures efficiency by batching all LLM requests into a single
    API call per file, minimizing latency and API costs.
    """
    # Create mock LLM service
    mock_llm = Mock(spec=LLMService)
    
    # Configure mock to return appropriate number of mappings
    from app.schema.models import HeaderMapping
    mock_mappings = [
        HeaderMapping(
            original_header=f"Unknown Header {i}",
            matched_parameter=None,
            method=MatchMethod.LLM,
            confidence=ConfidenceLevel.MEDIUM
        )
        for i in range(num_unmapped)
    ]
    mock_llm.batch_match_headers.return_value = mock_mappings
    
    matcher = HeaderMatcher(registry, mock_llm)
    
    # Create a mix of headers: some that match Tier 1, some that don't
    # We'll create headers that won't match Tier 1 or Tier 2
    headers = [f"Unknown Header {i}" for i in range(num_unmapped)]
    
    # Match all headers
    results = matcher.match_headers(headers)
    
    # Verify properties
    assert len(results) == num_unmapped, \
        f"Should return {num_unmapped} mappings, got {len(results)}"
    
    # Critical property: LLM should be called exactly ONCE
    assert mock_llm.batch_match_headers.call_count == 1, \
        f"Expected exactly 1 LLM call, got {mock_llm.batch_match_headers.call_count}"
    
    # Verify that all unmapped headers were sent in the single batch call
    call_args = mock_llm.batch_match_headers.call_args
    assert call_args is not None, "LLM should have been called"
    
    headers_sent = call_args[0][0]  # First positional argument
    assert len(headers_sent) == num_unmapped, \
        f"Expected {num_unmapped} headers in batch call, got {len(headers_sent)}"


# Feature: latspace-excel-parser, Property 4: Single LLM Batch Call with Mixed Headers
@settings(max_examples=100)
@given(
    num_exact=st.integers(min_value=0, max_value=5),
    num_fuzzy=st.integers(min_value=0, max_value=5),
    num_llm=st.integers(min_value=1, max_value=10)
)
def test_single_llm_batch_call_mixed_headers(num_exact, num_fuzzy, num_llm):
    """
    **Validates: Requirements 3.4, 6.1**
    
    Property 4 (Extended): Single LLM Batch Call with Mixed Headers
    
    For any mix of headers (some matching Tier 1, some Tier 2, some requiring LLM),
    exactly one LLM batch call should be made containing only the headers that
    failed both Tier 1 and Tier 2.
    
    This property ensures that the matcher correctly filters headers through
    tiers and only sends unmapped headers to the LLM.
    """
    # Create mock LLM service
    mock_llm = Mock(spec=LLMService)
    
    # Configure mock to return appropriate number of mappings
    from app.schema.models import HeaderMapping
    mock_mappings = [
        HeaderMapping(
            original_header=f"LLM Header {i}",
            matched_parameter="Power_Output",
            method=MatchMethod.LLM,
            confidence=ConfidenceLevel.MEDIUM
        )
        for i in range(num_llm)
    ]
    mock_llm.batch_match_headers.return_value = mock_mappings
    
    matcher = HeaderMatcher(registry, mock_llm)
    
    # Create mixed headers
    headers = []
    
    # Add exact match headers (will match Tier 1)
    for i in range(num_exact):
        headers.append(registry.parameters[i % len(registry.parameters)])
    
    # Add fuzzy match headers (will match Tier 2)
    for i in range(num_fuzzy):
        headers.append(f"TG-{i+1} Unknown")
    
    # Add LLM headers (won't match Tier 1 or 2)
    for i in range(num_llm):
        headers.append(f"LLM Header {i}")
    
    # Match all headers
    results = matcher.match_headers(headers)
    
    # Verify properties
    total_headers = num_exact + num_fuzzy + num_llm
    assert len(results) == total_headers, \
        f"Should return {total_headers} mappings, got {len(results)}"
    
    # Critical property: LLM should be called exactly ONCE (or not at all if num_llm == 0)
    if num_llm > 0:
        assert mock_llm.batch_match_headers.call_count == 1, \
            f"Expected exactly 1 LLM call, got {mock_llm.batch_match_headers.call_count}"
        
        # Verify that only unmapped headers were sent to LLM
        call_args = mock_llm.batch_match_headers.call_args
        headers_sent = call_args[0][0]
        assert len(headers_sent) == num_llm, \
            f"Expected {num_llm} headers in LLM batch, got {len(headers_sent)}"
    else:
        # If no LLM headers, LLM should not be called
        mock_llm.batch_match_headers.assert_not_called()
    
    # Verify method distribution
    exact_count = sum(1 for r in results if r.method == MatchMethod.EXACT)
    fuzzy_count = sum(1 for r in results if r.method == MatchMethod.FUZZY)
    llm_count = sum(1 for r in results if r.method == MatchMethod.LLM)
    
    assert exact_count == num_exact, \
        f"Expected {num_exact} exact matches, got {exact_count}"
    assert fuzzy_count == num_fuzzy, \
        f"Expected {num_fuzzy} fuzzy matches, got {fuzzy_count}"
    assert llm_count == num_llm, \
        f"Expected {num_llm} LLM matches, got {llm_count}"
