"""
LLM Service for semantic header matching using Gemini 1.5 Flash.

This module provides the LLMService class that handles all interactions
with the Gemini API for Tier 3 semantic matching. It uses Pydantic v2
structured outputs to ensure reliable response parsing and includes
error handling with retry logic.
"""

import google.generativeai as genai
from typing import List, Optional
import logging
import time
from app.schema.models import HeaderMapping, MatchMethod, ConfidenceLevel
from pydantic import TypeAdapter

# Configure logging
logger = logging.getLogger(__name__)


class LLMService:
    """Handles all LLM interactions using Gemini 1.5 Flash"""
    
    def __init__(self, api_key: str, max_retries: int = 3):
        """
        Initialize the LLM service with Gemini API.
        
        Args:
            api_key: Google Gemini API key
            max_retries: Maximum number of retry attempts for API calls
        """
        if not api_key:
            raise ValueError("API key cannot be empty")
        
        genai.configure(api_key=api_key)
        # Use gemini-flash-latest for best performance and compatibility
        self.model = genai.GenerativeModel('gemini-flash-latest')
        self.max_retries = max_retries
        logger.info("LLMService initialized with Gemini Flash")
    
    def batch_match_headers(
        self, 
        headers: List[str], 
        parameters: List[str], 
        assets: List[str]
    ) -> List[HeaderMapping]:
        """
        Batch match multiple headers in ONE LLM call.
        Uses Pydantic v2 structured outputs for reliable parsing.
        
        Args:
            headers: List of unmapped headers to match
            parameters: List of registry parameters
            assets: List of registry asset types
            
        Returns:
            List of HeaderMapping objects with method="llm"
        """
        if not headers:
            logger.warning("batch_match_headers called with empty headers list")
            return []
        
        logger.info(f"Batch matching {len(headers)} headers via LLM")
        
        # Construct prompt
        prompt = self._build_batch_match_prompt(headers, parameters, assets)
        
        # Call LLM with retry logic
        response_text = self._call_llm_with_retry(prompt)
        
        if response_text is None:
            # LLM call failed after retries - return unmapped headers
            logger.error("LLM call failed after all retries, returning unmapped headers")
            return [
                HeaderMapping(
                    original_header=header,
                    matched_parameter=None,
                    matched_asset=None,
                    method=MatchMethod.NONE,
                    confidence=ConfidenceLevel.LOW
                )
                for header in headers
            ]
        
        # Parse response using Pydantic
        try:
            mappings = self._parse_llm_response(response_text, headers)
            logger.info(f"Successfully parsed {len(mappings)} mappings from LLM")
            return mappings
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            # Return unmapped headers on parsing failure
            return [
                HeaderMapping(
                    original_header=header,
                    matched_parameter=None,
                    matched_asset=None,
                    method=MatchMethod.NONE,
                    confidence=ConfidenceLevel.LOW
                )
                for header in headers
            ]

    def simple_query(self, prompt: str) -> str:
        """
        Simple text query for header row detection.
        
        Args:
            prompt: The query prompt
            
        Returns:
            Text response from the LLM
        """
        logger.info("Executing simple LLM query")
        
        response_text = self._call_llm_with_retry(prompt, use_structured_output=False)
        
        if response_text is None:
            logger.error("Simple query failed after all retries")
            return ""
        
        return response_text
    
    def _build_batch_match_prompt(
        self, 
        headers: List[str], 
        parameters: List[str], 
        assets: List[str]
    ) -> str:
        """
        Build the prompt for batch header matching.
        
        Args:
            headers: List of unmapped headers
            parameters: List of registry parameters
            assets: List of registry asset types
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""You are mapping Excel column headers to a standardized registry.

REGISTRY PARAMETERS:
{', '.join(parameters)}

REGISTRY ASSETS:
{', '.join(assets)}

UNMAPPED HEADERS:
{chr(10).join(f"{i+1}. {h}" for i, h in enumerate(headers))}

For each header, determine:
1. The best matching parameter (or null if none)
2. The best matching asset (or null if none)
3. Confidence level: high, medium, or low

Return a JSON array of mappings with the following structure:
[
  {{
    "original_header": "header text",
    "matched_parameter": "parameter name or null",
    "matched_asset": "asset name or null",
    "method": "llm",
    "confidence": "high|medium|low",
    "normalized_header": null
  }}
]

Ensure the array has exactly {len(headers)} mappings in the same order as the input headers."""
        
        return prompt
    
    def _call_llm_with_retry(
        self, 
        prompt: str, 
        use_structured_output: bool = True
    ) -> Optional[str]:
        """
        Call LLM with exponential backoff retry logic.
        
        Args:
            prompt: The prompt to send
            use_structured_output: Whether to use structured JSON output
            
        Returns:
            Response text or None if all retries failed
        """
        for attempt in range(self.max_retries):
            try:
                if use_structured_output:
                    # Use structured output for batch matching
                    response = self.model.generate_content(
                        prompt,
                        generation_config=genai.GenerationConfig(
                            response_mime_type="application/json"
                        )
                    )
                else:
                    # Simple text response
                    response = self.model.generate_content(prompt)
                
                return response.text
                
            except Exception as e:
                logger.warning(f"LLM API call attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries - 1:
                    # Exponential backoff: 1s, 2s, 4s
                    sleep_time = 2 ** attempt
                    logger.info(f"Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
                else:
                    logger.error(f"All {self.max_retries} retry attempts failed")
        
        return None
    
    def _parse_llm_response(
        self, 
        response_text: str, 
        original_headers: List[str]
    ) -> List[HeaderMapping]:
        """
        Parse LLM JSON response into HeaderMapping objects.
        
        Args:
            response_text: JSON response from LLM
            original_headers: Original headers for validation
            
        Returns:
            List of HeaderMapping objects
        """
        # Use Pydantic TypeAdapter for parsing
        adapter = TypeAdapter(List[HeaderMapping])
        mappings = adapter.validate_json(response_text)
        
        # Ensure method is set to LLM and validate
        for i, mapping in enumerate(mappings):
            mapping.method = MatchMethod.LLM
            
            # Set default confidence if not provided
            if mapping.confidence is None:
                mapping.confidence = ConfidenceLevel.MEDIUM
            
            # Validate that we have the right number of mappings
            if i >= len(original_headers):
                logger.warning(f"LLM returned more mappings than headers")
                break
        
        # If LLM returned fewer mappings than headers, fill in the rest
        if len(mappings) < len(original_headers):
            logger.warning(f"LLM returned {len(mappings)} mappings but expected {len(original_headers)}")
            for i in range(len(mappings), len(original_headers)):
                mappings.append(
                    HeaderMapping(
                        original_header=original_headers[i],
                        matched_parameter=None,
                        matched_asset=None,
                        method=MatchMethod.NONE,
                        confidence=ConfidenceLevel.LOW
                    )
                )
        
        return mappings[:len(original_headers)]  # Ensure we don't return more than requested
