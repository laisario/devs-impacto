import React, { useState, useEffect, useRef } from 'react';
import { 
  CheckCircle2, 
  AlertTriangle, 
  FileText, 
  Upload, 
  MessageSquare, 
  ChevronRight, 
  ShieldCheck, 
  Leaf, 
  User, 
  ArrowRight,
  Search,
  X,
  ChevronLeft,
  Info,
  Mic,
  Send,
  Play,
  Square,
  Eye,
  HelpCircle,
  Lightbulb,
  Phone
} from 'lucide-react';

// --- Tipos e Interfaces ---

type ViewState = 'landing' | 'onboarding' | 'dashboard' | 'escalation';
type CaseStatus = 'not_ready' | 'in_progress' | 'ready';
type DocStatus = 'missing' | 'uploaded' | 'ai_reviewed' | 'accepted';

interface ChecklistStep {
  text: string;
  helpContent?: {
    type: 'tip'; // Simplificado para apenas dicas de texto
    title: string;
    description: string;
  };
}

interface ChecklistItem {
  id: string;
  title: string;
  description: string;
  priority: 'high' | 'medium' | 'low';
  status: 'todo' | 'doing' | 'done';
  detailedSteps?: ChecklistStep[]; 
  relatedDocId?: string;    
}

interface Document {
  id: string;
  type: string;
  name: string;
  status: DocStatus;
  aiNotes?: string;
}

interface UserProfile {
  name: string;
  producerType: string;
  city: string;
  answers: Record<string, string>;
  riskFlags: string[];
  caseType: 'in_natura' | 'needs_human';
}

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  audioPlaying?: boolean;
}

// --- Dados Mockados e Lógica de Negócios Simulada ---

const MOCK_CONSULTANTS = [
  { id: 1, name: 'Ana Silva', role: 'Eng. de Alimentos', region: 'Sul', specialty: 'Processamento e Rotulagem', price: '$$' },
  { id: 2, name: 'Carlos Rural', role: 'Técnico Agrícola', region: 'Nordeste', specialty: 'CAF e DAP', price: '$' },
  { id: 3, name: 'Regulariza Agro', role: 'Consultoria', region: 'Sudeste', specialty: 'MAPA e SIF', price: '$$$' },
];

const ONBOARDING_QUESTIONS = [
  { 
    key: 'name', 
    text: 'Olá! Vamos começar. Qual é o seu nome completo?', 
    type: 'text',
    placeholder: 'Ex: João da Silva'
  },
  { 
    key: 'tipo_alimento', 
    text: 'Prazer! O que você produz principalmente?', 
    type: 'choice',
    options: ['Frutas', 'Verduras/Legumes', 'Processados (Geleias, Conservas)', 'Origem Animal (Mel, Ovos, Queijo)'] 
  },
  { 
    key: 'processa_alimento', 
    text: 'Você processa o alimento (corta, cozinha, embala a vácuo) antes de vender?', 
    type: 'choice',
    options: ['Não, vendo in natura (como colhido)', 'Sim, faço algum processamento'] 
  },
  { 
    key: 'publico_alvo', 
    text: 'Para quem você pretende vender?', 
    type: 'choice',
    options: ['Escola Pública (PNAE)', 'Mercados/Escolas Privadas', 'Ambas'] 
  },
  { 
    key: 'documentacao_base', 
    text: 'Como está sua documentação básica (CAF/DAP)?', 
    type: 'choice',
    options: ['Tenho ativa', 'Não tenho', 'Preciso renovar'] 
  },
  { 
    key: 'municipio', 
    text: 'Qual seu município e estado?', 
    type: 'text',
    placeholder: 'Ex: Bauru - SP'
  }
];

// --- Componentes ---

