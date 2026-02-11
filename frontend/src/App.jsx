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
      const response = await fetch('/api/backtest/run', {
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
    <div className="min-h-screen p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
            CHIMERA Backtest Simulator
          </h1>
          <p className="text-gray-300 text-lg">
            Test your lay betting strategy on historical Betfair data
          </p>
        </div>

        {/* Input Section */}
        {!results && (
          <div className="space-y-6 mb-8">
            <FileUpload files={files} setFiles={setFiles} />
            <TimeSelector value={minutesBefore} onChange={setMinutesBefore} />
            
            {error && (
              <div className="glass-dark p-4 border-red-500/50">
                <p className="text-red-400">{error}</p>
              </div>
            )}

            <div className="flex justify-center gap-4">
              <button
                onClick={handleRunBacktest}
                disabled={loading || files.length === 0}
                className="btn-primary"
              >
                {loading ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Processing {files.length} market(s)...
                  </>
                ) : (
                  `Run Simulation (${files.length} file${files.length !== 1 ? 's' : ''})`
                )}
              </button>
            </div>
          </div>
        )}

        {/* Results Section */}
        {results && (
          <div className="space-y-6">
            <Summary summary={results.summary} minutesBefore={results.minutes_before_race} />
            <ResultsTable 
              betResults={results.bet_results} 
              rulesBreakdown={results.rules_breakdown}
            />
            
            <div className="flex justify-center">
              <button onClick={handleReset} className="btn-secondary">
                Run Another Backtest
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
