import { useState } from 'react';
import { ArrowRight, CheckCircle2, ShieldCheck } from 'lucide-react';

export function LandingPage({
  onStart,
}: {
  onStart: () => void;
}) {
  const [isLoading, setIsLoading] = useState(false);

  const handleStart = async () => {
    setIsLoading(true);
    try {
      await onStart();
    } finally {
      // Keep loading state for a bit to show feedback
      setTimeout(() => setIsLoading(false), 500);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center font-sans">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 mx-auto mb-4" style={{ borderColor: '#00B521' }}></div>
          <p className="text-slate-600">Carregando...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      <header className="bg-white shadow-sm sticky top-0 z-50 w-full">
        <nav className="py-2 px-6 flex justify-between items-center max-w-6xl mx-auto w-full h-20">
          <div className="flex items-center gap-2 h-full">
            <img src="logo.jpeg" alt="Abrindo porteiras" className="h-full w-auto object-contain" />
          </div>
          <button
            onClick={handleStart}
            disabled={isLoading}
            className="text-sm font-medium text-slate-600 hover:text-primary-600 transition-colors disabled:opacity-50"
          >
            Entrar
          </button>
        </nav>
      </header>

      <main className="flex-1 flex flex-col items-center justify-center p-6 text-center max-w-4xl mx-auto mt-10">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary-100 text-primary-800 text-xs font-semibold mb-6">
          <ShieldCheck className="h-3 w-3" />
          MVP para Produtores Rurais
        </div>

        <h1 className="text-4xl md:text-5xl font-extrabold mb-6 leading-tight" style={{ color: '#00B521' }}>
          Venda para escolas e mercados <br className="hidden md:block" />
          sem medo da burocracia
        </h1>

        <p className="text-lg text-slate-600 mb-10 max-w-2xl mx-auto">
          Um assistente inteligente que organiza seus documentos, monta sua lista do que fazer e diz exatamente o que
          fazer para se regularizar.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 items-center">
          <button
            onClick={handleStart}
            disabled={isLoading}
            className="group text-white text-lg px-8 py-4 rounded-full font-bold transition-all flex items-center gap-3 shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
            style={{ backgroundColor: '#00B521', boxShadow: '0 10px 15px -3px rgba(0, 181, 33, 0.3)' }}
            onMouseEnter={(e) => !isLoading && (e.currentTarget.style.backgroundColor = '#00901a')}
            onMouseLeave={(e) => !isLoading && (e.currentTarget.style.backgroundColor = '#00B521')}
          >
            {isLoading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                <span>Carregando...</span>
              </>
            ) : (
              <>
                Começar Gratuitamente
                <ArrowRight className="h-5 w-5 group-hover:translate-x-1 transition-transform" />
              </>
            )}
          </button>
        </div>

        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8 w-full text-left">
          {[
            { title: 'Diagnóstico Rápido', desc: 'Responda perguntas simples e saiba seu status real.' },
            { title: 'Lista do que Fazer', desc: 'Nada de listas genéricas. Passos focados na sua produção.' },
            { title: 'Seus Auxílios Estão Seguros', desc: 'Fique tranquilo, você não corre risco de perder seus auxílios governamentais ao se regularizar.' },
          ].map((feat) => (
            <div
              key={feat.title}
              className="bg-white p-6 rounded-xl shadow-sm border border-slate-100 hover:border-primary-200 transition"
            >
              <CheckCircle2 className="text-primary-500 h-6 w-6 mb-3" />
              <h3 className="font-bold text-slate-800 mb-2">{feat.title}</h3>
              <p className="text-sm text-slate-500">{feat.desc}</p>
            </div>
          ))}
        </div>

        <p className="mt-12 text-xs text-slate-400 max-w-lg">
          Aviso: O Abrindo porteiras é uma ferramenta informativa. Não substituímos órgãos oficiais como MAPA,
          Vigilância Sanitária ou consultoria jurídica.
        </p>
      </main>
    </div>
  );
}
