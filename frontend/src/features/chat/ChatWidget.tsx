import { useEffect, useRef, useState } from 'react';
import { MessageSquare, Send, X } from 'lucide-react';
import type { ChatMessageResponseNew, ConversationState } from '../../services/api/chat';
import { sendChatMessageV2 } from '../../services/api/chat';
import { ApiClientError } from '../../services/api/client';
import { AudioRecorder } from './AudioRecorder';
import { AudioPlayer } from './AudioPlayer';
import { SuggestedActions } from './SuggestedActions';
import { ChatStatusIndicator } from './ChatStatusIndicator';
import { presignDocument } from '../../services/api/documents';
import { normalizeUploadUrl } from '../../services/api/client';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  audioUrl?: string | null;
  suggestedActions?: ChatMessageResponseNew['suggested_actions'];
  conversationState?: ConversationState;
}

const SUGGESTED_QUESTIONS = [
  "O que falta para eu me formalizar?",
  "Como consigo vender para as escolas?",
  "Preciso de CPF para participar?",
  "O que é DAP e como tirar?",
  "Quanto posso ganhar vendendo para o PNAE?",
];

console.log('📝 SUGGESTED_QUESTIONS loaded:', SUGGESTED_QUESTIONS.length, 'questions');

export function ChatWidget({ userName }: { userName: string }) {
  console.log('🚀 ChatWidget RENDERED', { userName });
  
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [prefersAudio, setPrefersAudio] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  console.log('📊 ChatWidget STATE:', { 
    isOpen, 
    messagesCount: messages.length, 
    isTyping,
    shouldShowEmpty: messages.length === 0 && !isTyping 
  });

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isOpen]);

  useEffect(() => {
    const shouldShowEmpty = messages.length === 0 && !isTyping;
    console.log('🔍 ChatWidget Debug:', {
      isOpen,
      messagesCount: messages.length,
      isTyping,
      shouldShowEmpty,
      messages: messages.map(m => ({ id: m.id, role: m.role, contentLength: m.content?.length || 0 }))
    });
    if (shouldShowEmpty) {
      console.log('✅ Should show empty state with', SUGGESTED_QUESTIONS.length, 'suggestions');
    }
  }, [isOpen, messages.length, isTyping, messages]);

  const handleSend = async (text?: string) => {
    const prompt = text || inputValue.trim();
    if (!prompt || isTyping) return;

    const newMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: prompt,
    };
    setMessages((prev) => [...prev, newMsg]);
    setInputValue('');
    setIsTyping(true);
    setError(null);

    try {
      const response = await sendChatMessageV2({
        conversation_id: conversationId || undefined,
        input_type: 'text',
        text: prompt,
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

      // Ensure text is always a string - support both new (text) and legacy (content) formats
      const responseText = String(
        (response as any).text || 
        (response as any).content || 
        ''
      );
      
      if (!responseText) {
        console.error('Empty response text:', response);
        setError('Resposta vazia do servidor. Tente novamente.');
        return;
      }
      
      const replyMsg: ChatMessage = {
        id: response.message_id,
        role: 'assistant',
        content: responseText,
        audioUrl: response.audio_url || null,
        suggestedActions: response.suggested_actions || [],
        conversationState: response.conversation_state,
      };
      
      console.log('Adding assistant message:', {
        id: replyMsg.id,
        contentLength: replyMsg.content.length,
        contentPreview: replyMsg.content.substring(0, 100),
        hasContent: !!replyMsg.content,
        responseObject: response,
      });
      
      setMessages((prev) => {
        const newMessages = [...prev, replyMsg];
        console.log('Updated messages count:', newMessages.length);
        return newMessages;
      });

      // Auto-play audio if user prefers audio
      if (prefersAudio && response.audio_url) {
        setTimeout(() => {
          const audio = new Audio(response.audio_url!);
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

      // Add error message to chat
      const errorMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content:
          'Desculpe, ocorreu um erro ao processar sua mensagem. Por favor, tente novamente ou consulte a Emater para mais informações.',
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleAudioRecording = async (audioBlob: Blob) => {
    try {
      setIsTyping(true);
      setError(null);

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

      const replyMsg: ChatMessage = {
        id: response.message_id,
        role: 'assistant',
        content: response.text || 'Sem resposta',
        audioUrl: response.audio_url || null,
        suggestedActions: response.suggested_actions || [],
        conversationState: response.conversation_state,
      };
      setMessages((prev) => [...prev, replyMsg]);

      // Auto-play audio if user prefers audio
      if (prefersAudio && response.audio_url) {
        setTimeout(() => {
          const audio = new Audio(response.audio_url!);
          audio.play().catch((err) => {
            console.error('Error auto-playing audio:', err);
          });
        }, 100);
      }
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message || 'Erro ao processar áudio. Tente novamente.');
      } else {
        setError('Erro ao processar áudio. Tente novamente.');
      }
    } finally {
      setIsTyping(false);
    }
  };

  const handleActionExecuted = (action: ChatMessageResponseNew['suggested_actions'][0]) => {
    // Show success feedback
    if (action.type === 'mark_task_done') {
      const successMsg: ChatMessage = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `✅ Tarefa "${action.task_code}" marcada como concluída! Parabéns! 🎉`,
      };
      setMessages((prev) => [...prev, successMsg]);

      // Scroll to bottom to show success message
      setTimeout(() => {
        scrollToBottom();
      }, 100);
    }
  };

  return (
    <>
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 bg-green-600 hover:bg-green-700 text-white p-4 rounded-full shadow-lg transition-transform hover:scale-110 z-50 flex items-center justify-center group"
          aria-label="Abrir chat"
        >
          <MessageSquare className="h-6 w-6" />
          <span className="absolute right-full mr-3 bg-white text-slate-700 px-3 py-1 rounded-lg text-sm font-bold shadow-md opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
            Tirar dúvidas
          </span>
        </button>
      )}

      {isOpen && (
        <div
          className="fixed bottom-6 right-6 bg-white rounded-2xl shadow-2xl border border-slate-200 z-50 flex flex-col animate-in slide-in-from-bottom-10 fade-in duration-300"
          style={{ 
            height: '500px', 
            width: 'min(384px, calc(100vw - 3rem))',
            maxWidth: '384px',
            overflow: 'hidden',
            boxSizing: 'border-box',
            display: 'flex',
            flexDirection: 'column'
          }}
        >
          <div className="bg-primary-500 p-4 flex justify-between items-center text-white rounded-t-2xl" style={{ flexShrink: 0 }}>
            <div className="flex items-center gap-2 flex-1 min-w-0">
              <img src="/logo.png" alt="Abrindo porteiras" className="h-5 w-5 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <h3 className="font-bold text-sm">Ajuda Abrindo porteiras</h3>
                <div className="flex items-center gap-2 mt-1">
                  <span className="w-1.5 h-1.5 bg-primary-300 rounded-full animate-pulse"></span>
                  <span className="text-[10px] opacity-90">Online</span>
                  {messages.length > 1 && messages[messages.length - 1]?.conversationState && (
                    <ChatStatusIndicator
                      state={messages[messages.length - 1].conversationState!.chat_state}
                      currentTaskCode={messages[messages.length - 1].conversationState!.current_task_code}
                      className="ml-2"
                    />
                  )}
                </div>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="hover:bg-primary-600 p-1 rounded transition"
              aria-label="Fechar chat"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto overflow-x-hidden bg-slate-50" style={{ 
            minHeight: 0
          }}>
            {messages.length === 0 && !isTyping ? (
              <div className="flex flex-col py-6 px-4">
                <div className="mb-6 w-full text-center">
                  <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4 mx-auto">
                    <MessageSquare className="h-8 w-8 text-green-600" />
                  </div>
                  <h3 className="text-lg font-semibold text-slate-800 mb-2">
                    Olá! Como posso ajudar?
                  </h3>
                  <p className="text-sm text-slate-600 mb-6 max-w-sm mx-auto">
                    Faça uma pergunta sobre o que você precisa fazer. Pode perguntar como se estivesse falando com um amigo!
                  </p>
                </div>
                
                <div className="w-full space-y-2">
                  <p className="text-xs font-medium text-slate-500 mb-3 text-left">
                    Sugestões de perguntas:
                  </p>
                  {SUGGESTED_QUESTIONS.length > 0 ? (
                    SUGGESTED_QUESTIONS.map((question, idx) => (
                      <button
                        key={`suggestion-${idx}`}
                        onClick={() => {
                          console.log('✅ Clicked suggestion:', question);
                          handleSend(question);
                        }}
                        className="w-full text-left px-4 py-3 bg-white border-2 border-slate-200 rounded-xl hover:border-green-500 hover:bg-green-50 transition-all text-sm text-slate-700 hover:text-green-700 group active:scale-[0.98] shadow-sm"
                        disabled={isTyping}
                        type="button"
                      >
                        <span className="flex items-center gap-2">
                          <span className="text-green-600 opacity-0 group-hover:opacity-100 transition-opacity text-base">💬</span>
                          <span className="flex-1">{question}</span>
                          <span className="text-green-600 opacity-0 group-hover:opacity-100 transition-opacity text-lg">
                            →
                          </span>
                        </span>
                      </button>
                    ))
                  ) : (
                    <p className="text-xs text-red-500">⚠️ Nenhuma sugestão disponível</p>
                  )}
                </div>
              </div>
            ) : null}
            
            {messages.length > 0 && (
              <div className="p-4 pb-4 space-y-4">
                {error && (
              <div
                className="bg-red-50 border-l-4 border-red-500 rounded-lg p-4 text-sm text-red-700 flex items-start gap-2 animate-in slide-in-from-top-2"
                role="alert"
              >
                <svg
                  className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                  aria-hidden="true"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clipRule="evenodd"
                  />
                </svg>
                <div className="flex-1">
                  <p className="font-semibold">Erro</p>
                  <p>{error}</p>
                </div>
                <button
                  onClick={() => setError(null)}
                  className="text-red-500 hover:text-red-700 flex-shrink-0"
                  aria-label="Fechar erro"
                >
                  <X className="h-4 w-4" />
                </button>
                </div>
              )}

              {messages.length > 0 && messages.map((msg) => {
              // Ensure content is always a string
              const content = String(msg.content || '');
              
              // Debug log for empty messages
              if (!content && msg.role === 'assistant') {
                console.warn('Empty assistant message:', msg);
              }
              
              return (
                <div
                  key={msg.id}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} w-full`}
                >
                  <div
                    className={`max-w-[85%] min-w-0 rounded-2xl p-3 text-base relative group ${
                      msg.role === 'user'
                        ? 'bg-primary-500 text-white rounded-br-none'
                        : 'bg-white text-slate-700 shadow-sm border border-slate-100 rounded-bl-none'
                    }`}
                    style={{ 
                      wordBreak: 'break-word', 
                      overflowWrap: 'break-word',
                      overflow: 'hidden'
                    }}
                  >
                    {content ? (
                      <p 
                        className="text-base leading-relaxed whitespace-pre-wrap"
                        style={{ 
                          wordBreak: 'break-word',
                          overflowWrap: 'break-word',
                          hyphens: 'auto',
                          margin: 0,
                          padding: 0
                        }}
                      >
                        {content}
                      </p>
                    ) : (
                      <p className="text-base leading-relaxed text-slate-400 italic m-0 p-0">
                        Carregando mensagem...
                      </p>
                    )}

                  {msg.role === 'assistant' && (
                    <div className="mt-3 space-y-2 border-t border-slate-100 pt-2">
                      {msg.audioUrl && (
                        <AudioPlayer audioUrl={msg.audioUrl} className="justify-start" />
                      )}
                      {!msg.audioUrl && (
                        <button
                          onClick={() => setPrefersAudio(!prefersAudio)}
                          className="text-xs text-primary-500 hover:text-primary-600 font-medium"
                        >
                          {prefersAudio ? '✓ Preferir áudio' : 'Preferir áudio'}
                        </button>
                      )}
                      {msg.suggestedActions && msg.suggestedActions.length > 0 && (
                        <SuggestedActions
                          actions={msg.suggestedActions}
                          onActionExecuted={handleActionExecuted}
                          onError={(err) => setError(err.message)}
                        />
                      )}
                    </div>
                  )}
                  </div>
                </div>
              );
            })}

            {isTyping && (
              <div className="flex justify-start animate-in fade-in slide-in-from-left-2">
                <div className="bg-primary-50 border border-primary-200 rounded-2xl px-4 py-3 flex items-center gap-3">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-primary-500 rounded-full animate-bounce"></span>
                    <span className="w-2 h-2 bg-primary-500 rounded-full animate-bounce delay-75"></span>
                    <span className="w-2 h-2 bg-primary-500 rounded-full animate-bounce delay-150"></span>
                  </div>
                  <span className="text-xs text-primary-700 font-medium">Pensando...</span>
                </div>
                </div>
              )}
              {messages.length > 0 && <div ref={messagesEndRef} />}
              </div>
            )}
          </div>

          <div className="bg-white border-t border-slate-100 rounded-b-2xl" style={{ 
            padding: '12px',
            paddingBottom: '12px',
            overflow: 'hidden', 
            boxSizing: 'border-box',
            flexShrink: 0,
            height: '68px'
          }}>
            <div className="flex gap-2 items-center" style={{ 
              width: '100%', 
              minWidth: 0, 
              maxWidth: '100%', 
              boxSizing: 'border-box',
              gap: '8px'
            }}>
              <div style={{ flexShrink: 0 }}>
                <AudioRecorder
                  onRecordingComplete={handleAudioRecording}
                  onError={(err) => setError(err.message)}
                  disabled={isTyping}
                />
              </div>

              <div className="relative" style={{ 
                flex: '1 1 0%', 
                minWidth: 0, 
                maxWidth: '100%',
                overflow: 'visible',
                height: '44px'
              }}>
                <input
                  type="text"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                  placeholder="Pergunte como se estivesse falando com um amigo..."
                  className="w-full h-11 pl-4 pr-10 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-green-500 text-sm"
                  style={{ 
                    textOverflow: 'ellipsis',
                    overflow: 'hidden',
                    whiteSpace: 'nowrap',
                    width: '100%',
                    height: '44px',
                    boxSizing: 'border-box',
                    paddingRight: '2.5rem'
                  }}
                  disabled={isTyping}
                  aria-label="Digite sua mensagem"
                  maxLength={500}
                />
                <button
                  onClick={() => handleSend()}
                  disabled={!inputValue.trim() || isTyping}
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 text-green-600 hover:bg-green-100 rounded-lg disabled:opacity-50 disabled:hover:bg-transparent transition"
                  aria-label="Enviar mensagem"
                  style={{ 
                    flexShrink: 0,
                    zIndex: 10
                  }}
                >
                  <Send className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
