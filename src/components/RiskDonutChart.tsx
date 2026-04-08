interface RiskDonutChartProps {
  low: number;
  medium: number;
  high: number;
  total: number;
  size?: number;
  className?: string;
}

export default function RiskDonutChart({ low, medium, high, total, size = 200, className = '' }: RiskDonutChartProps) {
  if (total === 0) {
    return (
      <div className={`flex items-center justify-center ${className}`} style={{ width: size, height: size }}>
        <div className="text-center">
          <p className="text-slate-500 text-sm">No data</p>
        </div>
      </div>
    );
  }

  const radius = size / 2 - 10;
  const circumference = 2 * Math.PI * radius;
  
  const lowPercent = (low / total) * 100;
  const mediumPercent = (medium / total) * 100;
  const highPercent = (high / total) * 100;

  const lowDashOffset = 0;
  const mediumDashOffset = (lowPercent / 100) * circumference;
  const highDashOffset = ((lowPercent + mediumPercent) / 100) * circumference;

  return (
    <div className={`relative ${className}`} style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-90">
        {/* Low Risk - Green */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#10b981"
          strokeWidth="20"
          strokeDasharray={`${(lowPercent / 100) * circumference} ${circumference}`}
          strokeDashoffset={lowDashOffset}
          className="transition-all duration-500"
        />
        {/* Medium Risk - Amber */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#f59e0b"
          strokeWidth="20"
          strokeDasharray={`${(mediumPercent / 100) * circumference} ${circumference}`}
          strokeDashoffset={-mediumDashOffset}
          className="transition-all duration-500"
        />
        {/* High Risk - Red */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#ef4444"
          strokeWidth="20"
          strokeDasharray={`${(highPercent / 100) * circumference} ${circumference}`}
          strokeDashoffset={-highDashOffset}
          className="transition-all duration-500"
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="text-center">
          <p className="text-2xl font-bold text-slate-900">{total}</p>
          <p className="text-xs text-slate-500">Total</p>
        </div>
      </div>
      <div className="absolute -bottom-8 left-0 right-0 flex justify-center space-x-4 text-xs">
        <div className="flex items-center space-x-1">
          <div className="w-3 h-3 rounded-full bg-green-500"></div>
          <span className="text-slate-600">{low}</span>
        </div>
        <div className="flex items-center space-x-1">
          <div className="w-3 h-3 rounded-full bg-amber-500"></div>
          <span className="text-slate-600">{medium}</span>
        </div>
        <div className="flex items-center space-x-1">
          <div className="w-3 h-3 rounded-full bg-red-500"></div>
          <span className="text-slate-600">{high}</span>
        </div>
      </div>
    </div>
  );
}

