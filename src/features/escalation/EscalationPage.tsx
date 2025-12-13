import { useMemo, useState } from 'react';
import { ArrowRight, Search } from 'lucide-react';
import { MOCK_CONSULTANTS } from './consultants';

export function EscalationPage({ onBack }: { onBack: () => void }) {
  const [query, setQuery] = useState('');

  const consultants = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return MOCK_CONSULTANTS;
    return MOCK_CONSULTANTS.filter((c) => c.specialty.toLowerCase().includes(q) || c.role.toLowerCase().includes(q));
  }, [query]);

  return (
    <div className="min-h-screen bg-slate-50 font-sans p-6">
      <div className="max-w-3xl mx-auto">
        <button onClick={onBack} className="flex items-center text-slate-500 hover:text-slate-800 mb-6">
          <ArrowRight className="h-4 w-4 rotate-180 mr-1" /> Voltar
        </button>

        <header className="mb-8">
          <h1 className="text-3xl font-bold text-slate-800 mb-2">Ajuda Especializada</h1>
          <p className="text-slate-600">
            Seu caso possui detalhes técnicos que exigem um profissional. Selecionamos consultores baseados na sua
            região.
          </p>
        </header>

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="p-4 border-b border-slate-100 bg-slate-50 flex gap-2">
            <Search className="text-slate-400 h-5 w-5" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Filtrar por especialidade..."
              className="bg-transparent outline-none text-sm w-full"
            />
          </div>

          <div className="divide-y divide-slate-100">
            {consultants.map((cons) => (
              <div
                key={cons.id}
                className="p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 hover:bg-slate-50 transition"
              >
                <div>
                  <h3 className="font-bold text-slate-800">{cons.name}</h3>
                  <div className="flex items-center gap-2 text-sm text-slate-500 mt-1">
                    <span>{cons.role}</span>
                    <span>•</span>
                    <span>{cons.region}</span>
                  </div>
                  <div className="mt-2 inline-flex items-center px-2 py-1 rounded bg-blue-50 text-blue-700 text-xs font-semibold">
                    {cons.specialty}
                  </div>
                </div>
                <div className="flex flex-col items-end gap-2">
                  <span className="text-xs font-bold text-slate-400">Preço Estimado: {cons.price}</span>
                  <button className="bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-bold hover:bg-green-700 transition">
                    Contatar via WhatsApp
                  </button>
                </div>
              </div>
            ))}

            {consultants.length === 0 && (
              <div className="p-6 text-sm text-slate-500">Nenhum consultor encontrado para esse filtro.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
