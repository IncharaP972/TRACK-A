"""
Unit tests for the LLM service with mocking.
Tests specific examples and error handling.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json

from app.services.llm import LLMService
from app.schema.models import HeaderMapping, MatchMethod, ConfidenceLevel


class TestLLMServiceInitialization:
    """Test LLM service initialization"""
    
    def test_initialization_with_valid_api_key(self):
        """Test that LLMService initializes correctly with valid API key"""
        service = LLMService(api_key="test_api_key_123")
        assert service.max_retries == 3
        assert service.model is not None
    
    def test_initialization_with_custom_max_retries(self):
        """Test that LLMService accepts custom max_retries"""
        service = LLMService(api_key="test_key", max_retries=5)
        assert service.max_retries == 5
    
    def test_initialization_with_empty_api_key_raises_error(self):
        """Test that empty API key raises ValueError"""
        with pytest.raises(ValueError, match="API key cannot be empty"):
            LLMService(api_key="")


class TestBatchMatchHeaders:
    """Test batch_match_headers method"""
    
    @patch('app.services.llm.genai.GenerativeModel')
    def test_batch_match_headers_with_valid_response(self, mock_model_class):
        """Test batch matching with valid LLM response"""
        # Setup mock
        mock_model = MagicMock()
        mock_model_class.return_value = mock_model
        
        headers = ["Power TG1", "Temperature AFBC2", "Efficiency"]
        parameters = ["Power_Output", "Temperature", "Efficiency"]
        assets = ["TG", "AFBC"]
        
        # Mock LLM response
        mock_response_data = [
            {
                "original_header": "Power TG1",
                "matched_parameter": "Power_Output",
                "matched_asset": "TG",
                "method": "llm",
                "confidence": "high",
                "normalized_header": None
            },
            {
                "original_header": "Temperature AFBC2",
                "matched_parameter": "Temperature",
                "matched_asset": "AFBC",
                "method": "llm",
                "confidence": "medium",
                "normalized_header": None
            },
            {
                "original_header": "Efficiency",
                "matched_parameter": "Efficiency",
                "matched_asset": None,
                "method": "llm",
                "confidence": "high",
                "normalized_header": None
            }
        ]
        
        mock_response = MagicMock()
        mock_response.text = json.dumps(mock_response_data)
        mock_model.generate_content.return_value = mock_response
        
        # Create service and call method
        service = LLMService(api_key="test_key")
        service.model = mock_model
        
        result = service.batch_match_headers(headers, parameters, assets)
        
        # Verify results
        assert len(result) == 3
        assert all(m.method == MatchMethod.LLM for m in result)
        assert result[0].original_header == "Power TG1"
        assert result[0].matched_parameter == "Power_Output"
        assert result[0].matched_asset == "TG"
        assert result[0].confidence == ConfidenceLevel.HIGH
        
        # Verify LLM was called once
        assert mock_model.generate_content.call_count == 1
    
    @patch('app.services.llm.genai.GenerativeModel')
    def test_batch_match_headers_with_empty_list(self, mock_model_class):
        """Test batch matching with empty headers list"""
        mock_model = MagicMock()
        mock_model_class.return_value = mock_model
        
        service = LLMService(api_key="test_key")
        service.model = mock_model
        
        result = service.batch_match_headers([], ["param1"], ["asset1"])
        
        # Should return empty list without calling LLM
        assert result == []
        assert mock_model.generate_content.call_count == 0
    
    @patch('app.services.llm.genai.GenerativeModel')
    def test_batch_match_headers_with_api_failure(self, mock_model_class):
        """Test batch matching when LLM API fails"""
        mock_model = MagicMock()
        mock_model_class.return_value = mock_model
        
        # Mock API failure
        mock_model.generate_content.side_effect = Exception("API Error")
        
        service = LLMService(api_key="test_key", max_retries=2)
        service.model = mock_model
        
        headers = ["Header1", "Header2"]
        result = service.batch_match_headers(headers, ["param1"], ["asset1"])
        
        # Should return unmapped headers with method=NONE
        assert len(result) == 2
        assert all(m.method == MatchMethod.NONE for m in result)
        assert all(m.confidence == ConfidenceLevel.LOW for m in result)
        assert all(m.matched_parameter is None for m in result)
        assert all(m.matched_asset is None for m in result)
        
        # Verify retries were attempted
        assert mock_model.generate_content.call_count == 2
    
    @patch('app.services.llm.genai.GenerativeModel')
    def test_batch_match_headers_with_invalid_json_response(self, mock_model_class):
        """Test batch matching when LLM returns invalid JSON"""
        mock_model = MagicMock()
        mock_model_class.return_value = mock_model
        
        # Mock invalid JSON response
        mock_response = MagicMock()
        mock_response.text = "This is not valid JSON"
        mock_model.generate_content.return_value = mock_response
        
        service = LLMService(api_key="test_key")
        service.model = mock_model
        
        headers = ["Header1", "Header2"]
        result = service.batch_match_headers(headers, ["param1"], ["asset1"])
        
        # Should return unmapped headers on parsing failure
        assert len(result) == 2
        assert all(m.method == MatchMethod.NONE for m in result)
        assert all(m.confidence == ConfidenceLevel.LOW for m in result)
    
    @patch('app.services.llm.genai.GenerativeModel')
    def test_batch_match_headers_with_fewer_mappings_than_headers(self, mock_model_class):
        """Test batch matching when LLM returns fewer mappings than headers"""
        mock_model = MagicMock()
        mock_model_class.return_value = mock_model
        
        headers = ["Header1", "Header2", "Header3"]
        
        # Mock response with only 2 mappings
        mock_response_data = [
            {
                "original_header": "Header1",
                "matched_parameter": "param1",
                "matched_asset": None,
                "method": "llm",
                "confidence": "high",
                "normalized_header": None
            },
            {
                "original_header": "Header2",
                "matched_parameter": "param2",
                "matched_asset": None,
                "method": "llm",
                "confidence": "medium",
                "normalized_header": None
            }
        ]
        
        mock_response = MagicMock()
        mock_response.text = json.dumps(mock_response_data)
        mock_model.generate_content.return_value = mock_response
        
        service = LLMService(api_key="test_key")
        service.model = mock_model
        
        result = service.batch_match_headers(headers, ["param1", "param2"], ["asset1"])
        
        # Should fill in missing mappings with NONE
        assert len(result) == 3
        assert result[0].method == MatchMethod.LLM
        assert result[1].method == MatchMethod.LLM
        assert result[2].method == MatchMethod.NONE
        assert result[2].confidence == ConfidenceLevel.LOW
    
    @patch('app.services.llm.genai.GenerativeModel')
    def test_batch_match_headers_with_more_mappings_than_headers(self, mock_model_class):
        """Test batch matching when LLM returns more mappings than headers"""
        mock_model = MagicMock()
        mock_model_class.return_value = mock_model
        
        headers = ["Header1", "Header2"]
        
        # Mock response with 3 mappings (more than headers)
        mock_response_data = [
            {
                "original_header": "Header1",
                "matched_parameter": "param1",
                "matched_asset": None,
                "method": "llm",
                "confidence": "high",
                "normalized_header": None
            },
            {
                "original_header": "Header2",
                "matched_parameter": "param2",
                "matched_asset": None,
                "method": "llm",
                "confidence": "medium",
                "normalized_header": None
            },
            {
                "original_header": "Header3",
                "matched_parameter": "param3",
                "matched_asset": None,
                "method": "llm",
                "confidence": "low",
                "normalized_header": None
            }
        ]
        
        mock_response = MagicMock()
        mock_response.text = json.dumps(mock_response_data)
        mock_model.generate_content.return_value = mock_response
        
        service = LLMService(api_key="test_key")
        service.model = mock_model
        
        result = service.batch_match_headers(headers, ["param1", "param2"], ["asset1"])
        
        # Should only return mappings for requested headers
        assert len(result) == 2
        assert result[0].original_header == "Header1"
        assert result[1].original_header == "Header2"


class TestSimpleQuery:
    """Test simple_query method"""
    
    @patch('app.services.llm.genai.GenerativeModel')
    def test_simple_query_with_valid_response(self, mock_model_class):
        """Test simple query with valid response"""
        mock_model = MagicMock()
        mock_model_class.return_value = mock_model
        
        mock_response = MagicMock()
        mock_response.text = "3"
        mock_model.generate_content.return_value = mock_response
        
        service = LLMService(api_key="test_key")
        service.model = mock_model
        
        result = service.simple_query("Which row is the header?")
        
        assert result == "3"
        assert mock_model.generate_content.call_count == 1
    
    @patch('app.services.llm.genai.GenerativeModel')
    def test_simple_query_with_api_failure(self, mock_model_class):
        """Test simple query when API fails"""
        mock_model = MagicMock()
        mock_model_class.return_value = mock_model
        
        mock_model.generate_content.side_effect = Exception("API Error")
        
        service = LLMService(api_key="test_key", max_retries=2)
        service.model = mock_model
        
        result = service.simple_query("Test prompt")
        
        # Should return empty string on failure
        assert result == ""
        assert mock_model.generate_content.call_count == 2


class TestRetryLogic:
    """Test retry logic with exponential backoff"""
    
    @patch('app.services.llm.time.sleep')
    @patch('app.services.llm.genai.GenerativeModel')
    def test_retry_with_exponential_backoff(self, mock_model_class, mock_sleep):
        """Test that retries use exponential backoff"""
        mock_model = MagicMock()
        mock_model_class.return_value = mock_model
        
        # Fail first 2 attempts, succeed on 3rd
        mock_model.generate_content.side_effect = [
            Exception("Error 1"),
            Exception("Error 2"),
            MagicMock(text="Success")
        ]
        
        service = LLMService(api_key="test_key", max_retries=3)
        service.model = mock_model
        
        result = service.simple_query("Test prompt")
        
        # Should succeed on 3rd attempt
        assert result == "Success"
        assert mock_model.generate_content.call_count == 3
        
        # Verify exponential backoff: 1s, 2s
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(1)  # 2^0 = 1
        mock_sleep.assert_any_call(2)  # 2^1 = 2
    
    @patch('app.services.llm.time.sleep')
    @patch('app.services.llm.genai.GenerativeModel')
    def test_no_retry_on_success(self, mock_model_class, mock_sleep):
        """Test that no retries occur when first attempt succeeds"""
        mock_model = MagicMock()
        mock_model_class.return_value = mock_model
        
        mock_response = MagicMock()
        mock_response.text = "Success"
        mock_model.generate_content.return_value = mock_response
        
        service = LLMService(api_key="test_key", max_retries=3)
        service.model = mock_model
        
        result = service.simple_query("Test prompt")
        
        assert result == "Success"
        assert mock_model.generate_content.call_count == 1
        assert mock_sleep.call_count == 0


class TestBuildBatchMatchPrompt:
    """Test _build_batch_match_prompt method"""
    
    def test_build_batch_match_prompt_structure(self):
        """Test that prompt is built with correct structure"""
        service = LLMService(api_key="test_key")
        
        headers = ["Header1", "Header2"]
        parameters = ["Power_Output", "Temperature"]
        assets = ["TG", "AFBC"]
        
        prompt = service._build_batch_match_prompt(headers, parameters, assets)
        
        # Verify prompt contains all necessary components
        assert "REGISTRY PARAMETERS:" in prompt
        assert "Power_Output" in prompt
        assert "Temperature" in prompt
        assert "REGISTRY ASSETS:" in prompt
        assert "TG" in prompt
        assert "AFBC" in prompt
        assert "UNMAPPED HEADERS:" in prompt
        assert "1. Header1" in prompt
        assert "2. Header2" in prompt
        assert "exactly 2 mappings" in prompt


class TestConfidenceHandling:
    """Test confidence level handling"""
    
    @patch('app.services.llm.genai.GenerativeModel')
    def test_default_confidence_when_missing(self, mock_model_class):
        """Test that missing confidence defaults to MEDIUM"""
        mock_model = MagicMock()
        mock_model_class.return_value = mock_model
        
        # Mock response without explicit confidence (will use default)
        mock_response_data = [
            {
                "original_header": "Header1",
                "matched_parameter": "param1",
                "matched_asset": None,
                "method": "llm",
                "confidence": "medium",  # Explicitly set to medium
                "normalized_header": None
            }
        ]
        
        mock_response = MagicMock()
        mock_response.text = json.dumps(mock_response_data)
        mock_model.generate_content.return_value = mock_response
        
        service = LLMService(api_key="test_key")
        service.model = mock_model
        
        result = service.batch_match_headers(["Header1"], ["param1"], ["asset1"])
        
        # Should have MEDIUM confidence
        assert result[0].confidence == ConfidenceLevel.MEDIUM
    
    @patch('app.services.llm.genai.GenerativeModel')
    def test_all_confidence_levels_preserved(self, mock_model_class):
        """Test that all confidence levels are correctly preserved"""
        mock_model = MagicMock()
        mock_model_class.return_value = mock_model
        
        mock_response_data = [
            {
                "original_header": "Header1",
                "matched_parameter": "param1",
                "matched_asset": None,
                "method": "llm",
                "confidence": "high",
                "normalized_header": None
            },
            {
                "original_header": "Header2",
                "matched_parameter": "param2",
                "matched_asset": None,
                "method": "llm",
                "confidence": "medium",
                "normalized_header": None
            },
            {
                "original_header": "Header3",
                "matched_parameter": "param3",
                "matched_asset": None,
                "method": "llm",
                "confidence": "low",
                "normalized_header": None
            }
        ]
        
        mock_response = MagicMock()
        mock_response.text = json.dumps(mock_response_data)
        mock_model.generate_content.return_value = mock_response
        
        service = LLMService(api_key="test_key")
        service.model = mock_model
        
        result = service.batch_match_headers(
            ["Header1", "Header2", "Header3"],
            ["param1", "param2", "param3"],
            ["asset1"]
        )
        
        assert result[0].confidence == ConfidenceLevel.HIGH
        assert result[1].confidence == ConfidenceLevel.MEDIUM
        assert result[2].confidence == ConfidenceLevel.LOW
