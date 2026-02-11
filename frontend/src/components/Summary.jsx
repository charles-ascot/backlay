function Summary({ summary, minutesBefore }) {
  const formatCurrency = (value) => {
    const formatted = Math.abs(value).toFixed(2)
    const sign = value >= 0 ? '+' : '-'
    return `${sign}£${formatted}`
  }

  const stats = [
    { label: 'Markets Processed', value: summary.total_markets },
    { label: 'Markets with Bets', value: summary.markets_with_bets },
    { label: 'Total Bets Placed', value: summary.total_bets },
    { label: 'Win Rate', value: `${summary.win_rate}%` },
    { label: 'Total Staked', value: `£${summary.total_staked}` },
    { label: 'Total Liability', value: `£${summary.total_liability}` },
  ]

  const pnlColor = summary.net_profit_loss >= 0 ? 'text-green-400' : 'text-red-400'
  const pnlBg = summary.net_profit_loss >= 0 ? 'bg-green-500/20' : 'bg-red-500/20'
  const pnlBorder = summary.net_profit_loss >= 0 ? 'border-green-500/50' : 'border-red-500/50'

  return (
    <div className="glass p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-3xl font-bold">Backtest Results</h2>
          <p className="text-gray-400 mt-1">
            Bets placed at {minutesBefore} minutes before race time
          </p>
        </div>
        <div className={`${pnlBg} ${pnlBorder} border-2 rounded-xl px-6 py-4`}>
          <div className="text-sm text-gray-300 mb-1">Net P&L</div>
          <div className={`text-4xl font-bold ${pnlColor}`}>
            {formatCurrency(summary.net_profit_loss)}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {stats.map((stat, index) => (
          <div key={index} className="glass-dark p-4 rounded-lg">
            <div className="text-xs text-gray-400 mb-1">{stat.label}</div>
            <div className="text-2xl font-bold">{stat.value}</div>
          </div>
        ))}
      </div>

      <div className="mt-6 grid grid-cols-3 gap-4 text-center">
        <div>
          <div className="text-sm text-gray-400">Winning Bets</div>
          <div className="text-3xl font-bold text-green-400">{summary.winning_bets}</div>
        </div>
        <div>
          <div className="text-sm text-gray-400">Losing Bets</div>
          <div className="text-3xl font-bold text-red-400">{summary.losing_bets}</div>
        </div>
        <div>
          <div className="text-sm text-gray-400">Markets Skipped</div>
          <div className="text-3xl font-bold text-gray-400">{summary.markets_skipped}</div>
        </div>
      </div>
    </div>
  )
}

export default Summary
