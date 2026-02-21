"""
Unit tests for HeaderMatcher three-tier matching strategy.

This module contains unit tests that verify specific examples and edge cases
for the header matching system.

Requirements: 4.1, 5.1, 6.1
"""

import pytest
from unittest.mock import Mock, MagicMock
from app.core.matcher import HeaderMatcher
from app.registry.data import RegistryManager
from app.services.llm import LLMService
from app.schema.models import HeaderMapping, MatchMethod, ConfidenceLevel


@pytest.fixture
def registry():
    """Fixture providing a RegistryManager instance."""
    return RegistryManager()


@pytest.fixture
def mock_llm():
    """Fixture providing a mocked LLMService."""
    return Mock(spec=LLMService)


@pytest.fixture
def matcher(registry, mock_llm):
    """Fixture providing a HeaderMatcher instance."""
    return HeaderMatcher(registry, mock_llm)


class TestTier1ExactMatching:
    """Test cases for Tier 1 exact matching."""
    
    def test_exact_match_standard_parameter(self, matcher):
        """Test exact match with a standard parameter name."""
        result = matcher._tier1_exact_match("Power_Output")
        
        assert result is not None
        assert result.matched_parameter == "Power_Output"
        assert result.method == MatchMethod.EXACT
        assert result.confidence == ConfidenceLevel.HIGH
        assert result.original_header == "Power_Output"
    
    def test_exact_match_case_insensitive(self, matcher):
        """Test exact match is case insensitive."""
        result = matcher._tier1_exact_match("power_output")
        
        assert result is not None
        assert result.matched_parameter == "Power_Output"
        assert result.method == MatchMethod.EXACT
        assert result.confidence == ConfidenceLevel.HIGH
    
    def test_exact_match_with_spaces(self, matcher):
        """Test exact match handles spaces."""
        result = matcher._tier1_exact_match("Power Output")
        
        assert result is not None
        assert result.matched_parameter == "Power_Output"
        assert result.method == MatchMethod.EXACT
    
    def test_exact_match_with_special_chars(self, matcher):
        """Test exact match handles special characters."""
        result = matcher._tier1_exact_match("Power-Output")
        
        assert result is not None
        assert result.matched_parameter == "Power_Output"
        assert result.method == MatchMethod.EXACT
    
    def test_exact_match_no_match(self, matcher):
        """Test exact match returns None for unknown header."""
        result = matcher._tier1_exact_match("Unknown Header")
        
        assert result is None
    
    def test_exact_match_multiple_parameters(self, matcher):
        """Test exact match with multiple different parameters."""
        test_cases = [
            ("Temperature", "Temperature"),
            ("Efficiency", "Efficiency"),
            ("Fuel_Consumption", "Fuel_Consumption"),
            ("Steam_Pressure", "Steam_Pressure"),
        ]
        
        for header, expected_param in test_cases:
            result = matcher._tier1_exact_match(header)
            assert result is not None
            assert result.matched_parameter == expected_param


class TestTier2RegexMatching:
    """Test cases for Tier 2 regex-based asset extraction."""
    
    def test_regex_match_tg_asset(self, matcher):
        """Test regex match extracts TG asset identifier."""
        result = matcher._tier2_regex_match("Power TG-1")
        
        assert result is not None
        assert result.matched_asset == "TG-1"
        assert result.method == MatchMethod.FUZZY
        assert result.confidence in [ConfidenceLevel.MEDIUM, ConfidenceLevel.LOW]
    
    def test_regex_match_afbc_asset(self, matcher):
        """Test regex match extracts AFBC asset identifier."""
        result = matcher._tier2_regex_match("AFBC-2 Temperature")
        
        assert result is not None
        assert result.matched_asset == "AFBC-2"
        assert result.method == MatchMethod.FUZZY
    
    def test_regex_match_esp_asset(self, matcher):
        """Test regex match extracts ESP asset identifier."""
        result = matcher._tier2_regex_match("ESP-3 Efficiency")
        
        assert result is not None
        assert result.matched_asset == "ESP-3"
        assert result.method == MatchMethod.FUZZY
    
    def test_regex_match_with_parameter_inference(self, matcher):
        """Test regex match infers parameter from context."""
        result = matcher._tier2_regex_match("TG-1 Power_Output")
        
        assert result is not None
        assert result.matched_asset == "TG-1"
        assert result.matched_parameter == "Power_Output"
        assert result.confidence == ConfidenceLevel.MEDIUM
    
    def test_regex_match_without_parameter(self, matcher):
        """Test regex match without inferrable parameter."""
        result = matcher._tier2_regex_match("TG-1 Unknown")
        
        assert result is not None
        assert result.matched_asset == "TG-1"
        assert result.matched_parameter is None
        assert result.confidence == ConfidenceLevel.LOW
    
    def test_regex_match_no_asset(self, matcher):
        """Test regex match returns None when no asset found."""
        result = matcher._tier2_regex_match("Unknown Header")
        
        assert result is None
    
    def test_regex_match_various_formats(self, matcher):
        """Test regex match handles various asset identifier formats."""
        test_cases = [
            ("TG1", "TG1"),
            ("TG-1", "TG-1"),
            ("TG_1", "TG_1"),
            ("AFBC2", "AFBC2"),
            ("AFBC-2", "AFBC-2"),
        ]
        
        for header, expected_asset in test_cases:
            result = matcher._tier2_regex_match(header)
            assert result is not None
            assert result.matched_asset == expected_asset


