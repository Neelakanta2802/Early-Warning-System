import { AlertTriangle, Clock } from 'lucide-react';
import RiskBadge from './RiskBadge';
import type { RiskLevel } from '../types/database';

interface EarlyWarningCardProps {
  studentId?: string;
  studentName: string;
  studentIdNumber: string;
  riskLevel: RiskLevel;
  riskScore: number;
  detectedAt: string;
  reason: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  onClick?: () => void;
}

export default function EarlyWarningCard({
  studentName,
  studentIdNumber,
  riskLevel,
  riskScore,
  detectedAt,
  reason,
  severity,
  onClick,
}: EarlyWarningCardProps) {
  const severityColors = {
    critical: 'border-red-300 bg-red-50',
    high: 'border-red-200 bg-red-50',
    medium: 'border-amber-200 bg-amber-50',
    low: 'border-blue-200 bg-blue-50',
  };

  const getTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return '1 day ago';
    if (diffDays < 7) return `${diffDays} days ago`;
    return date.toLocaleDateString();
  };

  return (
    <div
      className={`border rounded-xl p-4 hover:shadow-md transition-all ${onClick ? 'cursor-pointer' : ''} ${severityColors[severity]}`}
      onClick={onClick}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-start space-x-3 flex-1">
          <div className="flex-shrink-0 mt-1">
            <AlertTriangle className={`h-5 w-5 ${
              severity === 'critical' || severity === 'high' ? 'text-red-600' : 'text-amber-600'
            }`} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center space-x-2 mb-1">
              <h4 className="font-semibold text-slate-900 truncate">{studentName}</h4>
              <RiskBadge riskLevel={riskLevel} size="sm" />
            </div>
            <p className="text-sm text-slate-600 mb-2">{studentIdNumber}</p>
            <p className="text-sm text-slate-700 font-medium">{reason}</p>
          </div>
        </div>
      </div>
      <div className="flex items-center justify-between text-xs text-slate-500">
        <div className="flex items-center space-x-1">
          <Clock className="h-3 w-3" />
          <span>Detected {getTimeAgo(detectedAt)}</span>
        </div>
        <span className="font-medium">Risk Score: {riskScore}/100</span>
      </div>
    </div>
  );
}

