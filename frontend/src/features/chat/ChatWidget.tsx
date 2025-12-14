import { useEffect, useRef, useState } from 'react';
import { Leaf, MessageSquare, Mic, Play, Send, Square, X } from 'lucide-react';
import type { ChatMessage } from '../../domain/models';

export function ChatWidget({ userName }: { userName: string }) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      role: 'assistant',
      content: `Olá, ${userName.split(' ')[0]}! Posso te ajudar com a lista de tarefas, explicar documentos ou ler as instruções em áudio. Como posso ajudar?`,
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isOpen]);

  const handleSend = () => {
    const prompt = inputValue.trim();
    if (!prompt) return;

    const newMsg: ChatMessage = { id: Date.now().toString(), role: 'user', content: prompt };
    setMessages((prev) => [...prev, newMsg]);
    setInputValue('');
    setIsTyping(true);

    window.setTimeout(() => {
      let replyText =
        'Entendi. Para resolver isso, você precisa ir até a Secretaria de Agricultura com seu RG e CPF.';

      const normalized = prompt.toLowerCase();
      if (normalized.includes('caf') || normalized.includes('dap')) {
        replyText =
          'A CAF (Cadastro Nacional da Agricultura Familiar) substituiu a DAP. Você pode solicitá-la no sindicato rural ou na Emater do seu município. Quer que eu liste os documentos necessários?';
      } else if (normalized.includes('nota')) {
        replyText =
          'Para emitir Nota Fiscal, você precisa do cadastro de produtor na prefeitura. É um processo rápido e gratuito na maioria dos municípios.';
      }

      const replyMsg: ChatMessage = { id: (Date.now() + 1).toString(), role: 'assistant', content: replyText };
      setMessages((prev) => [...prev, replyMsg]);
      setIsTyping(false);
    }, 1500);
  };

  const toggleRecording = () => {
    if (isRecording) return;
    setIsRecording(true);

    window.setTimeout(() => {
      setIsRecording(false);
      setInputValue('Como faço para renovar minha CAF que venceu?');
    }, 2000);
  };

  const playAudio = (text: string, msgId: string) => {
    window.speechSynthesis.cancel();

    setMessages((prev) => prev.map((m) => ({ ...m, audioPlaying: m.id === msgId })));

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'pt-BR';
    utterance.onend = () => {
      setMessages((prev) => prev.map((m) => ({ ...m, audioPlaying: false })));
    };

    window.speechSynthesis.speak(utterance);
  };

  const stopAudio = () => {
    window.speechSynthesis.cancel();
    setMessages((prev) => prev.map((m) => ({ ...m, audioPlaying: false })));
  };

  return (
    <>
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

      {isOpen && (
        <div
          className="fixed bottom-6 right-6 w-full max-w-sm bg-white rounded-2xl shadow-2xl border border-slate-200 z-50 flex flex-col overflow-hidden animate-in slide-in-from-bottom-10 fade-in duration-300"
          style={{ height: '500px' }}
        >
          <div className="bg-green-600 p-4 flex justify-between items-center text-white">
            <div className="flex items-center gap-2">
              <div className="bg-white/20 p-1.5 rounded-full">
                <Leaf className="h-4 w-4" />
              </div>
              <div>
                <h3 className="font-bold text-sm">Ajuda CertificaFácil</h3>
                <p className="text-[10px] opacity-90 flex items-center gap-1">
                  <span className="w-1.5 h-1.5 bg-green-300 rounded-full animate-pulse"></span> Online
                </p>
              </div>
            </div>
            <button onClick={() => setIsOpen(false)} className="hover:bg-green-700 p-1 rounded transition">
              <X className="h-5 w-5" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-4 bg-slate-50 space-y-4">
            {messages.map((msg) => (
              <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className={`max-w-[85%] rounded-2xl p-3 text-sm relative group ${
                    msg.role === 'user'
                      ? 'bg-green-600 text-white rounded-br-none'
                      : 'bg-white text-slate-700 shadow-sm border border-slate-100 rounded-bl-none'
                  }`}
                >
                  <p>{msg.content}</p>

                  {msg.role === 'assistant' && (
                    <div className="mt-2 flex items-center gap-2 border-t border-slate-100 pt-2">
                      <button
                        onClick={() => (msg.audioPlaying ? stopAudio() : playAudio(msg.content, msg.id))}
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