class TestTier3LLMMatching:
    """Test cases for Tier 3 LLM semantic matching."""
    
    def test_llm_match_single_header(self, matcher, mock_llm):
        """Test LLM match with a single header."""
        mock_llm.batch_match_headers.return_value = [
            HeaderMapping(
                original_header="Unusual Header",
                matched_parameter="Power_Output",
                method=MatchMethod.LLM,
                confidence=ConfidenceLevel.MEDIUM
            )
        ]
        
        results = matcher._tier3_llm_match(["Unusual Header"])
        
        assert len(results) == 1
        assert results[0].method == MatchMethod.LLM
        mock_llm.batch_match_headers.assert_called_once()
    
    def test_llm_match_multiple_headers(self, matcher, mock_llm):
        """Test LLM match with multiple headers."""
        headers = ["Header 1", "Header 2", "Header 3"]
        mock_llm.batch_match_headers.return_value = [
            HeaderMapping(
                original_header=h,
                matched_parameter="Power_Output",
                method=MatchMethod.LLM,
                confidence=ConfidenceLevel.MEDIUM
            )
            for h in headers
        ]
        
        results = matcher._tier3_llm_match(headers)
        
        assert len(results) == 3
        mock_llm.batch_match_headers.assert_called_once()
    
    def test_llm_match_empty_list(self, matcher, mock_llm):
        """Test LLM match with empty header list."""
        results = matcher._tier3_llm_match([])
        
        assert len(results) == 0
        mock_llm.batch_match_headers.assert_not_called()


class TestInferParameterFromContext:
    """Test cases for parameter inference helper."""
    
    def test_infer_parameter_with_match(self, matcher):
        """Test parameter inference when remaining text matches."""
        result = matcher._infer_parameter_from_context("TG-1 Power_Output", "TG-1")
        
        assert result == "Power_Output"
    
    def test_infer_parameter_no_match(self, matcher):
        """Test parameter inference when remaining text doesn't match."""
        result = matcher._infer_parameter_from_context("TG-1 Unknown", "TG-1")
        
        assert result is None
    
    def test_infer_parameter_empty_remaining(self, matcher):
        """Test parameter inference when no text remains."""
        result = matcher._infer_parameter_from_context("TG-1", "TG-1")
        
        assert result is None
    
    def test_infer_parameter_case_insensitive(self, matcher):
        """Test parameter inference is case insensitive."""
        result = matcher._infer_parameter_from_context("TG-1 temperature", "TG-1")
        
        assert result == "Temperature"


class TestMatchHeadersIntegration:
    """Integration tests for the complete match_headers workflow."""
    
    def test_match_headers_all_exact(self, matcher, mock_llm):
        """Test matching when all headers match Tier 1."""
        headers = ["Power_Output", "Temperature", "Efficiency"]
        
        results = matcher.match_headers(headers)
        
        assert len(results) == 3
        assert all(r.method == MatchMethod.EXACT for r in results)
        mock_llm.batch_match_headers.assert_not_called()
    
    def test_match_headers_all_fuzzy(self, matcher, mock_llm):
        """Test matching when all headers match Tier 2."""
        headers = ["TG-1 Unknown", "AFBC-2 Unknown", "ESP-3 Unknown"]
        
        results = matcher.match_headers(headers)
        
        assert len(results) == 3
        assert all(r.method == MatchMethod.FUZZY for r in results)
        mock_llm.batch_match_headers.assert_not_called()
    
    def test_match_headers_all_llm(self, matcher, mock_llm):
        """Test matching when all headers require LLM."""
        headers = ["Unknown 1", "Unknown 2", "Unknown 3"]
        mock_llm.batch_match_headers.return_value = [
            HeaderMapping(
                original_header=h,
                matched_parameter=None,
                method=MatchMethod.LLM,
                confidence=ConfidenceLevel.LOW
            )
            for h in headers
        ]
        
        results = matcher.match_headers(headers)
        
        assert len(results) == 3
        assert all(r.method == MatchMethod.LLM for r in results)
        mock_llm.batch_match_headers.assert_called_once()
    
    def test_match_headers_mixed(self, matcher, mock_llm):
        """Test matching with mixed header types."""
        headers = ["Power_Output", "TG-1 Unknown", "Unknown Header"]
        mock_llm.batch_match_headers.return_value = [
            HeaderMapping(
                original_header="Unknown Header",
                matched_parameter=None,
                method=MatchMethod.LLM,
                confidence=ConfidenceLevel.LOW
            )
        ]
        
        results = matcher.match_headers(headers)
        
        assert len(results) == 3
        assert results[0].method == MatchMethod.EXACT
        assert results[1].method == MatchMethod.FUZZY
        assert results[2].method == MatchMethod.LLM
        mock_llm.batch_match_headers.assert_called_once()
    
    def test_match_headers_empty_list(self, matcher, mock_llm):
        """Test matching with empty header list."""
        results = matcher.match_headers([])
        
        assert len(results) == 0
        mock_llm.batch_match_headers.assert_not_called()
    
    def test_match_headers_preserves_order(self, matcher, mock_llm):
        """Test that match_headers preserves input order."""
        headers = ["Temperature", "TG-1 Unknown", "Power_Output"]
        mock_llm.batch_match_headers.return_value = []
        
        results = matcher.match_headers(headers)
        
        assert len(results) == 3
        assert results[0].original_header == "Temperature"
        assert results[1].original_header == "TG-1 Unknown"
        assert results[2].original_header == "Power_Output"
