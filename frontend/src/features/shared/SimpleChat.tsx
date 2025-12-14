import { useState, useEffect } from 'react';
import { MessageCircle, X, Send, Volume2, VolumeX, Mic, Type } from 'lucide-react';
import { sendChatMessageV2 } from '../../services/api/chat';
import { ApiClientError } from '../../services/api/client';
import { AudioRecorder } from '../chat/AudioRecorder';
import { AudioPlayer } from '../chat/AudioPlayer';
import { presignDocument } from '../../services/api/documents';
import { normalizeUploadUrl } from '../../services/api/client';
import { getProducerProfile } from '../../services/api/producer';
import { getOnboardingPreference } from '../../services/api/onboarding';

const SUGGESTED_QUESTIONS = [
  {
    text: "O que eu preciso fazer para começar?",
    icon: "🚀",
    description: "Veja os primeiros passos"
  },
  {
    text: "Como vender meus produtos para as escolas?",
    icon: "🏫",
    description: "Entenda o processo de venda"
  },
  {
    text: "Quais documentos eu preciso ter?",
    icon: "📄",
    description: "Lista completa de documentos"
  },
  {
    text: "Quanto posso ganhar com o PNAE?",
    icon: "💰",
    description: "Saiba sobre os ganhos possíveis"
  },
  {
    text: "Preciso de ajuda para tirar a DAP",
    icon: "🤝",
    description: "Orientações passo a passo"
  },
];

interface SimpleChatProps {
  userName?: string;
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  audioUrl?: string | null;
}

type InputMode = 'text' | 'audio';

