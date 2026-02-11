function TimeSelector({ value, onChange }) {
  const timeOptions = [
    { value: 5, label: '5 minutes before race' },
    { value: 10, label: '10 minutes before race' },
    { value: 15, label: '15 minutes before race' },
    { value: 30, label: '30 minutes before race' },
    { value: 60, label: '1 hour before race' },
    { value: 90, label: '1.5 hours before race' },
    { value: 120, label: '2 hours before race' },
  ]

  return (
    <div className="glass p-6">
      <h2 className="text-2xl font-semibold mb-4">2. Select Bet Timing</h2>
      <p className="text-gray-300 mb-4">
        Choose when to place bets before race start time
      </p>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
        {timeOptions.map((option) => (
          <button
            key={option.value}
            onClick={() => onChange(option.value)}
            className={`p-4 rounded-lg border-2 transition-all ${
              value === option.value
                ? 'border-blue-500 bg-blue-500/20 text-white'
                : 'border-white/20 bg-white/5 text-gray-300 hover:border-white/40 hover:bg-white/10'
            }`}
          >
            <div className="text-center">
              <div className="text-2xl font-bold">{option.value}</div>
              <div className="text-xs mt-1">minutes before</div>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}

export default TimeSelector
