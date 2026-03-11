import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Shield, Sparkles, Send, Plus, Trash2, MessageSquare, ChevronLeft, Loader2, Bot, ExternalLink } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { aiAssistantAPI, forumAPI } from '@/lib/api';
import { toast } from 'sonner';
import Md from '@/components/Md';

const PERSONA_META = {
  ryai: { icon: Shield, color: '#F97316', label: 'RyAI', bg: 'rgba(249,115,22,0.12)' },
  zxai: { icon: Sparkles, color: '#10B981', label: 'zxAI', bg: 'rgba(16,185,129,0.12)' },
};

const AIAssistantPage = () => {
  const [sessions, setSessions] = useState([]);
  const [activeSession, setActiveSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [showSidebar, setShowSidebar] = useState(true);
  const [forumPostOpen, setForumPostOpen] = useState(false);
  const [forumPostTitle, setForumPostTitle] = useState('');
  const [forumPostContent, setForumPostContent] = useState('');
  const [forumPosting, setForumPosting] = useState(false);
  const [popularPrompts, setPopularPrompts] = useState([]);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Load sessions
  const loadSessions = useCallback(async () => {
    try {
      const r = await aiAssistantAPI.getSessions('adaptive');
      setSessions(r.data.sessions || []);
    } catch { /* ignore */ }
  }, []);

  useEffect(() => { loadSessions(); }, [loadSessions]);

  // Load popular prompts from both personas
  useEffect(() => {
    aiAssistantAPI.getPopularPrompts('ryai')
      .then(r => {
        const learned = (r.data.prompts || []).map(p => p.question);
        const defaults = [
          'How do I log my trades?',
          'What are the trading rules?',
          'How do commissions work?',
          'Why is consistency important?',
          'What benefits does CrossCurrent offer?',
          'How do I build good habits?',
        ];
        setPopularPrompts([...learned, ...defaults].slice(0, 6));
      })
      .catch(() => {
        setPopularPrompts([
          'How do I log my trades?',
          'What are the trading rules?',
          'How do commissions work?',
          'Why is consistency important?',
          'What benefits does CrossCurrent offer?',
          'How do I build good habits?',
        ]);
      });
  }, []);

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
    if (!input.trim() || sending) return;
    const msg = input.trim();
    setInput('');
    setSending(true);

    setMessages(prev => [...prev, { role: 'user', content: msg, created_at: new Date().toISOString() }]);

    try {
      const r = await aiAssistantAPI.chat({
        assistant_id: 'adaptive',
        message: msg,
        session_id: activeSession,
      });

      if (!activeSession) {
        setActiveSession(r.data.session_id);
        loadSessions();
      }

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: r.data.response,
        persona: r.data.persona || 'ryai',
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

  const isUncertainResponse = (content) => {
    const lc = content.toLowerCase();
    const phrases = [
      "i'm not sure", "i don't have", "i cannot", "i can't answer",
      "beyond my scope", "not able to", "don't have information",
      "unable to", "no information", "not equipped to",
      "recommend asking", "suggest reaching out", "community",
      "i don't know", "outside my", "no data on",
    ];
    return phrases.some(p => lc.includes(p));
  };

  const handlePostToForum = (userQuestion, aiResponse) => {
    setForumPostTitle(userQuestion.length > 100 ? userQuestion.substring(0, 100) + '...' : userQuestion);
    setForumPostContent(
      `**My Question:**\n${userQuestion}\n\n**AI Assistant Response:**\n> ${aiResponse.substring(0, 200)}...\n\nThe AI couldn't fully answer this. Can anyone from the community help?`
    );
    setForumPostOpen(true);
  };

  const handleSubmitForumPost = async () => {
    if (!forumPostTitle.trim() || !forumPostContent.trim()) {
      toast.error('Please fill in both title and content');
      return;
    }
    setForumPosting(true);
    try {
      await forumAPI.createPost({ title: forumPostTitle, content: forumPostContent, category: 'question' });
      toast.success('Posted to Community Forum! Check the forum for replies.');
      setForumPostOpen(false);
    } catch {
      toast.error('Failed to post to forum');
    } finally {
      setForumPosting(false);
    }
  };

  const renderPersonaIcon = (persona) => {
    const meta = PERSONA_META[persona] || PERSONA_META.ryai;
    const PIcon = meta.icon;
    return (
      <div className="w-7 h-7 rounded-lg flex-shrink-0 flex items-center justify-center mt-0.5" style={{ backgroundColor: meta.bg }}>
        <PIcon className="w-3.5 h-3.5" style={{ color: meta.color }} />
      </div>
    );
  };

  return (
    <>
    <div className="flex h-[calc(100vh-8rem)] md:h-[calc(100vh-6rem)] gap-0 -m-3 sm:-m-4 md:-m-6" data-testid="ai-assistant-page">
      {/* Sidebar - sessions */}
      <div className={`${showSidebar ? 'w-72' : 'w-0'} transition-all duration-200 overflow-hidden flex flex-col bg-[#0d0d0d] border-r border-[#1f1f1f]`}>
        {/* Header */}
        <div className="p-3 border-b border-[#1f1f1f]">
          <div className="flex items-center gap-2 px-2 py-1.5 mb-3">
            <Bot className="w-4 h-4 text-orange-400" />
            <span className="text-xs font-semibold text-white">CrossCurrent AI</span>
          </div>
          <Button onClick={handleNewChat} className="w-full h-9 text-xs bg-white/[0.06] hover:bg-white/[0.1] border border-white/[0.06] text-zinc-300 gap-2" data-testid="new-chat-btn">
            <Plus className="w-3.5 h-3.5" /> New Chat
          </Button>
        </div>

        {/* Sessions list */}
        <div className="flex-1 overflow-y-auto scrollbar-dark px-3 py-2 space-y-1">
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
        <div className="flex items-center gap-3 px-4 py-3 bg-[#0d0d0d] border-b border-[#1f1f1f]">
          <button onClick={() => setShowSidebar(!showSidebar)} className="text-zinc-500 hover:text-white transition-colors md:block hidden">
            <ChevronLeft className={`w-5 h-5 transition-transform ${!showSidebar ? 'rotate-180' : ''}`} />
          </button>
          <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ backgroundColor: 'rgba(249,115,22,0.15)' }}>
            <Bot className="w-4 h-4 text-orange-400" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-sm font-semibold text-white">CrossCurrent AI</h3>
            <p className="text-[11px] text-zinc-500 truncate">
              <span className="inline-flex items-center gap-1"><Shield className="w-3 h-3 text-orange-400" /> RyAI</span>
              <span className="text-zinc-700 mx-1.5">&</span>
              <span className="inline-flex items-center gap-1"><Sparkles className="w-3 h-3 text-emerald-400" /> zxAI</span>
              <span className="text-zinc-700 ml-1.5">— adapts to your needs</span>
            </p>
          </div>
        </div>

        {/* Messages area */}
        <div className="flex-1 overflow-y-auto scrollbar-dark px-4 py-4 space-y-4" data-testid="chat-messages">
          {messages.length === 0 && !activeSession && (
            <div className="flex flex-col items-center justify-center h-full max-w-lg mx-auto text-center">
              <div className="w-16 h-16 rounded-2xl flex items-center justify-center mb-4" style={{ backgroundColor: 'rgba(249,115,22,0.1)' }}>
                <Bot className="w-8 h-8 text-orange-400" />
              </div>
              <h2 className="text-xl font-bold text-white mb-1">CrossCurrent AI</h2>
              <p className="text-sm text-zinc-500 mb-2">Your adaptive assistant — powered by two specialized AI engines</p>
              <div className="flex items-center gap-4 mb-6">
                <div className="flex items-center gap-1.5 text-xs text-zinc-500">
                  <Shield className="w-3.5 h-3.5 text-orange-400" />
                  <span><span className="text-orange-400 font-medium">RyAI</span> — Platform Guide</span>
                </div>
                <div className="flex items-center gap-1.5 text-xs text-zinc-500">
                  <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
                  <span><span className="text-emerald-400 font-medium">zxAI</span> — Encouragement</span>
                </div>
              </div>

              {/* Quick prompts grid */}
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
              <p className="text-[10px] text-zinc-600 mt-3">The AI automatically detects which engine best serves your question</p>
            </div>
          )}

          {messages.map((m, i) => {
            const persona = m.persona || 'ryai';
            const meta = PERSONA_META[persona] || PERSONA_META.ryai;
            const isUncertain = m.role === 'assistant' && isUncertainResponse(m.content);
            const prevUserMsg = m.role === 'assistant' && i > 0 ? messages[i - 1] : null;

            return (
              <div key={i} className={`flex gap-3 ${m.role === 'user' ? 'justify-end' : ''}`}>
                {m.role === 'assistant' && renderPersonaIcon(persona)}
                <div className={`max-w-[75%] ${m.role === 'user' ? '' : ''}`}>
                  {m.role === 'assistant' && (
                    <span className="text-[10px] font-semibold ml-1 mb-0.5 block" style={{ color: meta.color }}>
                      {meta.label}
                    </span>
                  )}
                  <div className={`rounded-2xl px-4 py-2.5 text-sm ${
                    m.role === 'user'
                      ? 'bg-orange-500/15 text-zinc-100 rounded-br-md'
                      : 'bg-white/[0.05] text-zinc-200 rounded-bl-md'
                  }`}>
                    {m.role === 'assistant' ? <Md>{m.content}</Md> : m.content}
                  </div>
                  {isUncertain && prevUserMsg?.role === 'user' && (
                    <button
                      onClick={() => handlePostToForum(prevUserMsg.content, m.content)}
                      className="mt-1.5 ml-1 flex items-center gap-1.5 text-[11px] text-cyan-400 hover:text-cyan-300 transition-colors"
                      data-testid="post-to-forum-btn"
                    >
                      <ExternalLink className="w-3 h-3" /> Ask the Community Instead
                    </button>
                  )}
                </div>
              </div>
            );
          })}

          {sending && (
            <div className="flex gap-3">
              <div className="w-7 h-7 rounded-lg flex-shrink-0 flex items-center justify-center" style={{ backgroundColor: 'rgba(249,115,22,0.12)' }}>
                <Bot className="w-3.5 h-3.5 text-orange-400" />
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
        <div className="p-4 bg-[#0d0d0d] border-t border-[#1f1f1f]">
          <div className="flex gap-2 max-w-3xl mx-auto">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
              placeholder="Ask anything about CrossCurrent..."
              className="flex-1 rounded-xl px-4 py-3 text-sm text-white placeholder:text-gray-600 bg-[#1a1a1a] border border-[#2a2a2a] focus:border-orange-500/50 focus:outline-none transition-all"
              style={{ background: 'rgba(14,14,14,0.95)', border: '1px solid rgba(255,255,255,0.06)' }}
              disabled={sending}
              data-testid="chat-input"
            />
            <Button
              onClick={handleSend}
              disabled={!input.trim() || sending}
              className="h-auto px-4 rounded-xl text-white transition-all"
              style={{ backgroundColor: sending ? '#333' : '#F97316' }}
              data-testid="chat-send-btn"
            >
              {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            </Button>
          </div>
          <p className="text-[10px] text-zinc-600 text-center mt-2">AI responses are platform-specific. Not financial advice.</p>
        </div>
      </div>
    </div>

    {/* Forum Post Dialog */}
    <Dialog open={forumPostOpen} onOpenChange={setForumPostOpen}>
      <DialogContent className="glass-card border-[#222222] max-w-md">
        <DialogHeader>
          <DialogTitle className="text-white flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-cyan-400" /> Post to Community Forum
          </DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-2">
          <p className="text-xs text-zinc-500">The AI couldn't fully answer your question. Post it to the community forum where other members can help.</p>
          <div className="space-y-2">
            <label className="text-sm text-zinc-300 font-medium">Title</label>
            <Input
              value={forumPostTitle}
              onChange={(e) => setForumPostTitle(e.target.value)}
              placeholder="Brief summary of your question"
              className="bg-[#1a1a1a] border-white/[0.08] text-white"
              data-testid="forum-post-title"
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm text-zinc-300 font-medium">Content</label>
            <textarea
              value={forumPostContent}
              onChange={(e) => setForumPostContent(e.target.value)}
              placeholder="Describe your question in detail..."
              rows={6}
              className="w-full rounded-md bg-[#1a1a1a] border border-white/[0.08] text-white text-sm px-3 py-2 resize-none focus:outline-none focus:border-cyan-500/50"
              data-testid="forum-post-content"
            />
          </div>
          <div className="flex gap-3">
            <Button variant="outline" className="flex-1 border-white/[0.08]" onClick={() => setForumPostOpen(false)}>Cancel</Button>
            <Button
              className="flex-1 bg-cyan-600 hover:bg-cyan-500 text-white"
              onClick={handleSubmitForumPost}
              disabled={forumPosting || !forumPostTitle.trim()}
              data-testid="submit-forum-post"
            >
              {forumPosting ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : <MessageSquare className="w-4 h-4 mr-1" />}
              Post to Forum
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
    </>
  );
};

export default AIAssistantPage;
