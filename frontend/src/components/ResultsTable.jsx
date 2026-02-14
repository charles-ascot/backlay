import { useState } from 'react'

function ResultsTable({ betResults, rulesBreakdown }) {
  const [activeTab, setActiveTab] = useState('bets')

  const formatCurrency = (value) => {
    const formatted = Math.abs(value).toFixed(2)
    const sign = value >= 0 ? '+' : '-'
    return `${sign}\u00A3${formatted}`
  }

  const formatTime = (isoString) => {
    try {
      const date = new Date(isoString)
      return date.toLocaleString('en-GB', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    } catch {
      return isoString
    }
  }

  const exportToCSV = () => {
    const headers = ['Venue', 'Race Time', 'Runner', 'Odds', 'Stake', 'Liability', 'Result', 'P&L', 'Rule']
    const rows = betResults.map(bet => [
      bet.venue,
      bet.race_time,
      bet.runner_name,
      bet.odds,
      bet.stake,
      bet.liability,
      bet.actual_result,
      bet.profit_loss,
      bet.rule_applied,
    ])

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.join(','))
    ].join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `chimera-backtest-${new Date().toISOString().split('T')[0]}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  const getResultBadge = (result) => {
    if (result === 'WINNER') return 'badge badge-winner'
    if (result === 'LOSER') return 'badge badge-loser'
    return 'badge badge-removed'
  }

  return (
    <div className="glass-panel">
      {/* Tabs */}
      <div className="tab-bar">
        <button
          onClick={() => setActiveTab('bets')}
          className={`tab-button ${activeTab === 'bets' ? 'active' : ''}`}
        >
          All Bets ({betResults.length})
        </button>
        <button
          onClick={() => setActiveTab('rules')}
          className={`tab-button ${activeTab === 'rules' ? 'active' : ''}`}
        >
          By Rule ({rulesBreakdown.length})
        </button>

        <div className="tab-bar-spacer" />

        {activeTab === 'bets' && (
          <button onClick={exportToCSV} className="button-download">
            Export CSV
          </button>
        )}
      </div>

      {/* Bets Table */}
      {activeTab === 'bets' && (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Venue</th>
                <th>Race Time</th>
                <th>Runner</th>
                <th className="text-right">Odds</th>
                <th className="text-right">Stake</th>
                <th className="text-right">Liability</th>
                <th className="text-center">Result</th>
                <th className="text-right">P&L</th>
                <th>Rule</th>
              </tr>
            </thead>
            <tbody>
              {betResults.map((bet, index) => (
                <tr key={index}>
                  <td>{bet.venue}</td>
                  <td className="text-muted">{formatTime(bet.race_time)}</td>
                  <td style={{ fontWeight: 500 }}>{bet.runner_name}</td>
                  <td className="text-right font-mono">{bet.odds.toFixed(2)}</td>
                  <td className="text-right">&pound;{bet.stake.toFixed(2)}</td>
                  <td className="text-right text-muted">&pound;{bet.liability.toFixed(2)}</td>
                  <td className="text-center">
                    <span className={getResultBadge(bet.actual_result)}>
                      {bet.actual_result}
                    </span>
                  </td>
                  <td className={`text-right font-bold ${bet.profit_loss >= 0 ? 'text-positive' : 'text-negative'}`}>
                    {formatCurrency(bet.profit_loss)}
                  </td>
                  <td className="text-small">{bet.rule_applied}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Rules Breakdown Table */}
      {activeTab === 'rules' && (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Rule</th>
                <th className="text-right">Total Bets</th>
                <th className="text-right">Wins</th>
                <th className="text-right">Losses</th>
                <th className="text-right">Win Rate</th>
                <th className="text-right">Staked</th>
                <th className="text-right">Liability</th>
                <th className="text-right">Net P&L</th>
              </tr>
            </thead>
            <tbody>
              {rulesBreakdown.map((rule, index) => (
                <tr key={index}>
                  <td style={{ fontWeight: 600 }}>{rule.rule}</td>
                  <td className="text-right">{rule.total_bets}</td>
                  <td className="text-right text-positive">{rule.wins}</td>
                  <td className="text-right text-negative">{rule.losses}</td>
                  <td className="text-right font-mono">{rule.win_rate}%</td>
                  <td className="text-right">&pound;{rule.total_staked.toFixed(2)}</td>
                  <td className="text-right text-muted">&pound;{rule.total_liability.toFixed(2)}</td>
                  <td className={`text-right font-bold ${rule.net_pnl >= 0 ? 'text-positive' : 'text-negative'}`}>
                    {formatCurrency(rule.net_pnl)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default ResultsTable
