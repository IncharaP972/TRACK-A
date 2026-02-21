export type MatchMethod = 'exact' | 'fuzzy' | 'llm' | 'none'
export type ConfidenceLevel = 'high' | 'medium' | 'low'

export interface HeaderMapping {
  original_header: string
  matched_parameter: string | null
  matched_asset: string | null
  method: MatchMethod
  confidence: ConfidenceLevel
  normalized_header: string | null
}

export interface ParsedCell {
  row_index: number
  column_index: number
  original_value: any
  parsed_value: number | string | boolean | null
  header_mapping: HeaderMapping
  parse_success: boolean
  parse_error: string | null
}

export interface TableStructure {
  header_row_index: number
  data_start_row: number
  column_count: number
  merged_cells: Array<{
    min_row: number
    max_row: number
    min_col: number
    max_col: number
  }>
}

export interface ParseResult {
  file_name: string
  table_structure: TableStructure
  header_mappings: HeaderMapping[]
  parsed_data: ParsedCell[][]
  total_cells: number
  successful_parses: number
  llm_calls_made: number
}
