import { useState } from 'react'
import FileUpload from './components/FileUpload'
import TimeSelector from './components/TimeSelector'
import ResultsTable from './components/ResultsTable'
import Summary from './components/Summary'

function App() {
  const [files, setFiles] = useState([])
  const [gcsUrl, setGcsUrl] = useState('')
  const [inputMode, setInputMode] = useState('files')  // 'files' | 'gcs'
  const [minutesBefore, setMinutesBefore] = useState(30)
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)

  const canRun = inputMode === 'files'
    ? files.length > 0
    : gcsUrl.length > 5  // "gs://X" minimum

  const handleRunBacktest = async () => {
    if (!canRun) {
      setError(
        inputMode === 'files'
          ? 'Please upload at least one file'
          : 'Please enter a GCS bucket URL'
      )
      return
    }

    setLoading(true)
    setError(null)
    setResults(null)

    try {
      const apiBase = import.meta.env.VITE_API_URL || ''
      let response

      if (inputMode === 'files') {
        // Existing file upload flow
        const formData = new FormData()
        files.forEach(file => {
          formData.append('files', file)
        })
        formData.append('minutes_before', minutesBefore)

        response = await fetch(`${apiBase}/api/backtest/run`, {
          method: 'POST',
          body: formData,
        })
      } else {
        // GCS bucket flow
        response = await fetch(`${apiBase}/api/backtest/run-gcs`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            gcs_url: gcsUrl,
            minutes_before: minutesBefore,
          }),
        })
      }

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Backtest failed')
      }

      const data = await response.json()
      setResults(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setFiles([])
    setGcsUrl('')
    setResults(null)
    setError(null)
  }

  const getButtonLabel = () => {
    if (loading) {
      return inputMode === 'files'
        ? `Processing ${files.length} market(s)...`
        : 'Scanning GCS & processing...'
    }
    return inputMode === 'files'
      ? `Run Simulation (${files.length} file${files.length !== 1 ? 's' : ''})`
      : 'Run Simulation (GCS)'
  }

  return (
    <>
      <div className="image-bg" />
      <div className="login-overlay" />
      <div className="app">
        <div className="header">
          <div>
            <div className="header-title">CHIMERA</div>
            <div className="header-subtitle">Backtest Simulator</div>
          </div>
        </div>

        <div className="content">
          <div className="main-container">
            {/* Input Section */}
            {!results && (
              <>
                <FileUpload
                  files={files}
                  setFiles={setFiles}
                  gcsUrl={gcsUrl}
                  setGcsUrl={setGcsUrl}
                  inputMode={inputMode}
                  setInputMode={setInputMode}
                />
                <TimeSelector value={minutesBefore} onChange={setMinutesBefore} />

                {error && (
                  <div className="error-message">{error}</div>
                )}

                <button
                  onClick={handleRunBacktest}
                  disabled={loading || !canRun}
                  className="button-primary"
                >
                  {loading ? (
                    <>
                      <span className="spinner" />
                      {getButtonLabel()}
                    </>
                  ) : (
                    getButtonLabel()
                  )}
                </button>
              </>
            )}

            {/* Results Section */}
            {results && (
              <>
                <Summary summary={results.summary} minutesBefore={results.minutes_before_race} />
                <ResultsTable
                  betResults={results.bet_results}
                  rulesBreakdown={results.rules_breakdown}
                />

                <div className="flex-center mt-24">
                  <button onClick={handleReset} className="button-reset">
                    Run Another Backtest
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </>
  )
}

export default App
