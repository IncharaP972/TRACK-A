'use client'

import { useCallback, useState } from 'react'

interface FileUploadProps {
  onFileUpload: (file: File) => void
  error: string | null
}

export default function FileUpload({ onFileUpload, error }: FileUploadProps) {
  const [dragActive, setDragActive] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0]
      if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
        setSelectedFile(file)
      } else {
        alert('Please upload an Excel file (.xlsx or .xls)')
      }
    }
  }, [])

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault()
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0])
    }
  }, [])

  const handleSubmit = () => {
    if (selectedFile) {
      onFileUpload(selectedFile)
    }
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="card p-8">
        <div className="text-center mb-6">
          <h2 className="text-2xl font-bold text-white mb-2">
            Upload Excel File
          </h2>
          <p className="text-industrial-400">
            Upload your power plant operational data for intelligent header mapping
          </p>
        </div>

        <div
          className={`relative border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
            dragActive
              ? 'border-blue-500 bg-blue-500/10'
              : 'border-industrial-600 hover:border-industrial-500'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            type="file"
            id="file-upload"
            className="hidden"
            accept=".xlsx,.xls"
            onChange={handleChange}
          />

          <div className="space-y-4">
            <div className="flex justify-center">
              <svg
                className="w-16 h-16 text-industrial-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                />
              </svg>
            </div>

            {selectedFile ? (
              <div className="space-y-2">
                <div className="inline-flex items-center px-4 py-2 bg-industrial-700 rounded-lg">
                  <svg
                    className="w-5 h-5 text-green-400 mr-2"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                  <span className="text-white font-medium">{selectedFile.name}</span>
                </div>
                <p className="text-sm text-industrial-400">
                  {(selectedFile.size / 1024).toFixed(2)} KB
                </p>
              </div>
            ) : (
              <>
                <p className="text-lg text-industrial-300">
                  Drag and drop your Excel file here, or
                </p>
                <label
                  htmlFor="file-upload"
                  className="inline-block btn-primary cursor-pointer"
                >
                  Browse Files
                </label>
              </>
            )}

            <p className="text-sm text-industrial-500">
              Supports .xlsx and .xls files
            </p>
          </div>
        </div>

        {error && (
          <div className="mt-4 p-4 bg-red-900/20 border border-red-700 rounded-lg">
            <div className="flex items-center">
              <svg
                className="w-5 h-5 text-red-400 mr-2"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <span className="text-red-300">{error}</span>
            </div>
          </div>
        )}

        {selectedFile && (
          <div className="mt-6 flex justify-center space-x-4">
            <button
              onClick={() => setSelectedFile(null)}
              className="btn-secondary"
            >
              Clear
            </button>
            <button onClick={handleSubmit} className="btn-primary">
              Parse File
            </button>
          </div>
        )}

        <div className="mt-8 pt-6 border-t border-industrial-700">
          <h3 className="text-sm font-semibold text-industrial-300 mb-3">
            Three-Tier Matching Strategy:
          </h3>
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div className="p-3 bg-industrial-900/50 rounded-lg">
              <div className="badge badge-exact mb-2">Tier 1: Exact</div>
              <p className="text-industrial-400">
                O(1) normalized matching for standard parameters
              </p>
            </div>
            <div className="p-3 bg-industrial-900/50 rounded-lg">
              <div className="badge badge-fuzzy mb-2">Tier 2: Regex</div>
              <p className="text-industrial-400">
                Asset extraction using compiled patterns
              </p>
            </div>
            <div className="p-3 bg-industrial-900/50 rounded-lg">
              <div className="badge badge-llm mb-2">Tier 3: LLM</div>
              <p className="text-industrial-400">
                Semantic matching via Gemini 1.5 Flash
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
