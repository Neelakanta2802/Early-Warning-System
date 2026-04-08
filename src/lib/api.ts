/**
 * Backend API client for Early Warning System
 * Connects frontend to FastAPI backend for ML features and advanced operations
 */

// Default to 8001 because the backend runs on 8001 in this workspace's smoke-tested setup.
// In production, set VITE_API_URL explicitly (e.g. http://localhost:8000).
const ENV_API_URL_RAW = import.meta.env.VITE_API_URL as string | undefined;

function normalizeBaseUrl(url: string): string {
  // Guard against common Windows/cmd env issues: trailing spaces, surrounding quotes, trailing slashes.
  let s = (url ?? '').trim();
  if (!s) return s;
  if ((s.startsWith('"') && s.endsWith('"')) || (s.startsWith("'") && s.endsWith("'"))) {
    s = s.slice(1, -1).trim();
  }
  // Remove trailing slashes to keep `${baseUrl}${endpoint}` predictable
  s = s.replace(/\/+$/, '');
  return s;
}

const ENV_API_URL = ENV_API_URL_RAW ? normalizeBaseUrl(ENV_API_URL_RAW) : undefined;

// Default to 8001 (fixed backend), but we will auto-detect at runtime to avoid
// "uploads work but predictions don't" when an older backend is still running on 8000.
const DEFAULT_API_CANDIDATES = [
  ENV_API_URL,
  // Prefer IPv4 loopback explicitly; on Windows "localhost" can resolve to ::1 (IPv6)
  // while uvicorn binds to 0.0.0.0 (IPv4) by default.
  'http://127.0.0.1:8006',
  'http://127.0.0.1:8005',
  'http://127.0.0.1:8003',
  'http://127.0.0.1:8002',
  'http://127.0.0.1:8001',
  'http://127.0.0.1:8000',
  'http://localhost:8006',
  'http://localhost:8005',
  'http://localhost:8003',
  'http://localhost:8002',
  'http://localhost:8001',
  'http://localhost:8000',
]
  .filter(Boolean)
  .map((u) => normalizeBaseUrl(String(u)))
  .filter(Boolean) as string[];

type DiagnosticsResponse = {
  code_version?: string;
  database?: { connected?: boolean };
};

function dedupe(arr: string[]) {
  return Array.from(new Set(arr));
}

function parseFixVersion(codeVersion?: string): number {
  // e.g. "2024-12-25-FIXED-V4" -> 4
  if (!codeVersion) return 0;
  const m = codeVersion.match(/FIXED-V(\d+)/i);
  return m ? Number(m[1]) : 0;
}

class ApiClient {
  private baseUrl: string;
  private resolvedBaseUrl: string | null = null;
  private candidates: string[];

  constructor(baseUrl?: string) {
    const initial = baseUrl ? [normalizeBaseUrl(baseUrl)] : DEFAULT_API_CANDIDATES;
    this.candidates = dedupe(initial.map((u) => normalizeBaseUrl(u)).filter(Boolean));
    // Keep baseUrl as a default, but we will resolve it before requests
    this.baseUrl = normalizeBaseUrl(this.candidates[0] || 'http://localhost:8003');
  }

