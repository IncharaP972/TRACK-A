"""
Registry Manager for standardized parameters and asset identifiers.

This module provides the RegistryManager class which maintains:
- A complete list of standardized parameter names
- Asset identifier patterns for regex-based extraction
- O(1) lookup for exact matching operations
- Compiled regex patterns for efficient asset extraction

Requirements: 2.1, 2.2, 2.3, 2.5, 15.3
"""

from typing import Dict, List, Optional, Tuple
import re


class RegistryManager:
    """
    Manages standardized parameters and assets with efficient lookup.
    
    Provides three main operations:
    1. exact_match(): O(1) hash-based lookup for normalized parameter names
    2. extract_asset(): Regex-based asset identifier extraction
    3. _normalize(): String normalization for consistent matching
    """
    
    def __init__(self):
        # Standardized parameters for power plant operational data
        self.parameters: List[str] = [
            "Power_Output",
            "Temperature",
            "Efficiency",
            "Fuel_Consumption",
            "Emissions_CO2",
            "Emissions_NOx",
            "Emissions_SOx",
            "Steam_Pressure",
            "Steam_Temperature",
            "Boiler_Efficiency",
            "Heat_Rate",
            "Load_Factor",
            "Availability",
            "Forced_Outage_Rate",
            "Planned_Outage_Rate",
            "Auxiliary_Power",
            "Net_Generation",
            "Gross_Generation",
            "Capacity_Factor",
            "Thermal_Efficiency",
        ]
        
        # Asset identifiers with regex patterns
        # Patterns match variations like "AFBC-1", "AFBC_1", "AFBC1"
        self.assets: Dict[str, str] = {
            "AFBC": r"AFBC[-_]?\d+",
            "TG": r"TG[-_]?\d+",
            "ESP": r"ESP[-_]?\d+",
            "APH": r"APH[-_]?\d+",
            "FD_FAN": r"FD[-_]?FAN[-_]?\d+",
            "ID_FAN": r"ID[-_]?FAN[-_]?\d+",
            "PA_FAN": r"PA[-_]?FAN[-_]?\d+",
            "BOILER": r"BOILER[-_]?\d+",
            "TURBINE": r"TURBINE[-_]?\d+",
            "GENERATOR": r"GENERATOR[-_]?\d+",
            "CONDENSER": r"CONDENSER[-_]?\d+",
            "ECONOMIZER": r"ECONOMIZER[-_]?\d+",
        }
        
        # Normalized lookup for O(1) exact matching
        # Maps normalized strings to original parameter names
        self.normalized_params: Dict[str, str] = {
            self._normalize(p): p for p in self.parameters
        }
        
        # Compiled regex patterns for Tier 2 matching
        # Pre-compilation improves performance for repeated matching
        self.asset_patterns: Dict[str, re.Pattern] = {
            name: re.compile(pattern, re.IGNORECASE)
            for name, pattern in self.assets.items()
        }
    
    def _normalize(self, text: str) -> str:
        """
        Normalize text for exact matching.
        
        Removes all non-alphanumeric characters and converts to lowercase.
        This ensures that variations in case, whitespace, and special characters
        don't prevent matching.
        
        Examples:
            "Power_Output" -> "poweroutput"
            "Power Output" -> "poweroutput"
            "POWER-OUTPUT" -> "poweroutput"
            "  Power  Output  " -> "poweroutput"
        
        Args:
            text: Input string to normalize
            
        Returns:
            Normalized string with only lowercase alphanumeric characters
        """
        return re.sub(r'[^a-z0-9]', '', text.lower())
    
    def exact_match(self, header: str) -> Optional[str]:
        """
        Perform O(1) exact match lookup for a header.
        
        Normalizes the input header and looks it up in the pre-computed
        normalized_params dictionary. This provides constant-time lookup
        regardless of the registry size.
        
        Args:
            header: Excel column header to match
            
        Returns:
            Matched parameter name from registry, or None if no match found
            
        Examples:
            exact_match("Power_Output") -> "Power_Output"
            exact_match("power output") -> "Power_Output"
            exact_match("POWER-OUTPUT") -> "Power_Output"
            exact_match("Unknown Header") -> None
        """
        normalized = self._normalize(header)
        return self.normalized_params.get(normalized)
    
    def extract_asset(self, header: str) -> Optional[Tuple[str, str]]:
        """
        Extract asset identifier using compiled regex patterns.
        
        Searches the header string for any known asset patterns.
        Returns the first match found, along with the asset type.
        
        Args:
            header: Excel column header potentially containing an asset identifier
            
        Returns:
            Tuple of (asset_type, asset_identifier) if found, None otherwise
            
        Examples:
            extract_asset("Power TG1") -> ("TG", "TG1")
            extract_asset("AFBC-2 Temperature") -> ("AFBC", "AFBC-2")
            extract_asset("TG_3 Efficiency") -> ("TG", "TG_3")
            extract_asset("ESP-1") -> ("ESP", "ESP-1")
            extract_asset("Temperature") -> None
        """
        for asset_type, pattern in self.asset_patterns.items():
            match = pattern.search(header)
            if match:
                return (asset_type, match.group(0))
        return None
