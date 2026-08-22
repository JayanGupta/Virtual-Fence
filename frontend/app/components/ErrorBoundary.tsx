'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-[400px] flex-col items-center justify-center rounded-xl border border-slate-700/50 bg-slate-900/50 p-8 text-center">
          <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-neon-red/10">
            <svg className="h-8 w-8 text-neon-red" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h2 className="mb-2 text-lg font-bold text-slate-100">Component Error</h2>
          <p className="mb-6 max-w-md text-sm text-slate-400">
            The security console encountered an unexpected rendering error. Please refresh the page to restore functionality.
          </p>
          <button
            onClick={() => window.location.reload()}
            className="rounded-lg bg-slate-800 px-4 py-2 text-sm font-medium text-slate-300 transition hover:bg-slate-700 hover:text-white"
          >
            Reload Dashboard
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
