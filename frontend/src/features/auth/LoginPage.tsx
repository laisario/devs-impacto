import { useState } from 'react';
import { ArrowLeft, Leaf, CreditCard } from 'lucide-react';
import { login as apiLogin } from '../../services/api/auth';
import { ApiClientError } from '../../services/api/client';
import { useAuth } from '../../contexts/AuthContext';

interface LoginPageProps {
  onLogin: () => void;
  onBack: () => void;
}

export function LoginPage({ onLogin, onBack }: LoginPageProps) {
  const [cpf, setCpf] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const { login: authLogin } = useAuth();

  const formatCpf = (value: string): string => {
    // Remove all non-digit characters
    const digits = value.replace(/\D/g, '');
    // Limit to 11 digits
    const limited = digits.slice(0, 11);
    // Format: XXX.XXX.XXX-XX
    if (limited.length <= 3) {
      return limited;
    } else if (limited.length <= 6) {
      return `${limited.slice(0, 3)}.${limited.slice(3)}`;
    } else if (limited.length <= 9) {
      return `${limited.slice(0, 3)}.${limited.slice(3, 6)}.${limited.slice(6)}`;
    } else {
      return `${limited.slice(0, 3)}.${limited.slice(3, 6)}.${limited.slice(6, 9)}-${limited.slice(9, 11)}`;
    }
  };

  const handleCpfChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const formatted = formatCpf(e.target.value);
    setCpf(formatted);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const response = await apiLogin({ cpf });
      // Update auth context with the token and wait for it to complete
      await authLogin(response.access_token);
      // Call the onLogin callback to trigger navigation
      // onLogin will handle waiting for auth state
      onLogin();
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message || 'Erro ao fazer login. Tente novamente.');
      } else {
        setError('Erro ao fazer login. Tente novamente.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      <header className="bg-white shadow-sm sticky top-0 z-50 w-full">
        <nav className="p-6 flex justify-between items-center max-w-6xl mx-auto w-full">
          <button
            onClick={onBack}
            className="flex items-center gap-2 text-slate-600 hover:text-green-700 transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
            <span className="text-sm font-medium">Voltar</span>
          </button>
          <div className="flex items-center gap-2">
            <Leaf className="text-primary-500 h-6 w-6" />
            <span className="text-xl font-bold text-primary-500">Abrindo porteiras</span>
          </div>
          <div className="w-24"></div>
        </nav>
      </header>

      <main className="flex-1 flex flex-col items-center justify-center p-6">
        <div className="w-full max-w-md">
          <div className="bg-white rounded-2xl shadow-lg p-8 border border-slate-100">
            <h1 className="text-3xl font-bold text-primary-500 mb-2">Bem-vindo</h1>
            <p className="text-slate-600 mb-8">Digite seu CPF para continuar</p>

            {error && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label htmlFor="cpf" className="block text-sm font-medium text-slate-700 mb-2">
                  CPF
                </label>
                <div className="relative">
                  <CreditCard className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
                  <input
                    id="cpf"
                    type="text"
                    value={cpf}
                    onChange={handleCpfChange}
                    placeholder="000.000.000-00"
                    maxLength={14}
                    className="w-full pl-10 pr-4 py-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    disabled={isLoading}
                  />
                </div>
                <p className="mt-2 text-xs text-slate-500">
                  Seu CPF será validado automaticamente
                </p>
              </div>

              <button
                type="submit"
                disabled={isLoading || cpf.replace(/\D/g, '').length !== 11}
                className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {isLoading ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    <span>Validando...</span>
                  </>
                ) : (
                  'Entrar'
                )}
              </button>
            </form>
          </div>
        </div>
      </main>
    </div>
  );
}