export default function CertificaFacilApp() {
  const [view, setView] = useState<ViewState>('landing');
  const [user, setUser] = useState<UserProfile | null>(null);
  const [checklist, setChecklist] = useState<ChecklistItem[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);

  // --- Lógica do Motor de Decisão (Simulando Backend/IA) ---
  const generatePlan = (answers: Record<string, string>) => {
    setLoading(true);
    
    setTimeout(() => {
      const riskFlags = [];
      let caseType: 'in_natura' | 'needs_human' = 'in_natura';

      // Regras de Negócio
      if (answers.processa_alimento?.includes('Sim') || answers.tipo_alimento?.includes('Processados')) {
        riskFlags.push('Processamento Detectado');
        caseType = 'needs_human';
      }
      if (answers.tipo_alimento?.includes('Animal')) {
        riskFlags.push('Origem Animal');
        caseType = 'needs_human';
      }

      // Gerar Docs iniciais
      const initialDocs: Document[] = [
        { id: 'd1', type: 'identidade', name: 'RG/CPF', status: 'missing' },
        { id: 'd2', type: 'caf', name: 'CAF/DAP', status: answers.documentacao_base === 'Tenho ativa' ? 'uploaded' : 'missing' },
        { id: 'd3', type: 'residencia', name: 'Comprovante Residência', status: 'missing' },
        { id: 'd4', type: 'nota_fiscal', name: 'Nota Fiscal de Produtor (Exemplo)', status: 'missing' },
      ];

      // Gerar Checklist Dinâmico com Detalhes
      const newChecklist: ChecklistItem[] = [
        { 
          id: '1', 
          title: 'Regularizar Documentos Pessoais', 
          description: 'RG, CPF do produtor e cônjuge.', 
          priority: 'medium', 
          status: 'done',
          detailedSteps: [
            { text: 'Verifique se o RG tem menos de 10 anos de emissão.' },
            { text: 'Certifique-se de que o CPF está regular na Receita Federal.' },
            { text: 'Digitalize ou tire foto frente e verso.' }
          ],
          relatedDocId: 'd1'
        },
      ];

      if (answers.documentacao_base !== 'Tenho ativa') {
        newChecklist.push({ 
          id: '2', 
          title: 'Obter ou Renovar CAF/DAP', 
          description: 'Documento essencial para agricultura familiar.', 
          priority: 'high', 
          status: 'todo',
          detailedSteps: [
            { 
              text: 'Procure o sindicato rural ou escritório da Emater/Epagri do seu município.',
              helpContent: {
                type: 'tip',
                title: 'Como encontrar?',
                description: 'Busque na internet por "Sindicato Rural" ou "Emater" seguido do nome da sua cidade. Geralmente ficam próximos à Secretaria de Agricultura.'
              }
            },
            { text: 'Leve RG, CPF e documentos da terra (Escritura, Contrato de Arrendamento ou Comodato).' },
            { text: 'Agende uma visita técnica do extensionista na sua propriedade.' },
            { text: 'Após a visita, o documento será emitido e deve ser assinado.' }
          ],
          relatedDocId: 'd2' // Link para upload da CAF
        });
      }

      newChecklist.push({ 
        id: '3', 
        title: 'Habilitar Nota Fiscal de Produtor', 
        description: 'Necessário para receber pagamentos oficiais.', 
        priority: 'high', 
        status: 'todo',
        detailedSteps: [
          { text: 'Vá ao setor de tributos da Prefeitura Municipal.' },
          { text: 'Solicite o cadastro de Produtor Rural (leve a CAF/DAP e documentos da terra).' },
          { 
            text: 'Peça o talão de notas físicas ou acesso ao sistema de Nota Fiscal Eletrônica (NFP-e).',
            helpContent: {
              type: 'tip',
              title: 'Sobre o Formulário',
              description: 'Você deverá preencher o "Formulário de Inscrição Cadastral" (FAC). Ele solicita dados pessoais, documentos da terra e qual será sua atividade principal (ex: Agricultura).'
            }
          },
          { 
            text: 'Faça uma nota de teste (simbólica) para aprender o preenchimento.',
            helpContent: {
              type: 'tip',
              title: 'Dica de Preenchimento',
              description: 'Atenção aos campos: "Valor Unitário" (preço por kg ou unidade) e "Quantidade". A descrição deve ser exata conforme o produto (ex: Alface Crespa - Maço).'
            }
          }
        ],
        relatedDocId: 'd4'
      });

      if (answers.publico_alvo?.includes('Pública') || answers.publico_alvo?.includes('Ambas')) {
        newChecklist.push({ 
          id: '4', 
          title: 'Cadastro de Fornecedor na Prefeitura', 
          description: 'Ir à secretaria de educação ou agricultura.', 
          priority: 'medium', 
          status: 'todo',
          detailedSteps: [
            { 
              text: 'Localize o setor de compras ou a Secretaria de Educação.',
              helpContent: {
                type: 'tip',
                title: 'Dica de Localização',
                description: 'Pergunte na recepção da prefeitura pelo "Setor de Licitações" ou "Comissão de Compras do PNAE".'
              }
            },
            { text: 'Preencha a ficha de cadastro de fornecedor.' },
            { text: 'Entregue cópias da CAF/DAP, RG, CPF e Projeto de Venda (quando houver chamada).' }
          ]
        });
        newChecklist.push({ 
          id: '5', 
          title: 'Mapear Chamadas Públicas', 
          description: 'Ficar atento aos editais do PNAE.', 
          priority: 'medium', 
          status: 'todo',
          detailedSteps: [
            { text: 'Acesse o site da prefeitura semanalmente na área de "Licitações" ou "Chamadas Públicas".' },
            { text: 'Entre em contato com nutricionistas da rede municipal.' },
            { text: 'Verifique os produtos solicitados no edital e veja se você tem produção suficiente.' }
          ]
        });
      }

      if (caseType === 'needs_human') {
        newChecklist.unshift({ 
          id: '0', 
          title: 'Consultoria Sanitária', 
          description: 'Seu caso exige aprovação da Vigilância ou MAPA.', 
          priority: 'high', 
          status: 'todo',
          detailedSteps: [
            { 
              text: 'Identifique se seu produto precisa de SIM (Municipal), SIE (Estadual) ou SIF (Federal).',
              helpContent: {
                type: 'tip',
                title: 'Qual selo eu preciso?',
                description: 'SIM: Venda apenas no seu município. SIE: Venda em todo o estado. SIF: Venda no Brasil todo. Produtos animais sempre exigem um destes.'
              }
            },
            { text: 'Contrate um Responsável Técnico (RT) se exigido.' },
            { text: 'Adeque a estrutura física (cozinha, área de processamento) conforme normas.' }
          ]
        });
      }

      const newUser: UserProfile = {
        name: answers.name,
        producerType: answers.tipo_alimento,
        city: answers.municipio,
        answers,
        riskFlags,
        caseType
      };

      setUser(newUser);
      setChecklist(newChecklist);
      setDocuments(initialDocs);
      
      setLoading(false);
      setView('dashboard');
    }, 1500); // Simula delay da IA
  };

  // --- Views ---

  if (view === 'landing') {
    return <LandingPage 
      onStart={() => setView('onboarding')} 
      onConsult={() => setView('escalation')}
    />;
  }

  if (view === 'onboarding') {
    return <OnboardingFlow onFinish={generatePlan} isLoading={loading} />;
  }

  if (view === 'dashboard' && user) {
    return (
      <Dashboard 
        user={user} 
        checklist={checklist} 
        documents={documents}
        setChecklist={setChecklist}
        setDocuments={setDocuments}
        onEscalate={() => setView('escalation')}
        onLogout={() => setView('landing')}
      />
    );
  }

  if (view === 'escalation') {
    return <EscalationPage onBack={() => setView(user ? 'dashboard' : 'landing')} />;
  }

  return null;
}

