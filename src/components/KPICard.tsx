import { LucideIcon } from 'lucide-react';
import TrendIndicator from './TrendIndicator';

interface KPICardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  iconColor?: string;
  iconBg?: string;
  trend?: 'up' | 'down' | 'stable';
  trendValue?: string;
  className?: string;
  onClick?: () => void;
}

export default function KPICard({
  title,
  value,
  subtitle,
  icon: Icon,
  iconColor = 'text-blue-600',
  iconBg = 'bg-blue-100',
  trend,
  trendValue,
  className = '',
  onClick,
}: KPICardProps) {
  return (
    <div
      className={`bg-white rounded-xl border border-slate-200 p-6 hover:shadow-md transition-all ${onClick ? 'cursor-pointer' : ''} ${className}`}
      onClick={onClick}
    >
      <div className="flex items-start justify-between mb-4">
        <div className={`h-12 w-12 ${iconBg} rounded-lg flex items-center justify-center`}>
          <Icon className={`h-6 w-6 ${iconColor}`} />
        </div>
        {trend && <TrendIndicator trend={trend} value={trendValue} />}
      </div>
      <div className="space-y-1">
        <p className="text-sm font-medium text-slate-600">{title}</p>
        <p className="text-3xl font-bold text-slate-900">{value}</p>
        {subtitle && <p className="text-sm text-slate-500">{subtitle}</p>}
      </div>
    </div>
  );
}