export function SimpleChat({}: SimpleChatProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [prefersAudio, setPrefersAudio] = useState(false);
  const [inputMode, setInputMode] = useState<InputMode>('text');
  const [lastMessageWasAudio, setLastMessageWasAudio] = useState(false);

  // Load user preference from onboarding
  useEffect(() => {
    const loadUserPreference = async () => {
      try {
        const profile = await getProducerProfile();
        if (profile?.onboarding_status === 'completed') {
          // Fetch onboarding answer for preferences_1 question
          try {
            const preference = await getOnboardingPreference();
            if (preference.prefers_audio) {
              setPrefersAudio(true);
            }
          } catch (prefErr) {
            console.warn('Error loading onboarding preference:', prefErr);
            // Continue with default (text mode)
          }
        }
      } catch (err) {
        console.error('Error loading user preference:', err);
      }
    };
    if (isOpen) {
      loadUserPreference();
    }
  }, [isOpen]);

  const handleSend = async (messageText?: string) => {
    const textToSend = messageText || input.trim();
    if (!textToSend || isLoading) return;

    const userMessage = textToSend;
    setInput('');
    setError('');
    setLastMessageWasAudio(false); // Text message

    // Add user message
    const newMessages: ChatMessage[] = [...messages, { role: 'user' as const, content: userMessage }];
    setMessages(newMessages);
    setIsLoading(true);

    try {
      const response = await sendChatMessageV2({
        conversation_id: conversationId || undefined,
        input_type: 'text',
        text: userMessage,
        locale: 'pt-BR',
        client_capabilities: {
          can_play_audio: true,
          prefers_audio: prefersAudio,
        },
      });

      // Update conversation ID
      if (response.conversation_id) {
        setConversationId(response.conversation_id);
      }

      const audioUrl = response.audio_url ? normalizeUploadUrl(response.audio_url) : null;
      const assistantMessage: ChatMessage = {
        role: 'assistant' as const,
        content: response.text || 'Sem resposta',
        audioUrl: audioUrl,
      };

      setMessages([...newMessages, assistantMessage]);

      // Auto-play audio if user prefers audio or if last message was audio
      if (audioUrl && (prefersAudio || lastMessageWasAudio)) {
        setTimeout(() => {
          const audio = new Audio(audioUrl);
          audio.play().catch((err) => {
            console.error('Error auto-playing audio:', err);
          });
        }, 100);
      }
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message || 'Erro ao enviar mensagem. Tente novamente.');
      } else {
        setError('Erro ao enviar mensagem. Tente novamente.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleAudioRecording = async (audioBlob: Blob) => {
    try {
      setIsLoading(true);
      setError('');
      setLastMessageWasAudio(true); // Mark that we're sending audio

      // Upload audio file
      const presigned = await presignDocument({
        filename: `chat_audio_${Date.now()}.webm`,
        content_type: 'audio/webm',
      });

      // Upload blob to presigned URL (normalize to handle internal Docker URLs)
      const normalizedUploadUrl = normalizeUploadUrl(presigned.upload_url);
      await fetch(normalizedUploadUrl, {
        method: 'PUT',
        body: audioBlob,
        headers: {
          'Content-Type': 'audio/webm',
        },
      });

      // Add user message (indicating audio was sent)
      const newMessages: ChatMessage[] = [...messages, { 
        role: 'user' as const, 
        content: '🎤 Mensagem de áudio',
        audioUrl: presigned.file_url,
      }];
      setMessages(newMessages);

      // Send message with audio URL
      const response = await sendChatMessageV2({
        conversation_id: conversationId || undefined,
        input_type: 'audio',
        audio_url: presigned.file_url,
        locale: 'pt-BR',
        client_capabilities: {
          can_play_audio: true,
          prefers_audio: prefersAudio,
        },
      });

      // Update conversation ID
      if (response.conversation_id) {
        setConversationId(response.conversation_id);
      }

      const audioUrl = response.audio_url ? normalizeUploadUrl(response.audio_url) : null;
      const assistantMessage: ChatMessage = {
        role: 'assistant' as const,
        content: response.text || 'Sem resposta',
        audioUrl: audioUrl,
      };

      setMessages([...newMessages, assistantMessage]);

      // Auto-play audio if user prefers audio or if last message was audio
      if (audioUrl && (prefersAudio || lastMessageWasAudio)) {
        setTimeout(() => {
          const audio = new Audio(audioUrl);
          audio.play().catch((err) => {
            console.error('Error auto-playing audio:', err);
          });
        }, 100);
      }
      setLastMessageWasAudio(false); // Reset flag after response
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message || 'Erro ao processar áudio. Tente novamente.');
      } else {
        setError('Erro ao processar áudio. Tente novamente.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 bg-green-600 text-white rounded-full p-4 shadow-lg hover:bg-green-700 transition-all flex items-center gap-2 min-h-[56px] z-50"
        aria-label="Abrir ajuda"
      >
        <MessageCircle className="h-6 w-6" />
        <span className="font-bold text-base">Ajuda</span>
      </button>
    );
  }

  return (
    <div 
      className="fixed bottom-6 right-6 bg-white rounded-2xl shadow-2xl border border-slate-200/50 flex flex-col z-50 overflow-hidden backdrop-blur-sm"
      style={{ 
        width: 'min(400px, calc(100vw - 3rem))',
        maxWidth: '400px',
        height: '600px',
        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)'
      }}
    >
      <div className="bg-gradient-to-r from-green-600 to-green-500 text-white p-5 rounded-t-2xl flex items-center justify-between shadow-md">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center backdrop-blur-sm">
            <MessageCircle className="h-5 w-5" />
          </div>
          <span className="font-bold text-lg">Ajuda</span>
        </div>
        <button
          onClick={() => setIsOpen(false)}
          className="hover:bg-white/20 rounded-lg p-2 transition-all duration-200 hover:scale-110"
          aria-label="Fechar ajuda"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto overflow-x-hidden bg-gradient-to-b from-slate-50 to-white p-5 space-y-4">
        {messages.length === 0 && !isLoading && (
          <div className="flex flex-col py-4 animate-in fade-in slide-in-from-top-4 duration-500">
            <div className="mb-8 w-full text-center">
              <div className="w-20 h-20 bg-gradient-to-br from-green-100 to-green-50 rounded-full flex items-center justify-center mb-5 mx-auto shadow-lg ring-4 ring-green-50">
                <MessageCircle className="h-10 w-10 text-green-600" />
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-3 tracking-tight">
                Olá! Como posso ajudar?
              </h3>
              <p className="text-sm text-slate-600 mb-8 max-w-sm mx-auto leading-relaxed">
                Faça uma pergunta sobre o que você precisa fazer. Pode perguntar como se estivesse falando com um amigo!
              </p>
            </div>
            
            <div className="w-full space-y-3">
              <p className="text-xs font-semibold text-slate-500 mb-4 text-left uppercase tracking-wide">
                Perguntas frequentes:
              </p>
              {SUGGESTED_QUESTIONS.map((question, idx) => (
                <button
                  key={`suggestion-${idx}`}
                  onClick={() => {
                    handleSend(question.text);
                  }}
                  className="w-full text-left px-5 py-4 bg-white border border-slate-200 rounded-2xl hover:border-green-400 hover:bg-gradient-to-r hover:from-green-50 hover:to-emerald-50 transition-all duration-300 group active:scale-[0.97] shadow-sm hover:shadow-md hover:shadow-green-100"
                  disabled={isLoading}
                  type="button"
                  style={{ 
                    animationDelay: `${idx * 50}ms`,
                    animation: 'fadeInUp 0.5s ease-out forwards'
                  }}
                >
                  <div className="flex items-start gap-4">
                    <span className="text-2xl flex-shrink-0 transform group-hover:scale-110 transition-transform duration-300">
                      {question.icon}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-slate-800 group-hover:text-green-700 leading-snug mb-1">
                        {question.text}
                      </p>
                      <p className="text-xs text-slate-500 group-hover:text-green-600">
                        {question.description}
                      </p>
                    </div>
                    <span className="text-green-500 opacity-0 group-hover:opacity-100 transition-all duration-300 text-xl transform group-hover:translate-x-1 flex-shrink-0 mt-1">
                      →
                    </span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-in fade-in slide-in-from-bottom-2 duration-300`}
            style={{ animationDelay: `${idx * 50}ms` }}
          >
            <div
              className={`max-w-[85%] min-w-0 rounded-2xl px-4 py-3 text-sm shadow-sm ${
                msg.role === 'user'
                  ? 'bg-gradient-to-r from-green-600 to-green-500 text-white rounded-br-md'
                  : 'bg-white text-slate-800 border border-slate-200 rounded-bl-md'
              }`}
              style={{ wordBreak: 'break-word', overflowWrap: 'break-word' }}
            >
              <p className="whitespace-pre-wrap break-words leading-relaxed">{msg.content || 'Sem conteúdo'}</p>
              {msg.role === 'assistant' && msg.audioUrl && (
                <div className="mt-3 pt-3 border-t border-slate-200">
                  <AudioPlayer audioUrl={msg.audioUrl} />
                </div>
              )}
              {msg.role === 'assistant' && !msg.audioUrl && (
                <div className="mt-2">
                  <button
                    onClick={() => setPrefersAudio(!prefersAudio)}
                    className="text-xs text-slate-500 hover:text-green-600 font-medium transition-colors"
                  >
                    {prefersAudio ? '✓ Preferir áudio' : 'Preferir áudio'}
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start animate-in fade-in slide-in-from-left-2">
            <div className="bg-white border border-slate-200 rounded-2xl px-4 py-3 flex items-center gap-3 shadow-sm">
              <div className="flex gap-1.5">
                <span className="w-2 h-2 bg-green-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                <span className="w-2 h-2 bg-green-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                <span className="w-2 h-2 bg-green-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
              </div>
              <span className="text-sm text-slate-600 font-medium">Pensando...</span>
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border-l-4 border-red-500 rounded-xl p-4 text-sm text-red-700 shadow-sm animate-in slide-in-from-top-2">
            <p className="font-semibold mb-1">Erro</p>
            <p>{error}</p>
          </div>
        )}
      </div>

      <div className="border-t border-slate-200/80 bg-white/80 backdrop-blur-sm p-4 overflow-hidden">
        {/* Mode toggle */}
        <div className="flex gap-2 mb-3">
          <button
            onClick={() => setInputMode('text')}
            className={`flex-1 px-4 py-2 rounded-xl transition-all duration-200 flex items-center justify-center gap-2 ${
              inputMode === 'text'
                ? 'bg-green-100 text-green-700 font-medium shadow-sm'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            <Type className="h-4 w-4" />
            <span className="text-sm">Digitar</span>
          </button>
          <button
            onClick={() => setInputMode('audio')}
            className={`flex-1 px-4 py-2 rounded-xl transition-all duration-200 flex items-center justify-center gap-2 ${
              inputMode === 'audio'
                ? 'bg-green-100 text-green-700 font-medium shadow-sm'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            <Mic className="h-4 w-4" />
            <span className="text-sm">Gravar áudio</span>
          </button>
        </div>

        {/* Input area */}
        <div className="flex gap-3 min-w-0 items-center">
          {inputMode === 'audio' ? (
            <div className="flex-1 flex items-center justify-center">
              <AudioRecorder
                onRecordingComplete={handleAudioRecording}
                onError={(err) => setError(err.message)}
                disabled={isLoading}
              />
            </div>
          ) : (
            <>
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                placeholder="Pergunte como se estivesse falando com um amigo..."
                className="flex-1 min-w-0 px-5 py-3.5 bg-slate-50 border border-slate-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-green-500/20 focus:border-green-500 text-base transition-all duration-200 placeholder:text-slate-400"
                style={{ 
                  textOverflow: 'ellipsis',
                  overflow: 'hidden',
                  whiteSpace: 'nowrap',
                  maxWidth: '100%',
                  minHeight: '48px'
                }}
                disabled={isLoading}
              />
              <button
                onClick={() => handleSend()}
                disabled={!input.trim() || isLoading}
                className="bg-gradient-to-r from-green-600 to-green-500 text-white px-5 py-3.5 rounded-2xl hover:from-green-700 hover:to-green-600 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-md hover:shadow-lg transform hover:scale-105 active:scale-95 flex-shrink-0"
                aria-label="Enviar mensagem"
              >
                <Send className="h-5 w-5" />
              </button>
            </>
          )}
          <button
            onClick={() => setPrefersAudio(!prefersAudio)}
            className={`p-3 rounded-2xl transition-all duration-200 flex-shrink-0 ${
              prefersAudio
                ? 'bg-green-100 text-green-700 hover:bg-green-200'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
            title={prefersAudio ? 'Desativar preferência de áudio' : 'Ativar preferência de áudio'}
            aria-label={prefersAudio ? 'Desativar preferência de áudio' : 'Ativar preferência de áudio'}
          >
            {prefersAudio ? <Volume2 className="h-5 w-5" /> : <VolumeX className="h-5 w-5" />}
          </button>
        </div>
      </div>
    </div>
  );
}
