interface ConfidenceIndicatorProps {
  confidence: number; // 0-1
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

export default function ConfidenceIndicator({ 
  confidence, 
  size = 'md',
  showLabel = true 
}: ConfidenceIndicatorProps) {
  const sizeClasses = {
    sm: 'h-2 w-16',
    md: 'h-3 w-24',
    lg: 'h-4 w-32'
  };

  const textSizes = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base'
  };

  const getConfidenceColor = (conf: number) => {
    if (conf >= 0.8) return 'bg-green-500';
    if (conf >= 0.6) return 'bg-amber-500';
    return 'bg-red-500';
  };

  const getConfidenceLabel = (conf: number) => {
    if (conf >= 0.9) return 'Very High';
    if (conf >= 0.8) return 'High';
    if (conf >= 0.6) return 'Moderate';
    if (conf >= 0.4) return 'Low';
    return 'Very Low';
  };

  const percentage = (confidence * 100).toFixed(0);

  return (
    <div className="flex items-center space-x-2">
      <div className={`relative ${sizeClasses[size]} bg-slate-200 rounded-full overflow-hidden`}>
        <div
          className={`h-full ${getConfidenceColor(confidence)} transition-all duration-500 rounded-full`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      {showLabel && (
        <div className="flex items-center space-x-1">
          <span className={`${textSizes[size]} font-medium text-slate-700`}>
            {percentage}%
          </span>
          <span className={`${textSizes[size]} text-slate-500`}>
            ({getConfidenceLabel(confidence)})
          </span>
        </div>
      )}
    </div>
  );
}
