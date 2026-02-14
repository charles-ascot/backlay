import { useState } from 'react'
import FileUpload from './components/FileUpload'
import TimeSelector from './components/TimeSelector'
import ResultsTable from './components/ResultsTable'
import Summary from './components/Summary'

function App() {
  const [files, setFiles] = useState([])
  const [minutesBefore, setMinutesBefore] = useState(30)
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)

  const handleRunBacktest = async () => {
    if (files.length === 0) {
      setError('Please upload at least one file')
      return
    }

    setLoading(true)
    setError(null)
    setResults(null)

    const formData = new FormData()
    files.forEach(file => {
      formData.append('files', file)
    })
    formData.append('minutes_before', minutesBefore)

    try {
      const apiBase = import.meta.env.VITE_API_URL || ''
      const response = await fetch(`${apiBase}/api/backtest/run`, {
        method: 'POST',
        body: formData,
      })

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
    setResults(null)
    setError(null)
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
                <FileUpload files={files} setFiles={setFiles} />
                <TimeSelector value={minutesBefore} onChange={setMinutesBefore} />

                {error && (
                  <div className="error-message">{error}</div>
                )}

                <button
                  onClick={handleRunBacktest}
                  disabled={loading || files.length === 0}
                  className="button-primary"
                >
                  {loading ? (
                    <>
                      <span className="spinner" />
                      Processing {files.length} market(s)...
                    </>
                  ) : (
                    `Run Simulation (${files.length} file${files.length !== 1 ? 's' : ''})`
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
