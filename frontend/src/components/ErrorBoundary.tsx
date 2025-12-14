/**
 * Error Boundary component for catching React errors
 */

import { Component, ReactNode } from 'react';
import { AlertTriangle } from 'lucide-react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6">
          <div className="max-w-md w-full bg-white rounded-xl shadow-lg p-8 border border-red-200">
            <div className="flex items-center gap-3 mb-4">
              <AlertTriangle className="h-6 w-6 text-red-600" />
              <h1 className="text-xl font-bold text-slate-800">Algo deu errado</h1>
            </div>
            <p className="text-slate-600 mb-6">
              Ocorreu um erro inesperado. Por favor, recarregue a página ou tente novamente mais tarde.
            </p>
            {this.state.error && (
              <details className="mb-4">
                <summary className="text-sm text-slate-500 cursor-pointer mb-2">Detalhes do erro</summary>
                <pre className="text-xs bg-slate-100 p-3 rounded overflow-auto text-slate-700">
                  {this.state.error.toString()}
                </pre>
              </details>
            )}
            <button
              onClick={() => window.location.reload()}
              className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-4 rounded-lg transition-colors"
            >
              Recarregar Página
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
