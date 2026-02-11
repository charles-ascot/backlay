import { useState } from 'react'

function ResultsTable({ betResults, rulesBreakdown }) {
  const [activeTab, setActiveTab] = useState('bets')

  const formatCurrency = (value) => {
    const formatted = Math.abs(value).toFixed(2)
    const sign = value >= 0 ? '+' : '-'
    return `${sign}£${formatted}`
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

  return (
    <div className="glass p-6">
      {/* Tabs */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex gap-2">
          <button
            onClick={() => setActiveTab('bets')}
            className={`px-6 py-2 rounded-lg font-medium transition-all ${
              activeTab === 'bets'
                ? 'bg-blue-500 text-white'
                : 'bg-white/10 text-gray-300 hover:bg-white/20'
            }`}
          >
            All Bets ({betResults.length})
          </button>
          <button
            onClick={() => setActiveTab('rules')}
            className={`px-6 py-2 rounded-lg font-medium transition-all ${
              activeTab === 'rules'
                ? 'bg-blue-500 text-white'
                : 'bg-white/10 text-gray-300 hover:bg-white/20'
            }`}
          >
            By Rule ({rulesBreakdown.length})
          </button>
        </div>

        {activeTab === 'bets' && (
          <button
            onClick={exportToCSV}
            className="btn-secondary flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Export CSV
          </button>
        )}
      </div>

      {/* Bets Table */}
      {activeTab === 'bets' && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/20">
                <th className="text-left p-3 font-semibold">Venue</th>
                <th className="text-left p-3 font-semibold">Race Time</th>
                <th className="text-left p-3 font-semibold">Runner</th>
                <th className="text-right p-3 font-semibold">Odds</th>
                <th className="text-right p-3 font-semibold">Stake</th>
                <th className="text-right p-3 font-semibold">Liability</th>
                <th className="text-center p-3 font-semibold">Result</th>
                <th className="text-right p-3 font-semibold">P&L</th>
                <th className="text-left p-3 font-semibold">Rule</th>
              </tr>
            </thead>
            <tbody>
              {betResults.map((bet, index) => (
                <tr
                  key={index}
                  className="border-b border-white/10 hover:bg-white/5 transition-colors"
                >
                  <td className="p-3">{bet.venue}</td>
                  <td className="p-3 text-gray-300 text-xs">
                    {formatTime(bet.race_time)}
                  </td>
                  <td className="p-3 font-medium">{bet.runner_name}</td>
                  <td className="p-3 text-right font-mono">{bet.odds.toFixed(2)}</td>
                  <td className="p-3 text-right">£{bet.stake.toFixed(2)}</td>
                  <td className="p-3 text-right text-gray-400">£{bet.liability.toFixed(2)}</td>
                  <td className="p-3 text-center">
                    <span
                      className={`inline-block px-2 py-1 rounded text-xs font-medium ${
                        bet.actual_result === 'WINNER'
                          ? 'bg-red-500/20 text-red-400'
                          : bet.actual_result === 'LOSER'
                          ? 'bg-green-500/20 text-green-400'
                          : 'bg-gray-500/20 text-gray-400'
                      }`}
                    >
                      {bet.actual_result}
                    </span>
                  </td>
                  <td
                    className={`p-3 text-right font-bold ${
                      bet.profit_loss >= 0 ? 'text-green-400' : 'text-red-400'
                    }`}
                  >
                    {formatCurrency(bet.profit_loss)}
                  </td>
                  <td className="p-3 text-xs text-gray-400">{bet.rule_applied}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Rules Breakdown Table */}
      {activeTab === 'rules' && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/20">
                <th className="text-left p-3 font-semibold">Rule</th>
                <th className="text-right p-3 font-semibold">Total Bets</th>
                <th className="text-right p-3 font-semibold">Wins</th>
                <th className="text-right p-3 font-semibold">Losses</th>
                <th className="text-right p-3 font-semibold">Win Rate</th>
                <th className="text-right p-3 font-semibold">Total Staked</th>
                <th className="text-right p-3 font-semibold">Total Liability</th>
                <th className="text-right p-3 font-semibold">Net P&L</th>
              </tr>
            </thead>
            <tbody>
              {rulesBreakdown.map((rule, index) => (
                <tr
                  key={index}
                  className="border-b border-white/10 hover:bg-white/5 transition-colors"
                >
                  <td className="p-3 font-medium">{rule.rule}</td>
                  <td className="p-3 text-right">{rule.total_bets}</td>
                  <td className="p-3 text-right text-green-400">{rule.wins}</td>
                  <td className="p-3 text-right text-red-400">{rule.losses}</td>
                  <td className="p-3 text-right font-mono">{rule.win_rate}%</td>
                  <td className="p-3 text-right">£{rule.total_staked.toFixed(2)}</td>
                  <td className="p-3 text-right text-gray-400">
                    £{rule.total_liability.toFixed(2)}
                  </td>
                  <td
                    className={`p-3 text-right font-bold ${
                      rule.net_pnl >= 0 ? 'text-green-400' : 'text-red-400'
                    }`}
                  >
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
