"""
Three-tier header matching strategy for Excel column headers.

This module implements the HeaderMatcher class which orchestrates
a three-tier matching strategy:
1. Tier 1: Fast O(1) exact matching with normalization
2. Tier 2: Regex-based asset extraction with parameter inference
3. Tier 3: Batch LLM semantic matching (single call per file)

The matcher ensures efficiency by processing tiers sequentially
and batching all LLM calls into a single API request per file.

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4, 4.5,
              5.1, 5.2, 5.3, 5.4, 5.5, 15.4
"""

from typing import List, Optional, Tuple
from app.schema.models import HeaderMapping, MatchMethod, ConfidenceLevel
from app.registry.data import RegistryManager
from app.services.llm import LLMService
import logging

# Configure logging
logger = logging.getLogger(__name__)


class HeaderMatcher:
    """
    Implements three-tier header matching strategy.
    
    The matcher processes headers through three sequential tiers:
    - Tier 1: Normalized exact matching (O(1) lookup)
    - Tier 2: Regex-based asset extraction
    - Tier 3: Batch LLM semantic matching (one call per file)
    
    Each tier only processes headers that failed in previous tiers,
    ensuring efficiency and minimizing LLM API calls.
    """
    
    def __init__(self, registry: RegistryManager, llm_service: LLMService):
        """
        Initialize the HeaderMatcher with registry and LLM service.
        
        Args:
            registry: RegistryManager instance for parameter/asset lookup
            llm_service: LLMService instance for semantic matching
        """
        self.registry = registry
        self.llm_service = llm_service
        logger.info("HeaderMatcher initialized")
    
    def match_headers(self, headers: List[str]) -> List[HeaderMapping]:
        """
        Match all headers using three-tier strategy.
        
        This is the main entry point for header matching. It processes
        all headers through the three tiers sequentially, ensuring that
        each header is matched by the most appropriate method.
        
        Args:
            headers: List of Excel column headers to match
            
        Returns:
            List of HeaderMapping objects with audit trail, one per header
            in the same order as input
        """
        if not headers:
            logger.warning("match_headers called with empty headers list")
            return []
        
        logger.info(f"Matching {len(headers)} headers using three-tier strategy")
        
        try:
            # Initialize results list with None placeholders
            mappings: List[Optional[HeaderMapping]] = [None] * len(headers)
            unmapped_indices: List[int] = []
            
            # Tier 1: Exact matching
            logger.debug("Starting Tier 1: Exact matching")
            for idx, header in enumerate(headers):
                try:
                    tier1_result = self._tier1_exact_match(header)
                    if tier1_result:
                        mappings[idx] = tier1_result
                        logger.debug(f"Tier 1 matched: '{header}' -> {tier1_result.matched_parameter}")
                    else:
                        # Queue for Tier 2
                        unmapped_indices.append(idx)
                except Exception as e:
                    logger.error(f"Error in Tier 1 matching for header '{header}': {e}")
                    unmapped_indices.append(idx)
            
            logger.info(f"Tier 1 complete: {len(headers) - len(unmapped_indices)} exact matches, "
                       f"{len(unmapped_indices)} unmapped")
            
            # Tier 2: Regex asset extraction
            if unmapped_indices:
                logger.debug("Starting Tier 2: Regex asset extraction")
                still_unmapped: List[int] = []
                
                for idx in unmapped_indices:
                    header = headers[idx]
                    try:
                        tier2_result = self._tier2_regex_match(header)
                        if tier2_result:
                            mappings[idx] = tier2_result
                            logger.debug(f"Tier 2 matched: '{header}' -> "
                                       f"{tier2_result.matched_asset}/{tier2_result.matched_parameter}")
                        else:
                            still_unmapped.append(idx)
                    except Exception as e:
                        logger.error(f"Error in Tier 2 matching for header '{header}': {e}")
                        still_unmapped.append(idx)
                
                logger.info(f"Tier 2 complete: {len(unmapped_indices) - len(still_unmapped)} "
                           f"regex matches, {len(still_unmapped)} still unmapped")
                unmapped_indices = still_unmapped
            
            # Tier 3: Batch LLM semantic matching
            if unmapped_indices:
                logger.debug("Starting Tier 3: Batch LLM semantic matching")
                unmapped_headers = [headers[idx] for idx in unmapped_indices]
                
                try:
                    tier3_results = self._tier3_llm_match(unmapped_headers)
                    
                    for idx, mapping in zip(unmapped_indices, tier3_results):
                        mappings[idx] = mapping
                        logger.debug(f"Tier 3 processed: '{headers[idx]}' -> "
                                   f"method={mapping.method}, confidence={mapping.confidence}")
                    
                    logger.info(f"Tier 3 complete: processed {len(unmapped_headers)} headers via LLM")
                except Exception as e:
                    logger.error(f"Error in Tier 3 LLM matching: {e}")
                    # Create unmapped headers for all failed LLM matches
                    for idx in unmapped_indices:
                        if mappings[idx] is None:
                            mappings[idx] = HeaderMapping(
                                original_header=headers[idx],
                                matched_parameter=None,
                                matched_asset=None,
                                method=MatchMethod.NONE,
                                confidence=ConfidenceLevel.LOW
                            )
            
            # Ensure all mappings are filled (should never be None at this point)
            final_mappings = []
            for idx, mapping in enumerate(mappings):
                if mapping is None:
                    # Fallback: create unmapped header (should not happen)
                    logger.warning(f"Header at index {idx} was not mapped by any tier")
                    final_mappings.append(
                        HeaderMapping(
                            original_header=headers[idx],
                            matched_parameter=None,
                            matched_asset=None,
                            method=MatchMethod.NONE,
                            confidence=ConfidenceLevel.LOW
                        )
                    )
                else:
                    final_mappings.append(mapping)
            
            logger.info(f"Header matching complete: {len(final_mappings)} total mappings")
            return final_mappings
            
        except Exception as e:
            logger.error(f"Critical error in match_headers: {e}", exc_info=True)
            # Return unmapped headers for all inputs as fallback
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
    
    def _tier1_exact_match(self, header: str) -> Optional[HeaderMapping]:
        """
        Tier 1: Normalized exact matching with O(1) lookup.
        
        Uses the registry's exact_match method which normalizes the header
        and performs a hash-based lookup. This is the fastest matching method
        and should handle most well-formatted headers.
        
        Args:
            header: Excel column header to match
            
        Returns:
            HeaderMapping with method="exact" and confidence="high" if matched,
            None otherwise
        """
        matched_param = self.registry.exact_match(header)
        if matched_param:
            return HeaderMapping(
                original_header=header,
                matched_parameter=matched_param,
                method=MatchMethod.EXACT,
                confidence=ConfidenceLevel.HIGH,
                normalized_header=self.registry._normalize(header)
            )
        return None
    
    def _tier2_regex_match(self, header: str) -> Optional[HeaderMapping]:
        """
        Tier 2: Regex-based asset extraction.
        
        Attempts to extract asset identifiers (e.g., "TG-1", "AFBC-2") from
        the header using regex patterns. If an asset is found, tries to infer
        the parameter from the remaining text.
        
        Args:
            header: Excel column header to match
            
        Returns:
            HeaderMapping with method="fuzzy" if asset extracted, None otherwise
        """
        asset_match = self.registry.extract_asset(header)
        if asset_match:
            asset_type, asset_id = asset_match
            
            # Try to infer parameter from remaining text
            param = self._infer_parameter_from_context(header, asset_id)
            
            # Determine confidence based on whether parameter was inferred
            confidence = ConfidenceLevel.MEDIUM if param else ConfidenceLevel.LOW
            
            return HeaderMapping(
                original_header=header,
                matched_parameter=param,
                matched_asset=asset_id,
                method=MatchMethod.FUZZY,
                confidence=confidence
            )
        return None
    
    def _infer_parameter_from_context(self, header: str, asset_id: str) -> Optional[str]:
        """
        Attempt to infer parameter from header text after removing asset.
        
        Removes the asset identifier from the header and tries to match
        the remaining text against known parameters using exact matching.
        
        Args:
            header: Original header string
            asset_id: Asset identifier to remove (e.g., "TG-1")
            
        Returns:
            Matched parameter name if found, None otherwise
            
        Examples:
            _infer_parameter_from_context("Power TG-1", "TG-1") -> "Power_Output"
            _infer_parameter_from_context("TG-1 Temperature", "TG-1") -> "Temperature"
            _infer_parameter_from_context("TG-1", "TG-1") -> None
        """
        # Remove asset identifier from header
        remaining = header.replace(asset_id, "").strip()
        
        if not remaining:
            return None
        
        # Try exact match on remaining text
        return self.registry.exact_match(remaining)
    
    def _tier3_llm_match(self, headers: List[str]) -> List[HeaderMapping]:
        """
        Tier 3: Batch LLM semantic matching (ONE call per file).
        
        Sends all unmapped headers to the LLM service in a single batch call.
        This ensures we make exactly one LLM API call per file, regardless
        of how many headers need semantic matching.
        
        Args:
            headers: List of headers that failed Tier 1 and Tier 2
            
        Returns:
            List of HeaderMapping objects with method="llm" or method="none"
        """
        if not headers:
            return []
        
        # Single batch call to LLM service
        return self.llm_service.batch_match_headers(
            headers,
            self.registry.parameters,
            list(self.registry.assets.keys())
        )