  private async resolveBaseUrl(): Promise<string> {
    if (this.resolvedBaseUrl) return this.resolvedBaseUrl;

    // Probe candidates via /api/diagnostics (fast, and includes code_version)
    for (const candidate of this.candidates) {
      try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 1500);
        const res = await fetch(`${candidate}/api/diagnostics`, { signal: controller.signal });
        clearTimeout(timeout);
        if (!res.ok) continue;
        const diag = (await res.json()) as DiagnosticsResponse;
        const v = parseFixVersion(diag.code_version);
        const dbOk = diag.database?.connected === true;
        // Prefer FIXED-V4+ with DB connected
        if (dbOk && v >= 4) {
          this.resolvedBaseUrl = candidate;
          this.baseUrl = candidate;
          return candidate;
        }
      } catch {
        // ignore and try next candidate
      }
    }

    // Fallback: first reachable /api/health
    for (const candidate of this.candidates) {
      try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 1500);
        const res = await fetch(`${candidate}/api/health`, { signal: controller.signal });
        clearTimeout(timeout);
        if (res.ok) {
          this.resolvedBaseUrl = candidate;
          this.baseUrl = candidate;
          return candidate;
        }
      } catch {
        // ignore
      }
    }

    // Last resort
    this.resolvedBaseUrl = this.baseUrl;
    return this.baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const baseUrl = await this.resolveBaseUrl();
    const url = `${normalizeBaseUrl(baseUrl)}${endpoint}`;
    
    const config: RequestInit = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(error.detail || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  private async fetchRaw(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<Response> {
    const baseUrl = await this.resolveBaseUrl();
    const url = `${normalizeBaseUrl(baseUrl)}${endpoint}`;

    try {
      const response = await fetch(url, options);
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(error.detail || `HTTP error! status: ${response.status}`);
      }
      return response;
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  // Student endpoints
  async getStudents(params?: {
    department?: string;
    semester?: string;
    status?: string;
    limit?: number;
    offset?: number;
  }) {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          queryParams.append(key, value.toString());
        }
      });
    }
    const query = queryParams.toString();
    return this.request(`/api/students${query ? `?${query}` : ''}`);
  }

  async getStudent(studentId: string) {
    return this.request(`/api/students/${studentId}`);
  }

  async createStudent(studentData: {
    student_id: string;
    full_name: string;
    email?: string;
    department?: string;
    program?: string;
    year_level?: number;
    semester?: string;
    enrollment_date?: string;
    status?: string;
  }) {
    return this.request('/api/students', {
      method: 'POST',
      body: JSON.stringify(studentData),
    });
  }

  async uploadStudentData(
    file: File,
    studentName?: string,
    rollNumber?: string
  ) {
    if (!file) {
      throw new Error('No file provided');
    }

    const formData = new FormData();
    formData.append('file', file);
    if (studentName) formData.append('student_name', studentName);
    if (rollNumber) formData.append('roll_number', rollNumber);

    const baseUrl = await this.resolveBaseUrl();
    const url = `${baseUrl}/api/upload`;
    
    console.log('Uploading file:', {
      filename: file.name,
      size: file.size,
      type: file.type,
      url: url,
      baseUrl: this.baseUrl
    });
    
    try {
      // First check if backend is accessible
      try {
        const healthCheck = await fetch(`${baseUrl}/api/health`, { method: 'GET' });
        if (!healthCheck.ok) {
          throw new Error(`Backend health check failed. Status: ${healthCheck.status}`);
        }
      } catch (healthError: any) {
        console.error('Backend health check failed:', healthError);
        throw new Error(`Cannot connect to backend at ${baseUrl}. Please ensure the backend server is running.`);
      }
      
      const response = await fetch(url, {
        method: 'POST',
        body: formData,
        // Don't set Content-Type header - let browser set it with boundary
      });

      console.log('Upload response:', {
        status: response.status,
        statusText: response.statusText,
        ok: response.ok,
        headers: Object.fromEntries(response.headers.entries())
      });

      if (!response.ok) {
        let errorDetail = `HTTP error! status: ${response.status}`;
        
        // Handle different error scenarios
        if (response.status === 404) {
          errorDetail = `Endpoint not found at ${url}. Please check if backend is running and the endpoint is registered.`;
        } else if (response.status === 413) {
          errorDetail = 'File too large. Please try a smaller file.';
        } else if (response.status === 415) {
          errorDetail = 'Unsupported media type. Please check the file format.';
        } else {
          try {
            // Try to get error message from response body
            const contentType = response.headers.get('content-type') || '';
            if (contentType.includes('application/json')) {
              const error = await response.json();
              errorDetail = error.detail || error.message || errorDetail;
            } else {
              // Try to read as text
              const text = await response.text();
              if (text && text.trim()) {
                // Try to parse as JSON if it looks like JSON
                try {
                  const jsonError = JSON.parse(text);
                  errorDetail = jsonError.detail || jsonError.message || text;
                } catch {
                  errorDetail = text;
                }
              } else {
                errorDetail = response.statusText || errorDetail;
              }
            }
          } catch {
            // If response is not JSON/text, use status text
            errorDetail = response.statusText || `HTTP ${response.status}: ${response.statusText || 'Unknown error'}`;
          }
        }
        
        console.error('Upload failed:', {
          status: response.status,
          statusText: response.statusText,
          url: url,
          errorDetail: errorDetail
        });
        
        throw new Error(errorDetail);
      }

      const result = await response.json();
      console.log('Upload successful:', result);
      return result;
    } catch (error: any) {
      console.error('Upload error:', error);
      
      // Handle network errors
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        throw new Error(`Network error: Cannot connect to backend at ${this.baseUrl}. Please ensure the backend server is running.`);
      }
      
      if (error.message) {
        throw error;
      }
      throw new Error(`Failed to upload file: ${error.message || 'Unknown error'}`);
    }
  }

  async getStudentRisk(studentId: string, options?: {
    recalculate?: boolean;
    include_trend?: boolean;
    include_explanation?: boolean;
  }) {
    const params = new URLSearchParams();
    if (options?.recalculate) params.append('recalculate', 'true');
    if (options?.include_trend !== false) params.append('include_trend', 'true');
    if (options?.include_explanation !== false) params.append('include_explanation', 'true');
    
    const query = params.toString();
    return this.request(`/api/students/${studentId}/risk${query ? `?${query}` : ''}`);
  }

  // Reports
  async listReports() {
    return this.request('/api/reports');
  }

  async downloadReportCsv(reportId: string, limit: number = 5000): Promise<{ blob: Blob; filename: string }> {
    const qp = new URLSearchParams({ limit: String(limit) });
    const res = await this.fetchRaw(`/api/reports/${encodeURIComponent(reportId)}/csv?${qp.toString()}`, {
      method: 'GET',
      headers: {
        Accept: 'text/csv',
      },
    });
    const blob = await res.blob();
    const cd = res.headers.get('Content-Disposition') || '';
    const m = cd.match(/filename="?([^";]+)"?/i);
    const filename = (m && m[1]) ? m[1] : `${reportId}.csv`;
    return { blob, filename };
  }

  async evaluateStudent(studentId: string) {
    return this.request(`/api/students/${studentId}/evaluate`, {
      method: 'POST',
    });
  }

  async getStudentTrend(studentId: string, lookbackDays: number = 90) {
    return this.request(`/api/students/${studentId}/trend?lookback_days=${lookbackDays}`);
  }

  // Alerts endpoints
  async getAlerts(params?: {
    student_id?: string;
    acknowledged?: boolean;
    severity?: string;
    limit?: number;
  }) {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          queryParams.append(key, value.toString());
        }
      });
    }
    const query = queryParams.toString();
    return this.request(`/api/alerts${query ? `?${query}` : ''}`);
  }

  async acknowledgeAlert(alertId: string, acknowledgedBy: string) {
    return this.request(`/api/alerts/${alertId}/acknowledge`, {
      method: 'POST',
      body: JSON.stringify({ acknowledged_by: acknowledgedBy }),
    });
  }

  // Interventions endpoints
  async getInterventions(params?: {
    student_id?: string;
    status?: string;
    assigned_to?: string;
  }) {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          queryParams.append(key, value.toString());
        }
      });
    }
    const query = queryParams.toString();
    return this.request(`/api/interventions${query ? `?${query}` : ''}`);
  }

  async createIntervention(intervention: {
    student_id: string;
    assigned_to?: string;
    intervention_type: string;
    description: string;
    status?: string;
  }) {
    return this.request('/api/interventions', {
      method: 'POST',
      body: JSON.stringify(intervention),
    });
  }

  async updateIntervention(interventionId: string, updates: any) {
    return this.request(`/api/interventions/${interventionId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async deleteIntervention(interventionId: string) {
    return this.request(`/api/interventions/${interventionId}`, {
      method: 'DELETE',
    });
  }

  // Analytics endpoints
  async getAnalyticsOverview(params?: {
    department?: string;
    semester?: string;
  }) {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          queryParams.append(key, value);
        }
      });
    }
    const query = queryParams.toString();
    return this.request(`/api/analytics/overview${query ? `?${query}` : ''}`);
  }

  async getRiskTrends(params?: {
    days?: number;
    department?: string;
  }) {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          queryParams.append(key, value.toString());
        }
      });
    }
    const query = queryParams.toString();
    return this.request(`/api/analytics/trends${query ? `?${query}` : ''}`);
  }

  async getDepartmentAnalytics() {
    return this.request('/api/analytics/departments');
  }

  async getCourseAnalytics(semester?: string) {
    const query = semester ? `?semester=${semester}` : '';
    return this.request(`/api/analytics/courses${query}`);
  }

  // ML endpoints
  async trainModel(params?: {
    model_type?: string;
    use_mock_labels?: boolean;
    test_size?: number;
  }) {
    return this.request('/api/ml/train', {
      method: 'POST',
      body: JSON.stringify(params || {}),
    });
  }

  async getModelInfo() {
    return this.request('/api/ml/model/info');
  }

  async getFeatureImportance() {
    return this.request('/api/ml/features/importance');
  }

  async evaluateModel() {
    return this.request('/api/ml/evaluate', {
      method: 'POST',
    });
  }

  async checkRetraining() {
    return this.request('/api/ml/model/retrain-check');
  }

  async retrainModel(params?: {
    model_type?: string;
    use_mock_labels?: boolean;
  }) {
    return this.request('/api/ml/model/retrain', {
      method: 'POST',
      body: JSON.stringify(params || {}),
    });
  }

  async getModelVersions() {
    return this.request('/api/ml/model/versions');
  }

  async getModelPerformance() {
    return this.request('/api/ml/model/performance');
  }

  async checkDataDrift() {
    return this.request('/api/ml/model/drift');
  }

  // Health check
  async healthCheck() {
    return this.request('/api/health');
  }

  // Admin / maintenance
  async clearAllData() {
    return this.request('/api/admin/clear-data', { method: 'POST' });
  }

  // Upload history / apply / delete
  async listUploads(limit: number = 50) {
    return this.request(`/api/uploads?limit=${limit}`);
  }

  async applyUpload(uploadId: string) {
    return this.request(`/api/uploads/${encodeURIComponent(uploadId)}/apply`, { method: 'POST' });
  }

  async deleteUpload(uploadId: string) {
    return this.request(`/api/uploads/${encodeURIComponent(uploadId)}`, { method: 'DELETE' });
  }
}

// If VITE_API_URL is set, lock the frontend to that backend (prevents accidentally
// talking to an old backend/old database on a different port).
export const apiClient = new ApiClient(ENV_API_URL);
export default apiClient;
