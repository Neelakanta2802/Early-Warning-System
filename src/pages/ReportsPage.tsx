import { useEffect, useState } from 'react';
import { FileText, Download, RefreshCw, Loader2, AlertCircle } from 'lucide-react';
import apiClient from '../lib/api';

export default function ReportsPage() {
  const [reports, setReports] = useState<Array<{ id: string; title: string; description?: string; format?: string }>>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  const loadReports = async () => {
    setLoading(true);
    setError(null);
    try {
      const rows = (await apiClient.listReports()) as any[];
      const normalized = (rows || []).map((r: any) => ({
        id: String(r.id),
        title: String(r.title || r.id),
        description: r.description ? String(r.description) : undefined,
        format: r.format ? String(r.format) : 'csv',
      }));
      setReports(normalized);
    } catch (e: any) {
      console.error('Failed to load reports:', e);
      setReports([]);
      setError(e?.message || 'Failed to load reports');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadReports();
  }, []);

  const handleDownload = async (reportId: string) => {
    setDownloadingId(reportId);
    setError(null);
    try {
      const { blob, filename } = await apiClient.downloadReportCsv(reportId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (e: any) {
      console.error('Download failed:', e);
      setError(e?.message || 'Download failed');
    } finally {
      setDownloadingId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Reports & Insights</h1>
        <p className="text-slate-600 mt-1">
          Download real, up-to-date exports generated from your uploaded dataset
        </p>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <div className="p-6 border-b border-slate-200">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">Available Reports</h2>
            <button
              onClick={() => void loadReports()}
              disabled={loading}
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded border border-slate-200 text-slate-700 hover:bg-slate-50 disabled:opacity-60 disabled:cursor-not-allowed text-sm"
              title="Refresh"
            >
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
              Refresh
            </button>
          </div>
        </div>
        {error && (
          <div className="p-6 border-b border-slate-200 bg-red-50">
            <div className="flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-red-600 mt-0.5" />
              <div>
                <p className="font-semibold text-slate-900">Reports unavailable</p>
                <p className="text-sm text-slate-700 mt-1">{error}</p>
              </div>
            </div>
          </div>
        )}
        <div className="divide-y divide-slate-200">
          {loading ? (
            <div className="p-6 text-slate-500">Loading reports…</div>
          ) : reports.length === 0 ? (
            <div className="p-6 text-slate-500">No reports available.</div>
          ) : (
            reports.map((report) => (
              <div key={report.id} className="p-6 hover:bg-slate-50 transition-colors">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start space-x-4 min-w-0">
                    <div className="flex-shrink-0 h-12 w-12 bg-slate-100 rounded-lg flex items-center justify-center">
                      <FileText className="h-6 w-6 text-slate-600" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-3 mb-2">
                        <h3 className="font-semibold text-slate-900 truncate">{report.title}</h3>
                        <span className="px-2 py-1 text-xs font-medium bg-slate-100 text-slate-700 rounded">
                          {(report.format || 'csv').toUpperCase()}
                        </span>
                      </div>
                      {report.description && <p className="text-slate-600 text-sm">{report.description}</p>}
                      <p className="text-xs text-slate-500 mt-2">Export is generated from your current database state.</p>
                    </div>
                  </div>
                  <div className="flex items-center">
                    <button
                      onClick={() => void handleDownload(report.id)}
                      disabled={downloadingId === report.id}
                      className="flex items-center gap-2 px-4 py-2 bg-slate-900 text-white font-medium rounded-lg hover:bg-slate-800 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                    >
                      {downloadingId === report.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
                      <span>Download</span>
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="bg-gradient-to-br from-blue-50 to-slate-50 rounded-xl border border-blue-100 p-6">
        <p className="text-sm text-slate-700">
          Tip: If you uploaded a new dataset, the exports will reflect the new data immediately.
        </p>
      </div>
    </div>
  );
}
