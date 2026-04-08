import React from 'react';

type Props = {
  children: React.ReactNode;
};

type State = {
  hasError: boolean;
  message?: string;
};

export default class ErrorBoundary extends React.Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(error: unknown): State {
    return {
      hasError: true,
      message: error instanceof Error ? error.message : String(error),
    };
  }

  componentDidCatch(error: unknown, info: unknown) {
    // Keep this minimal; no PII.
    console.error('UI crash captured by ErrorBoundary:', error, info);
  }

  render() {
    if (this.state.hasError) {
      // Only shown when something crashes; does not change normal UI.
      return (
        <div className="min-h-[60vh] flex items-center justify-center">
          <div className="bg-white border border-red-200 rounded-xl p-6 max-w-lg w-full">
            <h2 className="text-lg font-semibold text-slate-900">Something went wrong</h2>
            <p className="text-sm text-slate-600 mt-2">
              Please refresh the page. If this keeps happening, re-upload your dataset and try again.
            </p>
            {this.state.message && (
              <div className="mt-4 text-xs bg-slate-50 border border-slate-200 rounded p-3 text-slate-700 overflow-auto">
                {this.state.message}
              </div>
            )}
            <div className="mt-4 flex gap-2">
              <button
                className="px-4 py-2 bg-slate-900 text-white rounded-lg text-sm hover:bg-slate-800"
                onClick={() => window.location.reload()}
              >
                Refresh
              </button>
              <button
                className="px-4 py-2 bg-slate-100 text-slate-900 rounded-lg text-sm hover:bg-slate-200"
                onClick={() => this.setState({ hasError: false, message: undefined })}
              >
                Try to continue
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

