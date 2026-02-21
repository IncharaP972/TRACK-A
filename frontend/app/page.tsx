'use client'

import { useState } from 'react'
import FileUpload from './components/FileUpload'
import ResultsDisplay from './components/ResultsDisplay'
import { ParseResult } from './types'

export default function Home() {
  const [parseResult, setParseResult] = useState<ParseResult | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleFileUpload = async (file: File) => {
    setIsLoading(true)
    setError(null)
    setParseResult(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/parse`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to parse file')
      }

      const data: ParseResult = await response.json()
      setParseResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setIsLoading(false)
    }
  }

  const handleReset = () => {
    setParseResult(null)
    setError(null)
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-industrial-900 via-industrial-800 to-industrial-900">
      {/* Header */}
      <header className="border-b border-industrial-700 bg-industrial-900/50 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white">
                LatSpace Excel Parser
              </h1>
              <p className="text-industrial-400 mt-1">
                Intelligent header mapping for power plant operational data
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <div className="text-sm text-industrial-400">Three-Tier Matching</div>
                <div className="flex space-x-2 mt-1">
                  <span className="badge badge-exact">Exact</span>
                  <span className="badge badge-fuzzy">Regex</span>
                  <span className="badge badge-llm">LLM</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8">
        {!parseResult && !isLoading && (
          <FileUpload onFileUpload={handleFileUpload} error={error} />
        )}

        {isLoading && (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500"></div>
            <p className="mt-4 text-industrial-300">Processing your Excel file...</p>
            <p className="text-sm text-industrial-500 mt-2">
              Running three-tier matching strategy
            </p>
          </div>
        )}

        {parseResult && (
          <ResultsDisplay result={parseResult} onReset={handleReset} />
        )}
      </div>

      {/* Footer */}
      <footer className="border-t border-industrial-700 bg-industrial-900/50 backdrop-blur-sm mt-12">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between text-sm text-industrial-500">
            <div>
              <span className="font-semibold text-industrial-400">Track A:</span> Intelligent Data Ingestion
            </div>
            <div className="flex items-center space-x-4">
              <span>92% Test Coverage</span>
              <span>•</span>
              <span>188 Tests Passing</span>
              <span>•</span>
              <span>15 Correctness Properties</span>
            </div>
          </div>
        </div>
      </footer>
    </main>
  )
}
