import type { RiskLevel } from '../types/database';

interface RiskBadgeProps {
  riskLevel: RiskLevel | 'none';
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  className?: string;
}

export default function RiskBadge({ riskLevel, size = 'md', showLabel = true, className = '' }: RiskBadgeProps) {
  const config = {
    low: {
      bg: 'bg-green-100',
      text: 'text-green-700',
      border: 'border-green-300',
      label: 'Low Risk',
      icon: '✓',
    },
    medium: {
      bg: 'bg-amber-100',
      text: 'text-amber-700',
      border: 'border-amber-300',
      label: 'Medium Risk',
      icon: '⚠',
    },
    high: {
      bg: 'bg-red-100',
      text: 'text-red-700',
      border: 'border-red-300',
      label: 'High Risk',
      icon: '🚨',
    },
    none: {
      bg: 'bg-slate-100',
      text: 'text-slate-600',
      border: 'border-slate-300',
      label: 'No Data',
      icon: '—',
    },
  };

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-3 py-1 text-sm',
    lg: 'px-4 py-2 text-base',
  };

  const style = config[riskLevel] || config.none;

  return (
    <span
      className={`inline-flex items-center space-x-1.5 font-semibold rounded-lg border ${style.bg} ${style.text} ${style.border} ${sizeClasses[size]} ${className}`}
    >
      <span>{style.icon}</span>
      {showLabel && <span>{style.label}</span>}
    </span>
  );
}

