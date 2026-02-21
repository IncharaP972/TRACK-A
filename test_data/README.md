# Test Data Files

This directory contains test Excel files designed to validate the three-tier matching strategy of the LatSpace Intelligent Excel Parser.

## 📊 Test Files Overview

### 1. clean_data.xlsx - Baseline Test (Tier 1 Only)
**Purpose**: Validate exact matching with perfectly formatted headers

**Characteristics**:
- 6 headers with exact registry matches
- 8 data rows
- Clean numeric formatting
- No ambiguity

**Expected Results**:
- ✅ 100% Tier 1 (Exact) matches
- ✅ High confidence on all mappings
- ✅ 0 LLM calls
- ✅ All values parsed successfully

**Headers**:
- Power_Output
- Temperature
- Efficiency
- Fuel_Consumption
- Emissions_CO2
- Steam_Pressure

---

### 2. messy_data.xlsx - Fuzzy Matching Test (Tier 1 + Tier 2)
**Purpose**: Validate regex-based asset extraction and parameter inference

**Characteristics**:
- 7 headers (3 exact, 4 with asset identifiers)
- 10 data rows
- Asset patterns: TG-1, AFBC-2, ESP-3, ID-FAN-1
- Mixed formatting

**Expected Results**:
- ✅ 3 Tier 1 (Exact) matches: Power_Output, Fuel_Consumption, Emissions_CO2
- ✅ 4 Tier 2 (Regex) matches: TG-1 Temperature, AFBC-2 Efficiency, ESP-3 Status, ID-FAN-1 Speed
- ✅ 0 LLM calls (all deterministic)
- ✅ Medium-high confidence

**Headers**:
- Power_Output (Exact)
- TG-1 Temperature (Asset + Parameter)
- AFBC-2 Efficiency (Asset + Parameter)
- ESP-3 Status (Asset only)
- Fuel_Consumption (Exact)
- ID-FAN-1 Speed (Asset only)
- Emissions_CO2 (Exact)

---

### 3. multi_asset.xlsx - Multi-Tier Test (All Three Tiers)
**Purpose**: Validate complete three-tier strategy including LLM semantic matching

**Characteristics**:
- 10 headers (1 exact, 6 asset-based, 3 ambiguous)
- 12 data rows with timestamps
- Multiple asset instances (TG-1, TG-2, AFBC-1, AFBC-2, ESP-1)
- Ambiguous headers requiring LLM interpretation

**Expected Results**:
- ✅ 1 Tier 1 (Exact) match: Fuel_Consumption
- ✅ 6 Tier 2 (Regex) matches: TG-1 Power_Output, TG-2 Power_Output, AFBC-1 Temperature, AFBC-2 Temperature, ESP-1 Availability
- ✅ 3 Tier 3 (LLM) matches: Boiler Heat Input, Plant Efficiency Rate, CO2 Emissions Level
- ✅ 1 LLM call (batch processing all 3 ambiguous headers)
- ✅ 1 Unmapped: Timestamp

**Headers**:
- Timestamp (Unmapped)
- TG-1 Power_Output (Asset + Exact)
- TG-2 Power_Output (Asset + Exact)
- AFBC-1 Temperature (Asset + Exact)
- AFBC-2 Temperature (Asset + Exact)
- Boiler Heat Input (LLM - ambiguous)
- Plant Efficiency Rate (LLM - ambiguous)
- CO2 Emissions Level (LLM - ambiguous)
- Fuel_Consumption (Exact)
- ESP-1 Availability (Asset)

---

### 4. cea_coal_report_real.xlsx - Real-World Dirty Data Test
**Purpose**: Validate robustness with real-world CEA (Central Electricity Authority) coal report data

**Characteristics**:
- Complex merged header cells (2-row headers)
- Regional grouping rows (NORTHERN REGION, WESTERN REGION)
- Mixed units embedded in cells:
  - "1980 MW" (unit in cell)
  - "43.6%" (percentage symbol)
  - "241.01 T" (tonnes abbreviation)
  - "33.67 k" (thousands abbreviation)
- Inconsistent null representations:
  - "nil"
  - "zero"
  - "-"
  - "0"
- Abbreviations: "Sec.", "MW Cap.", "PLF%"
- Real power station names and locations

**Expected Results**:
- ✅ Header row detection handles merged cells
- ✅ Parser strips units from numeric values
- ✅ Normalizes all null variations to None
- ✅ Handles percentage conversion
- ✅ Processes regional grouping rows
- ✅ Maps abbreviated headers to registry

