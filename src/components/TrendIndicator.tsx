import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface TrendIndicatorProps {
  trend: 'up' | 'down' | 'stable';
  value?: string | number;
  className?: string;
}

export default function TrendIndicator({ trend, value, className = '' }: TrendIndicatorProps) {
  const config = {
    up: {
      icon: TrendingUp,
      color: 'text-red-600',
      bg: 'bg-red-50',
      label: 'Increasing',
    },
    down: {
      icon: TrendingDown,
      color: 'text-green-600',
      bg: 'bg-green-50',
      label: 'Decreasing',
    },
    stable: {
      icon: Minus,
      color: 'text-slate-600',
      bg: 'bg-slate-50',
      label: 'Stable',
    },
  };

  const style = config[trend];
  const Icon = style.icon;

  return (
    <div className={`inline-flex items-center space-x-1 ${style.color} ${className}`}>
      <Icon className="h-4 w-4" />
      {value !== undefined && <span className="text-sm font-medium">{value}</span>}
    </div>
  );
}

