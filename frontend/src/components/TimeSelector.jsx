function TimeSelector({ value, onChange }) {
  const timeOptions = [
    { value: 5, label: '5 min' },
    { value: 10, label: '10 min' },
    { value: 15, label: '15 min' },
    { value: 30, label: '30 min' },
    { value: 60, label: '1 hr' },
    { value: 90, label: '1.5 hr' },
    { value: 120, label: '2 hr' },
  ]

  return (
    <div className="glass-panel">
      <div className="panel-title">2. Select Bet Timing</div>
      <div className="time-options">
        {timeOptions.map((option) => (
          <div
            key={option.value}
            onClick={() => onChange(option.value)}
            className={`time-option ${value === option.value ? 'selected' : ''}`}
          >
            <div className="time-value">{option.value}</div>
            <div className="time-label">min before</div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default TimeSelector
