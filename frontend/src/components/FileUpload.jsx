import { useRef } from 'react'

function FileUpload({ files, setFiles }) {
  const fileInputRef = useRef(null)

  const handleFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files)
    setFiles(selectedFiles)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    const droppedFiles = Array.from(e.dataTransfer.files)
    setFiles(droppedFiles)
  }

  const handleDragOver = (e) => {
    e.preventDefault()
  }

  const removeFile = (index) => {
    setFiles(files.filter((_, i) => i !== index))
  }

  return (
    <div className="glass p-6">
      <h2 className="text-2xl font-semibold mb-4">1. Upload Historical Data</h2>
      
      <div
        onClick={() => fileInputRef.current?.click()}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        className="border-2 border-dashed border-white/30 rounded-lg p-12 text-center cursor-pointer hover:border-blue-400/50 hover:bg-white/5 transition-all"
      >
        <div className="flex flex-col items-center gap-3">
          <svg className="w-16 h-16 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          <div>
            <p className="text-lg font-medium">Drop NDJSON files here or click to browse</p>
            <p className="text-sm text-gray-400 mt-1">One file per market (Betfair historical stream format)</p>
          </div>
        </div>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept=".ndjson,.txt"
        onChange={handleFileChange}
        className="hidden"
      />

      {files.length > 0 && (
        <div className="mt-6">
          <h3 className="text-lg font-medium mb-3">
            Uploaded Files ({files.length})
          </h3>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {files.map((file, index) => (
              <div
                key={index}
                className="flex items-center justify-between glass-dark p-3"
              >
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <svg className="w-5 h-5 text-blue-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <span className="truncate text-sm">{file.name}</span>
                  <span className="text-xs text-gray-400 flex-shrink-0">
                    {(file.size / 1024).toFixed(1)} KB
                  </span>
                </div>
                <button
                  onClick={() => removeFile(index)}
                  className="ml-4 text-red-400 hover:text-red-300 flex-shrink-0"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default FileUpload
