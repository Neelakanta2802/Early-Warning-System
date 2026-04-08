import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface RiskDataPoint {
  date: string;
  risk_score: number;
  risk_level: 'low' | 'medium' | 'high';
}

interface RiskTrendChartProps {
  data: RiskDataPoint[];
  height?: number;
}

export default function RiskTrendChart({ data }: RiskTrendChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-slate-500">
        <p className="text-sm">No trend data available</p>
      </div>
    );
  }

  const safeDate = (v: any): Date | null => {
    try {
      const d = new Date(v);
      return Number.isFinite(d.getTime()) ? d : null;
    } catch {
      return null;
    }
  };

  const safeScore = (v: any): number => {
    const n = Number(v);
    return Number.isFinite(n) ? n : 0;
  };

  const safeLevel = (v: any): 'low' | 'medium' | 'high' => {
    const s = String(v || '').toLowerCase();
    if (s === 'high' || s === 'medium' || s === 'low') return s as any;
    return 'low';
  };

  const cleaned = (data || [])
    .map((p: any) => {
      const d = safeDate(p?.date);
      return d
        ? {
            date: d.toISOString(),
            risk_score: safeScore(p?.risk_score),
            risk_level: safeLevel(p?.risk_level),
          }
        : null;
    })
    .filter(Boolean) as RiskDataPoint[];

  if (cleaned.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-slate-500">
        <p className="text-sm">No trend data available</p>
      </div>
    );
  }

  if (cleaned.length === 1) {
    return (
      <div className="flex items-center justify-center h-48 text-slate-500">
        <p className="text-sm">Insufficient data for trend analysis (need at least 2 data points)</p>
      </div>
    );
  }

  if (data.length === 1) {
    return (
      <div className="flex items-center justify-center h-48 text-slate-500">
        <p className="text-sm">Insufficient data for trend analysis (need at least 2 data points)</p>
      </div>
    );
  }

  // Sort by date
  const sortedData = [...cleaned].sort((a, b) => 
    new Date(a.date).getTime() - new Date(b.date).getTime()
  );

  const maxScore = Math.max(...sortedData.map(d => safeScore(d.risk_score)), 100);
  const minScore = Math.min(...sortedData.map(d => safeScore(d.risk_score)), 0);
  const scoreRange = maxScore - minScore || 100;

  // Calculate trend
  const firstScore = safeScore(sortedData[0].risk_score);
  const lastScore = safeScore(sortedData[sortedData.length - 1].risk_score);
  const trend = lastScore - firstScore;
  const trendPercent = firstScore > 0 ? ((trend / firstScore) * 100).toFixed(1) : '0.0';

  const getTrendIcon = () => {
    if (trend > 5) return <TrendingUp className="h-4 w-4 text-red-600" />;
    if (trend < -5) return <TrendingDown className="h-4 w-4 text-green-600" />;
    return <Minus className="h-4 w-4 text-slate-400" />;
  };

  const getTrendColor = () => {
    if (trend > 5) return 'text-red-600';
    if (trend < -5) return 'text-green-600';
    return 'text-slate-600';
  };

  const getRiskColor = (level: string) => {
    if (level === 'high') return '#ef4444';
    if (level === 'medium') return '#f59e0b';
    return '#10b981';
  };

  // Format date for display
  const formatDate = (dateString: string) => {
    const d = safeDate(dateString);
    return d ? d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : '—';
  };

  return (
    <div className="space-y-4">
      <div className="h-48 flex items-end justify-between space-x-1">
        {sortedData.map((point, index) => {
          const normalizedScore = ((safeScore(point.risk_score) - minScore) / scoreRange) * 100;
          const barHeight = Math.max(normalizedScore, 5); // Minimum 5% height for visibility

          return (
            <div key={index} className="flex-1 flex flex-col items-center group relative">
              <div
                className="w-full rounded-t transition-all duration-300 hover:opacity-80 cursor-pointer"
                style={{ 
                  height: `${barHeight}%`,
                  backgroundColor: getRiskColor(point.risk_level)
                }}
                title={`${formatDate(point.date)}: ${point.risk_score}/100 (${point.risk_level})`}
              />
              <span className="text-xs text-slate-500 mt-2">{formatDate(point.date)}</span>
              
              {/* Tooltip on hover */}
              <div className="absolute bottom-full mb-2 hidden group-hover:block z-10 bg-slate-900 text-white text-xs rounded px-2 py-1 whitespace-nowrap">
                <div className="font-semibold">{point.risk_score}/100</div>
                <div className="text-slate-300 capitalize">{point.risk_level} risk</div>
                <div className="text-slate-400">{formatDate(point.date)}</div>
                <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 translate-y-full w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-slate-900"></div>
              </div>
            </div>
          );
        })}
      </div>
      
      <div className="pt-4 border-t border-slate-200">
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center space-x-2">
            <span className="text-slate-600">Trend:</span>
            {getTrendIcon()}
            <span className={`font-semibold ${getTrendColor()}`}>
              {trend > 0 ? '+' : ''}{trend.toFixed(1)} points
            </span>
            <span className="text-slate-500">
              ({trendPercent}%)
            </span>
          </div>
          <div className="text-slate-500 text-xs">
            {sortedData.length} assessment{sortedData.length !== 1 ? 's' : ''}
          </div>
        </div>
      </div>
    </div>
  );
}