// --- Componente: Chat Widget (IA Conversacional) ---

function ChatWidget({ userName }: { userName: string }) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    { id: '1', role: 'assistant', content: `Olá, ${userName.split(' ')[0]}! Sou sua assistente virtual. Posso te ajudar com o checklist, explicar documentos ou ler as instruções em áudio. Como posso ajudar?` }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isOpen]);

  const handleSend = () => {
    if (!inputValue.trim()) return;

    const newMsg: ChatMessage = { id: Date.now().toString(), role: 'user', content: inputValue };
    setMessages(prev => [...prev, newMsg]);
    setInputValue('');
    setIsTyping(true);

    // Simulação de Resposta da IA
    setTimeout(() => {
      let replyText = "Entendi. Para resolver isso, você precisa ir até a Secretaria de Agricultura com seu RG e CPF.";
      if (inputValue.toLowerCase().includes('caf') || inputValue.toLowerCase().includes('dap')) {
        replyText = "A CAF (Cadastro Nacional da Agricultura Familiar) substituiu a DAP. Você pode solicitá-la no sindicato rural ou na Emater do seu município. Quer que eu liste os documentos necessários?";
      } else if (inputValue.toLowerCase().includes('nota')) {
        replyText = "Para emitir Nota Fiscal, você precisa do cadastro de produtor na prefeitura. É um processo rápido e gratuito na maioria dos municípios.";
      }

      const replyMsg: ChatMessage = { id: (Date.now() + 1).toString(), role: 'assistant', content: replyText };
      setMessages(prev => [...prev, replyMsg]);
      setIsTyping(false);
    }, 1500);
  };

  const toggleRecording = () => {
    if (isRecording) return;
    setIsRecording(true);
    
    // Simulação de Transcrição de Áudio (STT)
    setTimeout(() => {
      setIsRecording(false);
      setInputValue("Como faço para renovar minha CAF que venceu?");
    }, 2000);
  };

  const playAudio = (text: string, msgId: string) => {
    // Parar qualquer áudio anterior
    window.speechSynthesis.cancel();

    // Atualizar estado visual
    setMessages(prev => prev.map(m => ({ ...m, audioPlaying: m.id === msgId })));

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'pt-BR';
    utterance.onend = () => {
      setMessages(prev => prev.map(m => ({ ...m, audioPlaying: false })));
    };
    
    window.speechSynthesis.speak(utterance);
  };

  const stopAudio = () => {
    window.speechSynthesis.cancel();
    setMessages(prev => prev.map(m => ({ ...m, audioPlaying: false })));
  };

  return (
    <>
      {/* Botão Flutuante (FAB) */}
      {!isOpen && (
        <button 
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 bg-green-600 hover:bg-green-700 text-white p-4 rounded-full shadow-lg transition-transform hover:scale-110 z-50 flex items-center justify-center group"
        >
          <MessageSquare className="h-6 w-6" />
          <span className="absolute right-full mr-3 bg-white text-slate-700 px-3 py-1 rounded-lg text-sm font-bold shadow-md opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
            Tirar dúvidas
          </span>
        </button>
      )}

      {/* Janela do Chat */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 w-full max-w-sm bg-white rounded-2xl shadow-2xl border border-slate-200 z-50 flex flex-col overflow-hidden animate-in slide-in-from-bottom-10 fade-in duration-300" style={{ height: '500px' }}>
          
          {/* Header */}
          <div className="bg-green-600 p-4 flex justify-between items-center text-white">
            <div className="flex items-center gap-2">
              <div className="bg-white/20 p-1.5 rounded-full">
                <Leaf className="h-4 w-4" />
              </div>
              <div>
                <h3 className="font-bold text-sm">Assistente CertificaFácil</h3>
                <p className="text-[10px] opacity-90 flex items-center gap-1">
                  <span className="w-1.5 h-1.5 bg-green-300 rounded-full animate-pulse"></span> Online
                </p>
              </div>
            </div>
            <button onClick={() => setIsOpen(false)} className="hover:bg-green-700 p-1 rounded transition">
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Área de Mensagens */}
          <div className="flex-1 overflow-y-auto p-4 bg-slate-50 space-y-4">
            {messages.map((msg) => (
              <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] rounded-2xl p-3 text-sm relative group ${
                  msg.role === 'user' 
                    ? 'bg-green-600 text-white rounded-br-none' 
                    : 'bg-white text-slate-700 shadow-sm border border-slate-100 rounded-bl-none'
                }`}>
                  <p>{msg.content}</p>
                  
                  {/* Controles de Áudio para o Assistente */}
                  {msg.role === 'assistant' && (
                    <div className="mt-2 flex items-center gap-2 border-t border-slate-100 pt-2">
                      <button 
                        onClick={() => msg.audioPlaying ? stopAudio() : playAudio(msg.content, msg.id)}
                        className="flex items-center gap-1.5 text-xs font-bold text-green-600 hover:bg-green-50 px-2 py-1 rounded transition"
                      >
                        {msg.audioPlaying ? (
                          <>
                            <Square className="h-3 w-3 fill-current" /> Parar
                          </>
                        ) : (
                          <>
                            <Play className="h-3 w-3 fill-current" /> Ouvir
                          </>
                        )}
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
            {isTyping && (
              <div className="flex justify-start">
                <div className="bg-slate-200 rounded-full px-4 py-2 flex gap-1">
                  <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"></span>
                  <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce delay-75"></span>
                  <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce delay-150"></span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Área de Input */}
          <div className="p-3 bg-white border-t border-slate-100">
            {isRecording ? (
               <div className="flex items-center justify-between bg-red-50 text-red-600 px-4 py-3 rounded-xl border border-red-100 animate-pulse">
                 <span className="text-sm font-bold flex items-center gap-2">
                   <Mic className="h-4 w-4" /> Gravando...
                 </span>
                 <span className="text-xs">Ouvindo sua dúvida</span>
               </div>
            ) : (
              <div className="flex gap-2">
                <button 
                  onClick={toggleRecording}
                  className="p-3 text-slate-400 hover:text-green-600 hover:bg-green-50 rounded-xl transition bg-slate-50 border border-slate-200"
                  title="Falar (Transcrição)"
                >
                  <Mic className="h-5 w-5" />
                </button>
                <div className="flex-1 relative">
                  <input 
                    type="text" 
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                    placeholder="Digite sua dúvida..." 
                    className="w-full h-full pl-4 pr-10 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-green-500 text-sm"
                  />
                  <button 
                    onClick={handleSend}
                    disabled={!inputValue.trim()}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 text-green-600 hover:bg-green-100 rounded-lg disabled:opacity-50 disabled:hover:bg-transparent transition"
                  >
                    <Send className="h-4 w-4" />
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}

// --- Componente Landing Page ---

function LandingPage({ onStart, onConsult }: { onStart: () => void, onConsult: () => void }) {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      <nav className="p-6 flex justify-between items-center max-w-6xl mx-auto w-full">
        <div className="flex items-center gap-2">
          <Leaf className="text-green-600 h-6 w-6" />
          <span className="text-xl font-bold text-slate-800">CertificaFácil</span>
        </div>
        <button className="text-sm font-medium text-slate-600 hover:text-green-700">Entrar</button>
      </nav>

      <main className="flex-1 flex flex-col items-center justify-center p-6 text-center max-w-4xl mx-auto mt-10">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-green-100 text-green-800 text-xs font-semibold mb-6">
          <ShieldCheck className="h-3 w-3" />
          MVP para Produtores Rurais
        </div>
        
        <h1 className="text-4xl md:text-5xl font-extrabold text-slate-900 mb-6 leading-tight">
          Venda para escolas e mercados <br className="hidden md:block"/>
          <span className="text-green-600">sem medo da burocracia</span>
        </h1>
        
        <p className="text-lg text-slate-600 mb-10 max-w-2xl mx-auto">
          Um assistente inteligente que organiza seus documentos, monta seu checklist e diz exatamente o que fazer para se regularizar.
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
            { title: 'Cofre de Documentos', desc: 'Guarde tudo em um lugar seguro e receba alertas de validade.' }
          ].map((feat, i) => (
            <div key={i} className="bg-white p-6 rounded-xl shadow-sm border border-slate-100 hover:border-green-200 transition">
              <CheckCircle2 className="text-green-500 h-6 w-6 mb-3" />
              <h3 className="font-bold text-slate-800 mb-2">{feat.title}</h3>
              <p className="text-sm text-slate-500">{feat.desc}</p>
            </div>
          ))}
        </div>

        <p className="mt-12 text-xs text-slate-400 max-w-lg">
          Aviso: O CertificaFácil é uma ferramenta informativa. Não substituímos órgãos oficiais como MAPA, Vigilância Sanitária ou consultoria jurídica.
        </p>
      </main>
    </div>
  );
}

// --- Componente Onboarding (Chat) ---

function OnboardingFlow({ onFinish, isLoading }: { onFinish: (a: any) => void, isLoading: boolean }) {
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const inputRef = useRef<HTMLInputElement>(null);

  const currentQ = ONBOARDING_QUESTIONS[step];

  const handleAnswer = (val: string) => {
    const newAnswers = { ...answers, [currentQ.key]: val };
    setAnswers(newAnswers);
    if (inputRef.current) inputRef.current.value = '';

    if (step < ONBOARDING_QUESTIONS.length - 1) {
      setStep(step + 1);
    } else {
      onFinish(newAnswers);
    }
  };

  const handleTextSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputRef.current?.value) handleAnswer(inputRef.current.value);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-6 text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mb-4"></div>
        <h2 className="text-xl font-bold text-slate-800">Analisando seu caso...</h2>
        <p className="text-slate-500">Nossa IA está verificando as exigências para o seu perfil.</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white flex flex-col">
      <div className="w-full bg-slate-50 h-2">
        <div 
          className="bg-green-500 h-2 transition-all duration-500" 
          style={{ width: `${((step + 1) / ONBOARDING_QUESTIONS.length) * 100}%` }}
        />
      </div>

      <div className="flex-1 flex flex-col max-w-lg mx-auto w-full p-6 justify-center">
        <div className="mb-8 animate-fade-in">
          <div className="flex items-center gap-3 mb-4">
            <div className="bg-green-100 p-2 rounded-lg">
              <MessageSquare className="text-green-600 h-6 w-6" />
            </div>
            <span className="text-sm font-bold text-slate-400 uppercase tracking-wide">
              Pergunta {step + 1} de {ONBOARDING_QUESTIONS.length}
            </span>
          </div>
          <h2 className="text-2xl font-bold text-slate-800 leading-snug">{currentQ.text}</h2>
        </div>

        <div className="space-y-3">
          {currentQ.type === 'choice' && currentQ.options?.map((opt) => (
            <button
              key={opt}
              onClick={() => handleAnswer(opt)}
              className="w-full text-left p-4 border-2 border-slate-100 rounded-xl hover:border-green-500 hover:bg-green-50 transition font-medium text-slate-700 active:scale-95"
            >
              {opt}
            </button>
          ))}

          {currentQ.type === 'text' && (
            <form onSubmit={handleTextSubmit} className="flex flex-col gap-4">
              <input
                ref={inputRef}
                type="text"
                placeholder={currentQ.placeholder}
                className="w-full p-4 border-2 border-slate-200 rounded-xl focus:border-green-500 focus:outline-none text-lg"
                autoFocus
              />
              <button 
                type="submit"
                className="bg-green-600 text-white font-bold py-4 rounded-xl hover:bg-green-700 transition"
              >
                Continuar
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}

// --- Componente Dashboard ---

function Dashboard({ 
  user, checklist, documents, setChecklist, setDocuments, onEscalate, onLogout 
}: { 
  user: UserProfile, 
  checklist: ChecklistItem[], 
  documents: Document[],
  setChecklist: any,
  setDocuments: any,
  onEscalate: () => void,
  onLogout: () => void
}) {
  const [activeTab, setActiveTab] = useState<'checklist' | 'docs'>('checklist');
  const [selectedItem, setSelectedItem] = useState<ChecklistItem | null>(null);
  const [expandedStepHelp, setExpandedStepHelp] = useState<number | null>(null);

  const toggleItem = (id: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    setChecklist((prev: ChecklistItem[]) => prev.map(item => {
      if (item.id === id) {
        return { ...item, status: item.status === 'done' ? 'todo' : 'done' };
      }
      return item;
    }));
  };

  const uploadDoc = (id: string) => {
    setDocuments((prev: Document[]) => prev.map(doc => 
      doc.id === id ? { ...doc, status: 'uploaded' } : doc
    ));
    
    setTimeout(() => {
      setDocuments((prev: Document[]) => prev.map(doc => 
        doc.id === id ? { ...doc, status: 'ai_reviewed', aiNotes: 'Documento parece legível. Data de validade OK.' } : doc
      ));
    }, 1500);
  };

  const progress = Math.round((checklist.filter(i => i.status === 'done').length / checklist.length) * 100);
  const isRisky = user.caseType === 'needs_human';

  const openDetails = (item: ChecklistItem) => {
    setSelectedItem(item);
    setExpandedStepHelp(null);
  }

  // --- Sub-View: Detalhes do Item (Passo a Passo) ---
  if (selectedItem) {
    const relatedDoc = documents.find(d => d.id === selectedItem.relatedDocId);
    
    return (
      <div className="min-h-screen bg-slate-50 font-sans flex flex-col relative">
         <header className="bg-white shadow-sm p-4 sticky top-0 z-10">
          <div className="max-w-3xl mx-auto w-full">
            <button 
              onClick={() => setSelectedItem(null)}
              className="flex items-center text-slate-500 hover:text-slate-800 text-sm font-medium"
            >
              <ChevronLeft className="h-5 w-5 mr-1" />
              Voltar ao Checklist
            </button>
          </div>
         </header>

         <div className="flex-1 max-w-3xl mx-auto w-full p-6 pb-24">
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8">
              
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h2 className="text-2xl font-bold text-slate-800 mb-2">{selectedItem.title}</h2>
                  <p className="text-slate-500">{selectedItem.description}</p>
                </div>
                {selectedItem.priority === 'high' && (
                  <span className="bg-red-100 text-red-700 text-xs font-bold px-3 py-1 rounded-full uppercase">
                    Importante
                  </span>
                )}
              </div>

              {/* Seção Como Fazer */}
              {selectedItem.detailedSteps && selectedItem.detailedSteps.length > 0 && (
                <div className="mb-10">
                  <h3 className="font-bold text-lg text-slate-800 mb-4 flex items-center gap-2">
                    <Info className="h-5 w-5 text-blue-500" />
                    Passo a Passo
                  </h3>
                  <div className="space-y-4">
                    {selectedItem.detailedSteps.map((step, idx) => (
                      <div key={idx} className="flex flex-col gap-3">
                        <div className="flex items-start gap-4">
                          <div className="flex-shrink-0 h-8 w-8 rounded-full bg-blue-50 text-blue-600 font-bold flex items-center justify-center text-sm border border-blue-100">
                            {idx + 1}
                          </div>
                          <div className="flex-1">
                            <p className="text-slate-700 mt-1">{step.text}</p>
                            
                            {/* Botão "Me Mostre Como" */}
                            {step.helpContent && (
                              <button 
                                onClick={() => setExpandedStepHelp(expandedStepHelp === idx ? null : idx)}
                                className="mt-2 text-xs font-bold text-blue-600 hover:text-blue-800 flex items-center gap-1.5 transition"
                              >
                                {expandedStepHelp === idx ? (
                                  <>Ocultar guia</>
                                ) : (
                                  <>
                                    <Lightbulb className="h-3 w-3" />
                                    Dica útil
                                  </>
                                )}
                              </button>
                            )}
                          </div>
                        </div>

                        {/* Área Expandida de Ajuda (Texto Apenas) */}
                        {expandedStepHelp === idx && step.helpContent && (
                          <div className="ml-12 bg-blue-50 border border-blue-100 rounded-lg p-4 animate-in slide-in-from-top-2 fade-in">
                            <h4 className="font-bold text-sm text-blue-800 mb-2 flex items-center gap-2">
                                <Info className="h-4 w-4"/>
                                {step.helpContent.title}
                            </h4>
                            <p className="text-sm text-blue-700 leading-relaxed">{step.helpContent.description}</p>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Seção de Upload Contextual */}
              {relatedDoc && (
                <div className="bg-slate-50 rounded-lg p-6 border border-slate-200">
                  <h3 className="font-bold text-slate-800 mb-2 flex items-center gap-2">
                    <FileText className="h-5 w-5 text-green-600" />
                    Documento Necessário: {relatedDoc.name}
                  </h3>
                  <p className="text-sm text-slate-500 mb-4">
                    Após concluir os passos acima, envie a foto ou PDF do documento aqui para validação.
                  </p>
                  
                  <div className="flex items-center gap-4">
                    <div className="flex-1">
                      {relatedDoc.status === 'missing' && <span className="text-xs bg-slate-200 text-slate-600 px-2 py-1 rounded font-bold">Pendente</span>}
                      {(relatedDoc.status === 'uploaded' || relatedDoc.status === 'ai_reviewed') && <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded font-bold">Enviado</span>}
                    </div>
                    
                    <button 
                      onClick={() => uploadDoc(relatedDoc.id)}
                      disabled={relatedDoc.status !== 'missing'}
                      className="bg-slate-800 hover:bg-slate-900 text-white px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed transition"
                    >
                      <Upload className="h-4 w-4" />
                      {relatedDoc.status === 'missing' ? 'Fazer Upload Agora' : 'Upload Concluído'}
                    </button>
                  </div>
                  
                  {relatedDoc.aiNotes && (
                     <div className="mt-4 bg-white p-3 rounded border border-green-200 text-xs text-green-800 flex gap-2">
                       <ShieldCheck className="h-4 w-4 shrink-0" />
                       {relatedDoc.aiNotes}
                     </div>
                  )}
                </div>
              )}

              {/* Botão de Concluir Tarefa */}
              <div className="mt-10 pt-6 border-t border-slate-100 flex justify-end">
                <button 
                  onClick={() => {
                     if (selectedItem.status !== 'done') toggleItem(selectedItem.id);
                     setSelectedItem(null);
                  }}
                  className={`px-6 py-3 rounded-lg font-bold transition flex items-center gap-2 ${selectedItem.status === 'done' ? 'bg-green-100 text-green-700' : 'bg-green-600 text-white hover:bg-green-700'}`}
                >
                  <CheckCircle2 className="h-5 w-5" />
                  {selectedItem.status === 'done' ? 'Tarefa Concluída' : 'Marcar como Concluído'}
                </button>
              </div>

            </div>
         </div>
         <ChatWidget userName={user.name} />
      </div>
    );
  }

  // --- View Principal do Dashboard ---
  return (
    <div className="min-h-screen bg-slate-100 font-sans relative">
      {/* Header */}
      <header className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <div className="bg-green-600 rounded-full p-1.5">
              <Leaf className="text-white h-4 w-4" />
            </div>
            <span className="font-bold text-slate-800 hidden sm:inline">CertificaFácil</span>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right hidden sm:block">
              <p className="text-sm font-bold text-slate-800">{user.name}</p>
              <p className="text-xs text-slate-500">{user.city}</p>
            </div>
            <div className="h-8 w-8 bg-slate-200 rounded-full flex items-center justify-center">
              <User className="h-5 w-5 text-slate-500" />
            </div>
            <button onClick={onLogout} className="text-xs text-slate-400 hover:text-red-500">Sair</button>
          </div>
        </div>
      </header>

      <div className="max-w-5xl mx-auto p-4 md:p-8 pb-24">
        
        {/* Alerts */}
        {isRisky && (
          <div className="bg-orange-50 border border-orange-200 rounded-xl p-4 mb-6 flex items-start gap-4">
            <AlertTriangle className="text-orange-600 h-6 w-6 shrink-0 mt-1" />
            <div>
              <h3 className="font-bold text-orange-800">Atenção: Seu caso possui complexidade</h3>
              <p className="text-sm text-orange-700 mt-1">
                Detectamos <strong>{user.riskFlags.join(', ')}</strong>. Isso geralmente exige RT (Responsável Técnico) ou aprovação sanitária específica.
              </p>
              <button onClick={onEscalate} className="mt-3 text-sm bg-orange-100 text-orange-800 font-bold px-3 py-1.5 rounded hover:bg-orange-200 transition">
                Ver Consultores Recomendados
              </button>
            </div>
          </div>
        )}

        {/* Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="bg-white p-6 rounded-xl shadow-sm">
            <p className="text-xs font-bold text-slate-400 uppercase mb-1">Status Geral</p>
            <div className="flex items-center gap-2">
              <div className={`h-3 w-3 rounded-full ${progress === 100 ? 'bg-green-500' : 'bg-yellow-500'}`} />
              <span className="text-xl font-bold text-slate-800">
                {progress === 100 ? 'Pronto para Venda' : 'Em Preparação'}
              </span>
            </div>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-sm">
            <p className="text-xs font-bold text-slate-400 uppercase mb-1">Seu Progresso</p>
            <div className="flex items-center gap-3">
              <span className="text-2xl font-bold text-slate-800">{progress}%</span>
              <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-green-500 transition-all duration-1000" 
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-sm">
            <p className="text-xs font-bold text-slate-400 uppercase mb-1">Próxima Ação</p>
            <p className="text-sm font-medium text-slate-700 truncate">
              {checklist.find(i => i.status !== 'done')?.title || 'Tudo completo!'}
            </p>
          </div>
        </div>

        {/* Main Content Tabs */}
        <div className="flex gap-6 mb-4 border-b border-slate-200">
          <button 
            onClick={() => setActiveTab('checklist')}
            className={`pb-3 text-sm font-bold transition ${activeTab === 'checklist' ? 'text-green-600 border-b-2 border-green-600' : 'text-slate-500'}`}
          >
            Checklist de Tarefas
          </button>
          <button 
            onClick={() => setActiveTab('docs')}
            className={`pb-3 text-sm font-bold transition ${activeTab === 'docs' ? 'text-green-600 border-b-2 border-green-600' : 'text-slate-500'}`}
          >
            Meus Documentos
          </button>
        </div>

        {/* Checklist View */}
        {activeTab === 'checklist' && (
          <div className="space-y-3">
            {checklist.map((item) => (
              <div 
                key={item.id} 
                onClick={() => openDetails(item)}
                className={`group bg-white p-4 rounded-lg border shadow-sm transition-all hover:shadow-md hover:border-green-300 cursor-pointer flex items-start gap-4 ${item.status === 'done' ? 'border-green-200 bg-green-50/30' : 'border-slate-100'}`}
              >
                <div 
                  onClick={(e) => toggleItem(item.id, e)}
                  className={`mt-1 h-6 w-6 rounded border-2 flex items-center justify-center transition-colors z-10 ${item.status === 'done' ? 'bg-green-500 border-green-500 text-white' : 'border-slate-300 text-transparent hover:border-green-400'}`}
                >
                  <CheckCircle2 className="h-4 w-4" />
                </div>
                <div className="flex-1">
                  <div className="flex justify-between items-start">
                    <h4 className={`font-bold text-slate-800 ${item.status === 'done' ? 'line-through text-slate-400' : ''}`}>
                      {item.title}
                    </h4>
                    {item.priority === 'high' && item.status !== 'done' && (
                      <span className="text-[10px] font-bold bg-red-100 text-red-600 px-2 py-0.5 rounded-full uppercase">Alta Prioridade</span>
                    )}
                  </div>
                  <p className="text-sm text-slate-500 mt-1">{item.description}</p>
                  
                  {/* Indicação visual de que é clicável */}
                  <div className="mt-3 flex items-center text-xs text-green-600 font-bold opacity-0 group-hover:opacity-100 transition-opacity">
                    Ver passo a passo <ChevronRight className="h-3 w-3 ml-1" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Documents View */}
        {activeTab === 'docs' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {documents.map((doc) => (
              <div key={doc.id} className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex items-center gap-2">
                    <FileText className="text-slate-400 h-5 w-5" />
                    <span className="font-bold text-slate-700">{doc.name}</span>
                  </div>
                  {doc.status === 'missing' && <span className="text-xs bg-slate-100 text-slate-500 px-2 py-1 rounded">Pendente</span>}
                  {(doc.status === 'uploaded' || doc.status === 'ai_reviewed') && <span className="text-xs bg-blue-100 text-blue-600 px-2 py-1 rounded">Enviado</span>}
                </div>
                
                {doc.aiNotes && (
                  <div className="mb-4 bg-green-50 p-3 rounded text-xs text-green-800 flex gap-2">
                    <ShieldCheck className="h-4 w-4 shrink-0" />
                    {doc.aiNotes}
                  </div>
                )}

                <button 
                  onClick={() => uploadDoc(doc.id)}
                  disabled={doc.status !== 'missing'}
                  className="w-full border-2 border-dashed border-slate-300 rounded-lg p-3 text-slate-500 text-sm font-medium hover:border-green-500 hover:text-green-600 transition flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Upload className="h-4 w-4" />
                  {doc.status === 'missing' ? 'Fazer Upload' : 'Documento Enviado'}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      <ChatWidget userName={user.name} />
    </div>
  );
}

// --- Componente Escalation (Ajuda Especializada) ---

function EscalationPage({ onBack }: { onBack: () => void }) {
  return (
    <div className="min-h-screen bg-slate-50 font-sans p-6">
      <div className="max-w-3xl mx-auto">
        <button onClick={onBack} className="flex items-center text-slate-500 hover:text-slate-800 mb-6">
          <ArrowRight className="h-4 w-4 rotate-180 mr-1" /> Voltar
        </button>

        <header className="mb-8">
          <h1 className="text-3xl font-bold text-slate-800 mb-2">Ajuda Especializada</h1>
          <p className="text-slate-600">
            Seu caso possui detalhes técnicos que exigem um profissional. Selecionamos consultores baseados na sua região.
          </p>
        </header>

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="p-4 border-b border-slate-100 bg-slate-50 flex gap-2">
            <Search className="text-slate-400 h-5 w-5" />
            <input type="text" placeholder="Filtrar por especialidade..." className="bg-transparent outline-none text-sm w-full" />
          </div>
          
          <div className="divide-y divide-slate-100">
            {MOCK_CONSULTANTS.map((cons) => (
              <div key={cons.id} className="p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 hover:bg-slate-50 transition">
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
          </div>
        </div>
      </div>
    </div>
  );
}