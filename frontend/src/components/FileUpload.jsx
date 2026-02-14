import { useRef } from 'react'

function FileUpload({ files, setFiles, gcsUrl, setGcsUrl, inputMode, setInputMode }) {
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
      <div className="panel-title">1. Select Data Source</div>

      {/* Mode tabs */}
      <div className="tab-bar" style={{ marginBottom: '20px' }}>
        <button
          onClick={() => setInputMode('files')}
          className={`tab-button ${inputMode === 'files' ? 'active' : ''}`}
        >
          Local Files
        </button>
        <button
          onClick={() => setInputMode('gcs')}
          className={`tab-button ${inputMode === 'gcs' ? 'active' : ''}`}
        >
          GCS Bucket
        </button>
      </div>

      {/* Mode: Local file upload */}
      {inputMode === 'files' && (
        <>
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
        </>
      )}

      {/* Mode: GCS Bucket URL */}
      {inputMode === 'gcs' && (
        <div className="gcs-input-section">
          <div className="gcs-input-wrapper">
            <span className="gcs-prefix">gs://</span>
            <input
              type="text"
              value={gcsUrl.replace(/^gs:\/\//, '')}
              onChange={(e) => setGcsUrl(`gs://${e.target.value}`)}
              placeholder="bucket-name/path/to/data/"
              className="gcs-input"
            />
          </div>
          <div className="upload-subtext" style={{ marginTop: '12px' }}>
            Enter a GCS bucket path containing NDJSON files.
            Supports .json, .ndjson, and .gz files.
          </div>
        </div>
      )}
    </div>
  )
}

export default FileUpload
