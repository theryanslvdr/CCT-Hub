import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Shield, Sparkles, Send, Plus, Trash2, MessageSquare, Clock, ChevronLeft, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { aiAssistantAPI } from '@/lib/api';
import { toast } from 'sonner';
import Md from '@/components/Md';

const ICONS = { shield: Shield, sparkles: Sparkles };
const COLORS = { ryai: '#F97316', zxai: '#10B981' };

const AIAssistantPage = () => {
  const [assistants, setAssistants] = useState([]);
  const [activeAssistant, setActiveAssistant] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [activeSession, setActiveSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [showSidebar, setShowSidebar] = useState(true);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    aiAssistantAPI.listAssistants().then(r => {
      setAssistants(r.data.assistants || []);
      if (r.data.assistants?.length > 0) setActiveAssistant(r.data.assistants[0]);
    }).catch(() => toast.error('Failed to load assistants'));
  }, []);

  const loadSessions = useCallback(async (assistantId) => {
    try {
      const r = await aiAssistantAPI.getSessions(assistantId);
      setSessions(r.data.sessions || []);
    } catch { /* ignore */ }
  }, []);

  useEffect(() => {
    if (activeAssistant) loadSessions(activeAssistant.assistant_id);
  }, [activeAssistant, loadSessions]);

  const loadMessages = async (sessionId) => {
    try {
      const r = await aiAssistantAPI.getSessionMessages(sessionId);
      setMessages(r.data.messages || []);
    } catch { toast.error('Failed to load messages'); }
  };

  useEffect(() => {
    if (activeSession) loadMessages(activeSession);
  }, [activeSession]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || sending || !activeAssistant) return;
    const msg = input.trim();
    setInput('');
    setSending(true);

    // Optimistic user message
    setMessages(prev => [...prev, { role: 'user', content: msg, created_at: new Date().toISOString() }]);

    try {
      const r = await aiAssistantAPI.chat({
        assistant_id: activeAssistant.assistant_id,
        message: msg,
        session_id: activeSession,
      });

      if (!activeSession) {
        setActiveSession(r.data.session_id);
        loadSessions(activeAssistant.assistant_id);
      }

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: r.data.response,
        created_at: new Date().toISOString(),
      }]);
    } catch {
      toast.error('Failed to get response');
    } finally {
      setSending(false);
      inputRef.current?.focus();
    }
  };

  const handleNewChat = () => {
    setActiveSession(null);
    setMessages([]);
    inputRef.current?.focus();
  };

  const handleDeleteSession = async (sid, e) => {
    e.stopPropagation();
    try {
      await aiAssistantAPI.deleteSession(sid);
      setSessions(prev => prev.filter(s => s.id !== sid));
      if (activeSession === sid) { setActiveSession(null); setMessages([]); }
      toast.success('Chat deleted');
    } catch { toast.error('Delete failed'); }
  };

  const [popularPrompts, setPopularPrompts] = useState([]);

  const color = activeAssistant ? COLORS[activeAssistant.assistant_id] || '#F97316' : '#F97316';
  const Icon = activeAssistant ? ICONS[activeAssistant.icon] || MessageSquare : MessageSquare;

  // Load popular prompts from active learning
  useEffect(() => {
    if (!activeAssistant) return;
    aiAssistantAPI.getPopularPrompts(activeAssistant.assistant_id)
      .then(r => {
        const learned = (r.data.prompts || []).map(p => p.question);
        if (learned.length >= 4) {
          setPopularPrompts(learned.slice(0, 6));
        } else {
          // Fallback defaults
          const defaults = activeAssistant.assistant_id === 'ryai'
            ? ['How do I track my trades?', 'What are the trading rules?', 'How do commissions work?', 'Explain the profit tracker']
            : ['Why is consistency important?', 'How do I build good habits?', 'What benefits does CrossCurrent offer?', 'Tell me about rewards'];
          setPopularPrompts([...learned, ...defaults].slice(0, 6));
        }
      })
      .catch(() => {
        setPopularPrompts(activeAssistant.assistant_id === 'ryai'
          ? ['How do I track my trades?', 'What are the trading rules?', 'How do commissions work?', 'Explain the profit tracker']
          : ['Why is consistency important?', 'How do I build good habits?', 'What benefits does CrossCurrent offer?', 'Tell me about rewards']);
      });
  }, [activeAssistant]);

  return (
    <div className="flex h-[calc(100vh-8rem)] md:h-[calc(100vh-6rem)] gap-0 -m-3 sm:-m-4 md:-m-6" data-testid="ai-assistant-page">
      {/* Sidebar - sessions */}
      <div className={`${showSidebar ? 'w-72' : 'w-0'} transition-all duration-200 overflow-hidden flex flex-col`} style={{ background: 'rgba(8,8,8,0.95)', borderRight: '1px solid rgba(255,255,255,0.04)' }}>
        {/* Assistant selector tabs */}
        <div className="p-3 border-b border-white/[0.06] flex gap-1">
          {assistants.map(a => {
            const AIcon = ICONS[a.icon] || MessageSquare;
            const isActive = activeAssistant?.assistant_id === a.assistant_id;
            return (
              <button
                key={a.assistant_id}
                onClick={() => { setActiveAssistant(a); setActiveSession(null); setMessages([]); }}
                className={`flex-1 flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                  isActive ? 'bg-white/[0.08] text-white' : 'text-zinc-500 hover:text-zinc-300 hover:bg-white/[0.04]'
                }`}
                data-testid={`select-${a.assistant_id}`}
              >
                <AIcon className="w-3.5 h-3.5" style={{ color: COLORS[a.assistant_id] }} />
                {a.display_name}
              </button>
            );
          })}
        </div>

        {/* New chat button */}
        <div className="p-3">
          <Button onClick={handleNewChat} className="w-full h-9 text-xs bg-white/[0.06] hover:bg-white/[0.1] border border-white/[0.08] text-zinc-300 gap-2" data-testid="new-chat-btn">
            <Plus className="w-3.5 h-3.5" /> New Chat
          </Button>
        </div>

        {/* Sessions list */}
        <div className="flex-1 overflow-y-auto scrollbar-dark px-3 space-y-1">
          {sessions.map(s => (
            <button
              key={s.id}
              onClick={() => setActiveSession(s.id)}
              className={`w-full flex items-center gap-2 px-3 py-2.5 rounded-lg text-left text-sm transition-all group ${
                activeSession === s.id ? 'bg-white/[0.08] text-white' : 'text-zinc-400 hover:bg-white/[0.04] hover:text-zinc-200'
              }`}
              data-testid={`session-${s.id}`}
            >
              <MessageSquare className="w-3.5 h-3.5 flex-shrink-0 text-zinc-600" />
              <span className="truncate flex-1 text-xs">{s.title}</span>
              <Trash2
                className="w-3.5 h-3.5 text-zinc-600 opacity-0 group-hover:opacity-100 hover:text-red-400 transition-all flex-shrink-0"
                onClick={(e) => handleDeleteSession(s.id, e)}
              />
            </button>
          ))}
          {sessions.length === 0 && (
            <p className="text-xs text-zinc-600 text-center py-4">No conversations yet</p>
          )}
        </div>
      </div>

      {/* Main chat area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Chat header */}
        <div className="flex items-center gap-3 px-4 py-3" style={{ background: 'rgba(10,10,10,0.6)', borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
          <button onClick={() => setShowSidebar(!showSidebar)} className="text-zinc-500 hover:text-white transition-colors md:block hidden">
            <ChevronLeft className={`w-5 h-5 transition-transform ${!showSidebar ? 'rotate-180' : ''}`} />
          </button>
          <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ backgroundColor: `${color}20` }}>
            <Icon className="w-4 h-4" style={{ color }} />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-sm font-semibold text-white">{activeAssistant?.display_name || 'AI Assistant'}</h3>
            <p className="text-[11px] text-zinc-500 truncate">{activeAssistant?.tagline || ''}</p>
          </div>
        </div>

        {/* Messages area */}
        <div className="flex-1 overflow-y-auto scrollbar-dark px-4 py-4 space-y-4" data-testid="chat-messages">
          {messages.length === 0 && !activeSession && (
            <div className="flex flex-col items-center justify-center h-full max-w-lg mx-auto text-center">
              <div className="w-16 h-16 rounded-2xl flex items-center justify-center mb-4" style={{ backgroundColor: `${color}15` }}>
                <Icon className="w-8 h-8" style={{ color }} />
              </div>
              <h2 className="text-xl font-bold text-white mb-1">{activeAssistant?.display_name || 'AI Assistant'}</h2>
              <p className="text-sm text-zinc-500 mb-6">{activeAssistant?.greeting || 'How can I help you today?'}</p>

              {/* Quick prompts grid - powered by active learning */}
              <div className="grid grid-cols-2 gap-2 w-full">
                {popularPrompts.map((p, i) => (
                  <button
                    key={i}
                    onClick={() => { setInput(p); inputRef.current?.focus(); }}
                    className="p-3 rounded-xl border border-white/[0.06] bg-white/[0.02] hover:bg-white/[0.05] hover:border-white/[0.1] text-left text-xs text-zinc-400 hover:text-zinc-200 transition-all"
                    data-testid={`quick-prompt-${i}`}
                  >
                    {p}
                  </button>
                ))}
              </div>
              {popularPrompts.some((_, i) => i > 3) && (
                <p className="text-[10px] text-zinc-600 mt-2">Trending questions from the community</p>
              )}
            </div>
          )}

          {messages.map((m, i) => (
            <div key={i} className={`flex gap-3 ${m.role === 'user' ? 'justify-end' : ''}`}>
              {m.role === 'assistant' && (
                <div className="w-7 h-7 rounded-lg flex-shrink-0 flex items-center justify-center mt-0.5" style={{ backgroundColor: `${color}20` }}>
                  <Icon className="w-3.5 h-3.5" style={{ color }} />
                </div>
              )}
              <div className={`max-w-[75%] rounded-2xl px-4 py-2.5 text-sm ${
                m.role === 'user'
                  ? 'bg-orange-500/15 text-zinc-100 rounded-br-md'
                  : 'bg-white/[0.05] text-zinc-200 rounded-bl-md'
              }`}>
                {m.role === 'assistant' ? <Md>{m.content}</Md> : m.content}
              </div>
            </div>
          ))}

          {sending && (
            <div className="flex gap-3">
              <div className="w-7 h-7 rounded-lg flex-shrink-0 flex items-center justify-center" style={{ backgroundColor: `${color}20` }}>
                <Icon className="w-3.5 h-3.5" style={{ color }} />
              </div>
              <div className="bg-white/[0.05] rounded-2xl rounded-bl-md px-4 py-3">
                <div className="flex gap-1">
                  <div className="w-2 h-2 rounded-full bg-zinc-500 animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-2 h-2 rounded-full bg-zinc-500 animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-2 h-2 rounded-full bg-zinc-500 animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input area */}
        <div className="p-4" style={{ background: 'rgba(10,10,10,0.6)', borderTop: '1px solid rgba(255,255,255,0.04)' }}>
          <div className="flex gap-2 max-w-3xl mx-auto">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
              placeholder={`Ask ${activeAssistant?.display_name || 'AI'}...`}
              className="flex-1 rounded-xl px-4 py-3 text-sm text-white placeholder:text-zinc-600 focus:border-orange-500/30 focus:ring-1 focus:ring-orange-500/20 focus:outline-none transition-all"
              style={{ background: 'rgba(14,14,14,0.95)', border: '1px solid rgba(255,255,255,0.06)' }}
              disabled={sending}
              data-testid="chat-input"
            />
            <Button
              onClick={handleSend}
              disabled={!input.trim() || sending}
              className="h-auto px-4 rounded-xl text-white transition-all"
              style={{ backgroundColor: sending ? '#333' : color }}
              data-testid="chat-send-btn"
            >
              {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            </Button>
          </div>
          <p className="text-[10px] text-zinc-600 text-center mt-2">AI responses are platform-specific. Not financial advice.</p>
        </div>
      </div>
    </div>
  );
};

export default AIAssistantPage;
