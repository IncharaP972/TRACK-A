'use client'

import { ParseResult, HeaderMapping, ConfidenceLevel, MatchMethod } from '../types'

interface ResultsDisplayProps {
  result: ParseResult
  onReset: () => void
}

export default function ResultsDisplay({ result, onReset }: ResultsDisplayProps) {
  const getMethodBadge = (method: MatchMethod) => {
    const badges = {
      exact: 'badge-exact',
      fuzzy: 'badge-fuzzy',
      llm: 'badge-llm',
      none: 'badge-none',
    }
    const labels = {
      exact: 'Tier 1: Exact',
      fuzzy: 'Tier 2: Regex',
      llm: 'Tier 3: LLM',
      none: 'Unmapped',
    }
    return (
      <span className={`badge ${badges[method]}`}>
        {labels[method]}
      </span>
    )
  }

  const getConfidenceClass = (confidence: ConfidenceLevel) => {
    const classes = {
      high: 'confidence-high',
      medium: 'confidence-medium',
      low: 'confidence-low',
    }
    return classes[confidence]
  }

  const lowConfidenceMappings = result.header_mappings.filter(
    (m) => m.confidence === 'low'
  )
  const unmappedColumns = result.header_mappings.filter(
    (m) => m.method === 'none'
  )

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card p-6">
          <div className="text-sm text-industrial-400 mb-1">File Name</div>
          <div className="text-xl font-bold text-white truncate">
            {result.file_name}
          </div>
        </div>
        <div className="card p-6">
          <div className="text-sm text-industrial-400 mb-1">Total Cells</div>
          <div className="text-xl font-bold text-white">
            {result.total_cells.toLocaleString()}
          </div>
          <div className="text-xs text-industrial-500 mt-1">
            {result.successful_parses} successful
          </div>
        </div>
        <div className="card p-6">
          <div className="text-sm text-industrial-400 mb-1">LLM Calls</div>
          <div className="text-xl font-bold text-white">
            {result.llm_calls_made}
          </div>
          <div className="text-xs text-industrial-500 mt-1">
            Batch efficiency
          </div>
        </div>
        <div className="card p-6">
          <div className="text-sm text-industrial-400 mb-1">Header Row</div>
          <div className="text-xl font-bold text-white">
            Row {result.table_structure.header_row_index}
          </div>
          <div className="text-xs text-industrial-500 mt-1">
            {result.table_structure.column_count} columns
          </div>
        </div>
      </div>

      {/* Alerts for Low Confidence and Unmapped */}
      {(lowConfidenceMappings.length > 0 || unmappedColumns.length > 0) && (
        <div className="space-y-3">
          {unmappedColumns.length > 0 && (
            <div className="card p-4 border-red-700 bg-red-900/20">
              <div className="flex items-start">
                <svg
                  className="w-5 h-5 text-red-400 mr-3 mt-0.5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                  />
                </svg>
                <div className="flex-1">
                  <h3 className="text-red-300 font-semibold mb-1">
                    {unmappedColumns.length} Unmapped Column{unmappedColumns.length > 1 ? 's' : ''}
                  </h3>
                  <p className="text-sm text-red-400">
                    {unmappedColumns.map((m) => m.original_header).join(', ')}
                  </p>
                </div>
              </div>
            </div>
          )}
          {lowConfidenceMappings.length > 0 && (
            <div className="card p-4 border-yellow-700 bg-yellow-900/20">
              <div className="flex items-start">
                <svg
                  className="w-5 h-5 text-yellow-400 mr-3 mt-0.5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <div className="flex-1">
                  <h3 className="text-yellow-300 font-semibold mb-1">
                    {lowConfidenceMappings.length} Low Confidence Mapping{lowConfidenceMappings.length > 1 ? 's' : ''}
                  </h3>
                  <p className="text-sm text-yellow-400">
                    Review these mappings for accuracy
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Header Mappings Table */}
      <div className="card overflow-hidden">
        <div className="p-6 border-b border-industrial-700">
          <h2 className="text-xl font-bold text-white">Header Mappings</h2>
          <p className="text-sm text-industrial-400 mt-1">
            Audit trail showing the matching method for each column
          </p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-industrial-900/50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-industrial-400 uppercase tracking-wider">
                  Original Header
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-industrial-400 uppercase tracking-wider">
                  Matched Parameter
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-industrial-400 uppercase tracking-wider">
                  Asset
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-industrial-400 uppercase tracking-wider">
                  Method
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-industrial-400 uppercase tracking-wider">
                  Confidence
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-industrial-700">
              {result.header_mappings.map((mapping, idx) => (
                <tr
                  key={idx}
                  className={`hover:bg-industrial-700/30 transition-colors ${
                    mapping.confidence === 'low' ? 'bg-yellow-900/10' : ''
                  } ${mapping.method === 'none' ? 'bg-red-900/10' : ''}`}
                >
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-white">
                    {mapping.original_header}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-industrial-300">
                    {mapping.matched_parameter || (
                      <span className="text-industrial-500 italic">None</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-industrial-300">
                    {mapping.matched_asset || (
                      <span className="text-industrial-500 italic">None</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {getMethodBadge(mapping.method)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span className={`font-semibold ${getConfidenceClass(mapping.confidence)}`}>
                      {mapping.confidence.toUpperCase()}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Parsed Data Preview */}
      <div className="card overflow-hidden">
        <div className="p-6 border-b border-industrial-700">
          <h2 className="text-xl font-bold text-white">Parsed Data Preview</h2>
          <p className="text-sm text-industrial-400 mt-1">
            First {Math.min(10, result.parsed_data.length)} rows of parsed data
          </p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-industrial-900/50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-industrial-400 uppercase">
                  Row
                </th>
                {result.header_mappings.map((mapping, idx) => (
                  <th
                    key={idx}
                    className="px-4 py-3 text-left text-xs font-medium text-industrial-400 uppercase"
                  >
                    {mapping.matched_parameter || mapping.original_header}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-industrial-700">
              {result.parsed_data.slice(0, 10).map((row, rowIdx) => (
                <tr key={rowIdx} className="hover:bg-industrial-700/30 transition-colors">
                  <td className="px-4 py-3 whitespace-nowrap text-industrial-400 font-mono">
                    {row[0]?.row_index || rowIdx + 1}
                  </td>
                  {row.map((cell, cellIdx) => (
                    <td
                      key={cellIdx}
                      className={`px-4 py-3 whitespace-nowrap ${
                        cell.parse_success ? 'text-white' : 'text-red-400'
                      }`}
                    >
                      {cell.parsed_value !== null && cell.parsed_value !== undefined
                        ? String(cell.parsed_value)
                        : <span className="text-industrial-500 italic">null</span>}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {result.parsed_data.length > 10 && (
          <div className="p-4 bg-industrial-900/50 text-center text-sm text-industrial-400">
            Showing 10 of {result.parsed_data.length} rows
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex justify-center">
        <button onClick={onReset} className="btn-primary">
          Parse Another File
        </button>
      </div>
    </div>
  )
}
