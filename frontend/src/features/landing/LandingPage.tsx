import { ArrowRight, CheckCircle2, Leaf, Phone, ShieldCheck } from 'lucide-react';

export function LandingPage({
  onStart,
  onConsult,
}: {
  onStart: () => void;
  onConsult: () => void;
}) {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      <header className="bg-white shadow-sm sticky top-0 z-50 w-full">
        <nav className="p-6 flex justify-between items-center max-w-6xl mx-auto w-full">
          <div className="flex items-center gap-2">
            <Leaf className="text-green-600 h-6 w-6" />
            <span className="text-xl font-bold text-slate-800">CertificaFácil</span>
          </div>
          <button
            onClick={onStart}
            className="text-sm font-medium text-slate-600 hover:text-green-700 transition-colors"
          >
            Entrar
          </button>
        </nav>
      </header>

      <main className="flex-1 flex flex-col items-center justify-center p-6 text-center max-w-4xl mx-auto mt-10">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-green-100 text-green-800 text-xs font-semibold mb-6">
          <ShieldCheck className="h-3 w-3" />
          MVP para Produtores Rurais
        </div>

        <h1 className="text-4xl md:text-5xl font-extrabold text-slate-900 mb-6 leading-tight">
          Venda para escolas e mercados <br className="hidden md:block" />
          <span className="text-green-600">sem medo da burocracia</span>
        </h1>

        <p className="text-lg text-slate-600 mb-10 max-w-2xl mx-auto">
          Um assistente inteligente que organiza seus documentos, monta seu checklist e diz exatamente o que
          fazer para se regularizar.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 items-center">
          <button
            onClick={onStart}
            className="group bg-green-600 hover:bg-green-700 text-white text-lg px-8 py-4 rounded-full font-bold transition-all flex items-center gap-3 shadow-lg shadow-green-200"
          >
            Começar Gratuitamente
            <ArrowRight className="h-5 w-5 group-hover:translate-x-1 transition-transform" />
          </button>

          <button
            onClick={onConsult}
            className="group bg-white border-2 border-slate-200 hover:border-green-500 hover:text-green-600 text-slate-600 text-lg px-8 py-4 rounded-full font-bold transition-all flex items-center gap-3"
          >
            <Phone className="h-5 w-5 text-slate-400 group-hover:text-green-600" />
            Falar com especialista
          </button>
        </div>

        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8 w-full text-left">
          {[
            { title: 'Diagnóstico Rápido', desc: 'Responda perguntas simples e saiba seu status real.' },
            { title: 'Checklist Personalizado', desc: 'Nada de listas genéricas. Passos focados na sua produção.' },
            { title: 'Cofre de Documentos', desc: 'Guarde tudo em um lugar seguro e receba alertas de validade.' },
          ].map((feat) => (
            <div
              key={feat.title}
              className="bg-white p-6 rounded-xl shadow-sm border border-slate-100 hover:border-green-200 transition"
            >
              <CheckCircle2 className="text-green-500 h-6 w-6 mb-3" />
              <h3 className="font-bold text-slate-800 mb-2">{feat.title}</h3>
              <p className="text-sm text-slate-500">{feat.desc}</p>
            </div>
          ))}
        </div>

        <p className="mt-12 text-xs text-slate-400 max-w-lg">
          Aviso: O CertificaFácil é uma ferramenta informativa. Não substituímos órgãos oficiais como MAPA,
          Vigilância Sanitária ou consultoria jurídica.
        </p>
      </main>
    </div>
  );
}
