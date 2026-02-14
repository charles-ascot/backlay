function Summary({ summary, minutesBefore }) {
  const formatCurrency = (value) => {
    const formatted = Math.abs(value).toFixed(2)
    const sign = value >= 0 ? '+' : '-'
    return `${sign}\u00A3${formatted}`
  }

  const pnlPositive = summary.net_profit_loss >= 0

  return (
    <div className="glass-panel">
      <div className="panel-title">
        Backtest Results &mdash; {minutesBefore} min before race
      </div>

      {/* P&L Card */}
      <div className={`pnl-card ${pnlPositive ? 'positive' : 'negative'}`}>
        <div className="pnl-label">Net Profit / Loss</div>
        <div className={`pnl-value ${pnlPositive ? 'positive' : 'negative'}`}>
          {formatCurrency(summary.net_profit_loss)}
        </div>
      </div>

      {/* Stats Grid */}
      <div className="results-grid">
        <div className="result-card">
          <div className="result-value">{summary.total_markets}</div>
          <div className="result-label">Markets</div>
        </div>
        <div className="result-card">
          <div className="result-value">{summary.markets_with_bets}</div>
          <div className="result-label">With Bets</div>
        </div>
        <div className="result-card">
          <div className="result-value">{summary.total_bets}</div>
          <div className="result-label">Total Bets</div>
        </div>
        <div className="result-card">
          <div className="result-value">{summary.win_rate}%</div>
          <div className="result-label">Win Rate</div>
        </div>
        <div className="result-card">
          <div className="result-value positive">{summary.winning_bets}</div>
          <div className="result-label">Wins</div>
        </div>
        <div className="result-card">
          <div className="result-value negative">{summary.losing_bets}</div>
          <div className="result-label">Losses</div>
        </div>
        <div className="result-card">
          <div className="result-value">&pound;{summary.total_staked}</div>
          <div className="result-label">Total Staked</div>
        </div>
        <div className="result-card">
          <div className="result-value">&pound;{summary.total_liability}</div>
          <div className="result-label">Liability</div>
        </div>
      </div>
    </div>
  )
}

export default Summary
