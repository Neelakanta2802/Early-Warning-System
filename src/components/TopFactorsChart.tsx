import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface Factor {
  name: string;
  weight: number;
  value: number;
  impact: string;
}

interface TopFactorsChartProps {
  factors: Factor[];
  maxDisplay?: number;
}

export default function TopFactorsChart({ factors, maxDisplay = 5 }: TopFactorsChartProps) {
  if (!factors || factors.length === 0) {
    return (
      <div className="text-center py-8 text-slate-500">
        <p className="text-sm">No risk factors available</p>
      </div>
    );
  }

  const safeNum = (v: any): number => {
    const n = Number(v);
    return Number.isFinite(n) ? n : 0;
  };
  const safeStr = (v: any): string => (v === null || v === undefined ? '' : String(v));

  const sortedFactors = [...factors]
    .map((f: any) => ({
      ...f,
      name: safeStr(f?.name) || 'unknown',
      weight: safeNum(f?.weight),
      value: safeNum(f?.value),
      impact: safeStr(f?.impact),
    }))
    .sort((a, b) => Math.abs(b.weight) - Math.abs(a.weight))
    .slice(0, maxDisplay);

  const maxWeight = Math.max(...sortedFactors.map(f => Math.abs(f.weight)), 1);

  const getImpactIcon = (weight: number) => {
    if (weight > 0) return <TrendingUp className="h-4 w-4 text-red-600" />;
    if (weight < 0) return <TrendingDown className="h-4 w-4 text-green-600" />;
    return <Minus className="h-4 w-4 text-slate-400" />;
  };

  const getImpactColor = (weight: number) => {
    if (weight > 0) return 'bg-red-500';
    if (weight < 0) return 'bg-green-500';
    return 'bg-slate-400';
  };

  const formatFactorName = (name: string) => {
    return name
      .replace(/_/g, ' ')
      .replace(/\b\w/g, l => l.toUpperCase());
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-slate-900">Top Contributing Factors</h3>
        <span className="text-xs text-slate-500">Sorted by impact</span>
      </div>
      {sortedFactors.map((factor, index) => {
        const weightPercent = (Math.abs(factor.weight) / maxWeight) * 100;
        const isPositive = factor.weight > 0;

        return (
          <div key={index} className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 flex-1 min-w-0">
                {getImpactIcon(factor.weight)}
                <span className="text-sm font-medium text-slate-900 truncate">
                  {formatFactorName(factor.name)}
                </span>
              </div>
              <div className="flex items-center space-x-2 ml-2">
                <span className={`text-xs font-semibold ${
                  isPositive ? 'text-red-600' : 'text-green-600'
                }`}>
                  {factor.weight > 0 ? '+' : ''}{factor.weight.toFixed(2)}
                </span>
              </div>
            </div>
            <div className="relative h-2 bg-slate-200 rounded-full overflow-hidden">
              <div
                className={`h-full ${getImpactColor(factor.weight)} transition-all duration-500 rounded-full`}
                style={{ width: `${weightPercent}%` }}
              />
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-600">Value: {factor.value.toFixed(2)}</span>
              {factor.impact && (
                <span className="text-slate-500 italic">{factor.impact}</span>
              )}
            </div>
          </div>
        );
      })}
      {factors.length > maxDisplay && (
        <p className="text-xs text-slate-500 text-center pt-2">
          +{factors.length - maxDisplay} more factors
        </p>
      )}
    </div>
  );
}