**Headers** (Row 4-5, merged):
- Region/State
- Transport Mode
- Power Station Name
- Sec. (Sector abbreviation)
- MW Cap. (Megawatt Capacity)
- PLF% (JAN-19) (Plant Load Factor)
- PLF% (APR-JAN)
- Norm Stock (Days)
- Daily Req. (k Tonnes)
- STOCK IN HAND (merged):
  - Indig. (Indigenous)
  - Imp. (Imported)
  - Total Stock
- Days
- Criticality/Remarks

**Data Quality Issues** (Intentional):
- Row 1-3: Title/logo noise
- Row 6, 9: Regional grouping rows (bold, no data)
- Mixed formats: "1 day" vs "14" vs "33"
- Units in cells: "1980 MW", "241.01 T", "33.67 k"
- Percentage symbols: "43.6%", "44.8%"
- Null variations: "nil", "zero", "-", "0"
- Comma separators: "1,127.72"

---

## 🧪 Running Tests

### Generate All Test Files
```bash
# Generate original 3 test files
python test_data/create_test_data.py

# Generate CEA report
python test_data/create_cea_report.py
```

### Test with Frontend
1. Start the backend and frontend (see main README.md)
2. Navigate to http://localhost:3000
3. Upload each test file and observe:
   - Header mapping methods (Tier 1/2/3 badges)
   - Confidence levels
   - LLM call count
   - Parsed data preview

### Test with API
```bash
# Test clean data
curl -X POST "http://localhost:8000/api/parse" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test_data/clean_data.xlsx"

# Test messy data
curl -X POST "http://localhost:8000/api/parse" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test_data/messy_data.xlsx"

# Test multi-tier
curl -X POST "http://localhost:8000/api/parse" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test_data/multi_asset.xlsx"

# Test CEA report
curl -X POST "http://localhost:8000/api/parse" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test_data/cea_coal_report_real.xlsx"
```

---

## 📈 Expected Performance

| File | Headers | Tier 1 | Tier 2 | Tier 3 | LLM Calls | Processing Time |
|------|---------|--------|--------|--------|-----------|-----------------|
| clean_data.xlsx | 6 | 6 | 0 | 0 | 0 | <100ms |
| messy_data.xlsx | 7 | 3 | 4 | 0 | 0 | <150ms |
| multi_asset.xlsx | 10 | 1 | 6 | 3 | 1 | 500-2000ms |
| cea_coal_report_real.xlsx | 14 | ~5 | ~5 | ~4 | 1 | 500-2000ms |

---

## 🎯 Test Coverage

These test files validate:

✅ **Tier 1 (Exact Matching)**:
- Case insensitivity
- Whitespace normalization
- Special character handling
- O(1) lookup performance

✅ **Tier 2 (Regex Asset Extraction)**:
- Asset pattern recognition (AFBC-1, TG-2, ESP-3, etc.)
- Parameter inference from context
- Deterministic matching
- Medium-high confidence assignment

✅ **Tier 3 (LLM Semantic Matching)**:
- Batch processing (single API call per file)
- Ambiguous header interpretation
- Confidence level assignment
- Structured output parsing

✅ **Value Parsing**:
- Comma removal: "1,234.56" → 1234.56
- Percentage conversion: "45%" → 0.45
- Unit stripping: "1980 MW" → 1980
- Null normalization: "N/A", "nil", "-" → None
- Boolean conversion: "YES" → 1.0, "NO" → 0.0

✅ **Table Structure Detection**:
- Header row identification
- Merged cell handling
- Data start row detection
- Column count validation

✅ **Error Handling**:
- Invalid file types
- Empty files
- Missing headers
- Unparseable values

---

## 🔧 Customization

To create your own test files:

1. Copy one of the generator scripts
2. Modify headers to match your use case
3. Add data rows with various formats
4. Run the script to generate the Excel file
5. Test with the parser

Example:
```python
from openpyxl import Workbook

wb = Workbook()
ws = wb.active

# Add your headers
ws.append(["Custom_Header_1", "Custom_Header_2"])

# Add your data
ws.append(["value1", "value2"])

wb.save("test_data/custom_test.xlsx")
```

---

## 📝 Notes

- All test files use realistic power plant operational data
- Data values are synthetic but follow real-world patterns
- Files are designed to be progressively more challenging
- CEA report mimics actual government report structure
- Test files are version controlled for reproducibility

---

**Generated by**: LatSpace Excel Parser Test Suite
**Last Updated**: February 2026
