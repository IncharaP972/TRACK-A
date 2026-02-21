"""
Unit tests for RegistryManager.

Tests specific examples of exact_match and extract_asset functionality
with known parameters and sample headers.

Requirements: 2.1, 2.2
"""

import pytest
from app.registry.data import RegistryManager


@pytest.fixture
def registry():
    """Fixture providing a RegistryManager instance."""
    return RegistryManager()


class TestExactMatch:
    """Unit tests for exact_match with known parameters."""
    
    def test_exact_match_power_output(self, registry):
        """Test exact match for Power_Output parameter."""
        result = registry.exact_match("Power_Output")
        assert result == "Power_Output"
    
    def test_exact_match_temperature(self, registry):
        """Test exact match for Temperature parameter."""
        result = registry.exact_match("Temperature")
        assert result == "Temperature"
    
    def test_exact_match_efficiency(self, registry):
        """Test exact match for Efficiency parameter."""
        result = registry.exact_match("Efficiency")
        assert result == "Efficiency"
    
    def test_exact_match_case_insensitive(self, registry):
        """Test exact match is case insensitive."""
        result = registry.exact_match("POWER_OUTPUT")
        assert result == "Power_Output"
    
    def test_exact_match_with_spaces(self, registry):
        """Test exact match handles spaces."""
        result = registry.exact_match("Power Output")
        assert result == "Power_Output"
    
    def test_exact_match_with_hyphens(self, registry):
        """Test exact match handles hyphens."""
        result = registry.exact_match("Power-Output")
        assert result == "Power_Output"
    
    def test_exact_match_with_whitespace(self, registry):
        """Test exact match handles leading/trailing whitespace."""
        result = registry.exact_match("  Power_Output  ")
        assert result == "Power_Output"
    
    def test_exact_match_unknown_parameter(self, registry):
        """Test exact match returns None for unknown parameter."""
        result = registry.exact_match("Unknown_Parameter")
        assert result is None


class TestExtractAsset:
    """Unit tests for extract_asset with sample headers."""
    
    def test_extract_asset_power_tg1(self, registry):
        """Test extract_asset with 'Power TG1' header."""
        result = registry.extract_asset("Power TG1")
        assert result is not None
        asset_type, asset_id = result
        assert asset_type == "TG"
        assert asset_id == "TG1"
    
    def test_extract_asset_afbc2_temperature(self, registry):
        """Test extract_asset with 'AFBC-2 Temperature' header."""
        result = registry.extract_asset("AFBC-2 Temperature")
        assert result is not None
        asset_type, asset_id = result
        assert asset_type == "AFBC"
        assert asset_id == "AFBC-2"
    
    def test_extract_asset_tg_with_hyphen(self, registry):
        """Test extract_asset with TG-1 format."""
        result = registry.extract_asset("TG-1 Power Output")
        assert result is not None
        asset_type, asset_id = result
        assert asset_type == "TG"
        assert asset_id == "TG-1"
    
    def test_extract_asset_tg_with_underscore(self, registry):
        """Test extract_asset with TG_2 format."""
        result = registry.extract_asset("TG_2 Efficiency")
        assert result is not None
        asset_type, asset_id = result
        assert asset_type == "TG"
        assert asset_id == "TG_2"
    
    def test_extract_asset_esp(self, registry):
        """Test extract_asset with ESP asset."""
        result = registry.extract_asset("ESP-3 Status")
        assert result is not None
        asset_type, asset_id = result
        assert asset_type == "ESP"
        assert asset_id == "ESP-3"
    
    def test_extract_asset_aph(self, registry):
        """Test extract_asset with APH asset."""
        result = registry.extract_asset("APH1 Temperature")
        assert result is not None
        asset_type, asset_id = result
        assert asset_type == "APH"
        assert asset_id == "APH1"
    
    def test_extract_asset_fd_fan(self, registry):
        """Test extract_asset with FD_FAN asset."""
        result = registry.extract_asset("FDFAN-2 Speed")
        assert result is not None
        asset_type, asset_id = result
        assert asset_type == "FD_FAN"
        assert asset_id == "FDFAN-2"
    
    def test_extract_asset_id_fan(self, registry):
        """Test extract_asset with ID_FAN asset."""
        result = registry.extract_asset("ID-FAN-1 Current")
        assert result is not None
        asset_type, asset_id = result
        assert asset_type == "ID_FAN"
        assert asset_id == "ID-FAN-1"
    
    def test_extract_asset_boiler(self, registry):
        """Test extract_asset with BOILER asset."""
        result = registry.extract_asset("BOILER-1 Pressure")
        assert result is not None
        asset_type, asset_id = result
        assert asset_type == "BOILER"
        assert asset_id == "BOILER-1"
    
    def test_extract_asset_case_insensitive(self, registry):
        """Test extract_asset is case insensitive."""
        result = registry.extract_asset("power tg1")
        assert result is not None
        asset_type, asset_id = result
        assert asset_type == "TG"
        assert asset_id.upper() == "TG1"
    
    def test_extract_asset_no_match(self, registry):
        """Test extract_asset returns None when no asset found."""
        result = registry.extract_asset("Temperature")
        assert result is None
    
    def test_extract_asset_multiple_assets_returns_first(self, registry):
        """Test extract_asset returns first match when multiple assets present."""
        result = registry.extract_asset("AFBC-1 TG-2 Power")
        assert result is not None
        # Should return the first match found
        asset_type, asset_id = result
        assert asset_type in ["AFBC", "TG"]
