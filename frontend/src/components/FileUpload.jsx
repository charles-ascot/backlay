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
    <div className="glass-panel">
      <div className="panel-title">1. Upload Historical Data</div>

      <div
        onClick={() => fileInputRef.current?.click()}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        className="upload-zone"
      >
        <div className="upload-icon">&#128228;</div>
        <div className="upload-text">Drop NDJSON files here or click to browse</div>
        <div className="upload-subtext">One file per market (Betfair historical stream format)</div>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept=".ndjson,.txt,.json"
        onChange={handleFileChange}
        className="hidden"
      />

      {files.length > 0 && (
        <div className="file-list">
          <div className="file-list-title">
            Uploaded Files ({files.length})
          </div>
          {files.map((file, index) => (
            <div key={index} className="file-item">
              <div className="file-info">
                <span className="file-icon">&#128196;</span>
                <span className="file-name">{file.name}</span>
                <span className="file-size">
                  {(file.size / 1024).toFixed(1)} KB
                </span>
              </div>
              <button
                onClick={() => removeFile(index)}
                className="file-remove"
              >
                &#10005;
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default FileUpload
