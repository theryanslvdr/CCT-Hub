import React, { useState, useEffect, useCallback } from 'react';
import { Shield, Sparkles, MessageSquare, Brain, BookOpen, HelpCircle, Plus, Trash2, Save, Send, BarChart3, RefreshCw } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { aiAssistantAPI } from '@/lib/api';
import { toast } from 'sonner';

const ICONS = { shield: Shield, sparkles: Sparkles };
const COLORS = { ryai: '#F97316', zxai: '#10B981' };
const TABS = [
  { id: 'config', label: 'Personality', icon: Brain },
  { id: 'knowledge', label: 'Knowledge Base', icon: BookOpen },
  { id: 'unanswered', label: 'Unanswered', icon: HelpCircle },
  { id: 'stats', label: 'Analytics', icon: BarChart3 },
];

const AITrainingPage = () => {
  const [assistants, setAssistants] = useState([]);
  const [activeBot, setActiveBot] = useState('ryai');
  const [activeTab, setActiveTab] = useState('config');
  const [config, setConfig] = useState({});
  const [knowledge, setKnowledge] = useState([]);
  const [unanswered, setUnanswered] = useState([]);
  const [stats, setStats] = useState({});
  const [saving, setSaving] = useState(false);
  const [showAddKB, setShowAddKB] = useState(false);
  const [kbForm, setKbForm] = useState({ category: '', question: '', answer: '' });
  const [answerModal, setAnswerModal] = useState(null);
  const [adminAnswer, setAdminAnswer] = useState('');

  const loadData = useCallback(async () => {
    try {
      const [configRes, kbRes, uaRes, statsRes] = await Promise.all([
        aiAssistantAPI.getAdminConfig(),
        aiAssistantAPI.getKnowledge(activeBot),
        aiAssistantAPI.getUnanswered(activeBot),
        aiAssistantAPI.getStats(),
      ]);
      setAssistants(configRes.data.assistants || []);
      const active = (configRes.data.assistants || []).find(a => a.assistant_id === activeBot);
      if (active) setConfig(active);
      setKnowledge(kbRes.data.entries || []);
      setUnanswered(uaRes.data.items || []);
      setStats(statsRes.data || {});
    } catch { toast.error('Failed to load data'); }
  }, [activeBot]);

  useEffect(() => { loadData(); }, [loadData]);

  const handleSaveConfig = async () => {
    setSaving(true);
    try {
      await aiAssistantAPI.updateConfig(activeBot, {
        display_name: config.display_name,
        system_prompt: config.system_prompt,
        personality: config.personality,
        greeting: config.greeting,
        tagline: config.tagline,
        model: config.model,
      });
      toast.success('Configuration saved');
    } catch { toast.error('Save failed'); }
    setSaving(false);
  };

  const handleAddKB = async () => {
    if (!kbForm.category || !kbForm.question || !kbForm.answer) return toast.error('All fields required');
    try {
      await aiAssistantAPI.addTraining({ assistant_id: activeBot, ...kbForm });
      setShowAddKB(false);
      setKbForm({ category: '', question: '', answer: '' });
      loadData();
      toast.success('Knowledge added');
    } catch { toast.error('Failed to add'); }
  };

  const handleDeleteKB = async (id) => {
    try {
      await aiAssistantAPI.deleteKnowledge(id);
      setKnowledge(prev => prev.filter(e => e.id !== id));
      toast.success('Entry deleted');
    } catch { toast.error('Delete failed'); }
  };

  const handleAnswer = async () => {
    if (!adminAnswer.trim() || !answerModal) return;
    try {
      await aiAssistantAPI.answerUnanswered(answerModal.id, adminAnswer);
      setAnswerModal(null);
      setAdminAnswer('');
      loadData();
      toast.success('Answered & added to knowledge base');
    } catch { toast.error('Failed to answer'); }
  };

  const color = COLORS[activeBot] || '#F97316';
  const Icon = ICONS[assistants.find(a => a.assistant_id === activeBot)?.icon] || MessageSquare;

  return (
    <div className="space-y-6" data-testid="ai-training-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">AI Training Center</h1>
          <p className="text-sm text-zinc-500 mt-1">Configure and train your AI assistants</p>
        </div>
        <Button onClick={loadData} variant="ghost" size="sm" className="text-zinc-400 gap-2">
          <RefreshCw className="w-4 h-4" /> Refresh
        </Button>
      </div>

      {/* Bot selector */}
      <div className="flex gap-3">
        {assistants.map(a => {
          const AIcon = ICONS[a.icon] || MessageSquare;
          const isActive = activeBot === a.assistant_id;
          const c = COLORS[a.assistant_id] || '#F97316';
          return (
            <button
              key={a.assistant_id}
              onClick={() => setActiveBot(a.assistant_id)}
              className={`flex items-center gap-3 px-5 py-3 rounded-xl border transition-all ${
                isActive ? 'border-white/[0.12] bg-white/[0.06]' : 'border-white/[0.06] bg-transparent hover:bg-white/[0.03]'
              }`}
              data-testid={`bot-selector-${a.assistant_id}`}
            >
              <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ backgroundColor: `${c}20` }}>
                <AIcon className="w-5 h-5" style={{ color: c }} />
              </div>
              <div className="text-left">
                <p className={`text-sm font-semibold ${isActive ? 'text-white' : 'text-zinc-400'}`}>{a.display_name}</p>
                <p className="text-[11px] text-zinc-600">{a.tagline}</p>
              </div>
            </button>
          );
        })}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-[#111111] p-1 rounded-xl border border-white/[0.06] w-fit">
        {TABS.map(t => {
          const TIcon = t.icon;
          return (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-medium transition-all ${
                activeTab === t.id ? 'bg-white/[0.08] text-white' : 'text-zinc-500 hover:text-zinc-300'
              }`}
              data-testid={`tab-${t.id}`}
            >
              <TIcon className="w-3.5 h-3.5" />
              {t.label}
              {t.id === 'unanswered' && unanswered.length > 0 && (
                <span className="ml-1 px-1.5 py-0.5 rounded-full bg-red-500/20 text-red-400 text-[10px]">{unanswered.length}</span>
              )}
            </button>
          );
        })}
      </div>

      {/* Personality Config */}
      {activeTab === 'config' && (
        <Card className="glass-card p-6 space-y-5">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div>
              <Label className="text-zinc-400 text-xs uppercase tracking-wider">Display Name</Label>
              <Input value={config.display_name || ''} onChange={e => setConfig(p => ({...p, display_name: e.target.value}))} className="mt-1.5 bg-[#0a0a0a] border-white/[0.06] text-white" data-testid="config-display-name" />
            </div>
            <div>
              <Label className="text-zinc-400 text-xs uppercase tracking-wider">Tagline</Label>
              <Input value={config.tagline || ''} onChange={e => setConfig(p => ({...p, tagline: e.target.value}))} className="mt-1.5 bg-[#0a0a0a] border-white/[0.06] text-white" data-testid="config-tagline" />
            </div>
            <div>
              <Label className="text-zinc-400 text-xs uppercase tracking-wider">AI Model</Label>
              <Input value={config.model || ''} onChange={e => setConfig(p => ({...p, model: e.target.value}))} className="mt-1.5 bg-[#0a0a0a] border-white/[0.06] text-white font-mono text-xs" placeholder="openai/gpt-4o-mini" data-testid="config-model" />
              <p className="text-[10px] text-zinc-600 mt-1">OpenRouter model identifier</p>
            </div>
            <div>
              <Label className="text-zinc-400 text-xs uppercase tracking-wider">Personality Traits</Label>
              <Input value={config.personality || ''} onChange={e => setConfig(p => ({...p, personality: e.target.value}))} className="mt-1.5 bg-[#0a0a0a] border-white/[0.06] text-white" data-testid="config-personality" />
            </div>
          </div>
          <div>
            <Label className="text-zinc-400 text-xs uppercase tracking-wider">System Prompt</Label>
            <Textarea value={config.system_prompt || ''} onChange={e => setConfig(p => ({...p, system_prompt: e.target.value}))} rows={6} className="mt-1.5 bg-[#0a0a0a] border-white/[0.06] text-white text-sm resize-none" data-testid="config-system-prompt" />
            <p className="text-[10px] text-zinc-600 mt-1">Core instructions that define the AI's behavior and responses</p>
          </div>
          <div>
            <Label className="text-zinc-400 text-xs uppercase tracking-wider">Greeting Message</Label>
            <Textarea value={config.greeting || ''} onChange={e => setConfig(p => ({...p, greeting: e.target.value}))} rows={3} className="mt-1.5 bg-[#0a0a0a] border-white/[0.06] text-white text-sm resize-none" data-testid="config-greeting" />
          </div>
          <Button onClick={handleSaveConfig} disabled={saving} className="bg-orange-500 hover:bg-orange-400 text-white gap-2" data-testid="save-config-btn">
            <Save className="w-4 h-4" /> {saving ? 'Saving...' : 'Save Configuration'}
          </Button>
        </Card>
      )}

      {/* Knowledge Base */}
      {activeTab === 'knowledge' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-zinc-400">{knowledge.length} entries</p>
            <Button onClick={() => setShowAddKB(true)} className="bg-orange-500 hover:bg-orange-400 text-white gap-2 h-9 text-xs" data-testid="add-knowledge-btn">
              <Plus className="w-3.5 h-3.5" /> Add Knowledge
            </Button>
          </div>
          <div className="space-y-2">
            {knowledge.map(entry => (
              <Card key={entry.id} className="glass-card p-4" data-testid={`kb-entry-${entry.id}`}>
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/[0.06] text-zinc-400">{entry.category}</span>
                    </div>
                    <p className="text-sm text-white font-medium">{entry.question}</p>
                    <p className="text-xs text-zinc-400 mt-1 line-clamp-2">{entry.answer}</p>
                  </div>
                  <button onClick={() => handleDeleteKB(entry.id)} className="text-zinc-600 hover:text-red-400 transition-colors p-1">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </Card>
            ))}
            {knowledge.length === 0 && (
              <div className="text-center py-12 text-zinc-600 text-sm">
                <BookOpen className="w-8 h-8 mx-auto mb-2 opacity-50" />
                No knowledge entries yet. Add some to train the AI.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Unanswered Questions */}
      {activeTab === 'unanswered' && (
        <div className="space-y-3">
          {unanswered.map(item => (
            <Card key={item.id} className="glass-card p-4" data-testid={`unanswered-${item.id}`}>
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1">
                  <p className="text-sm text-white font-medium">{item.question}</p>
                  <p className="text-[11px] text-zinc-500 mt-1">Asked by: {item.user_name}</p>
                  {item.ai_attempted_response && (
                    <div className="mt-2 p-2 rounded-lg bg-amber-500/5 border border-amber-500/10">
                      <p className="text-[10px] text-amber-400 mb-1">AI's attempted response:</p>
                      <p className="text-xs text-zinc-400">{item.ai_attempted_response.replace('[ESCALATE]', '').trim()}</p>
                    </div>
                  )}
                </div>
                <Button size="sm" onClick={() => { setAnswerModal(item); setAdminAnswer(''); }} className="h-8 text-xs bg-orange-500 hover:bg-orange-400 text-white gap-1" data-testid={`answer-btn-${item.id}`}>
                  <Send className="w-3 h-3" /> Answer
                </Button>
              </div>
            </Card>
          ))}
          {unanswered.length === 0 && (
            <div className="text-center py-12 text-zinc-600 text-sm">
              <HelpCircle className="w-8 h-8 mx-auto mb-2 opacity-50" />
              No unanswered questions. The AI is handling everything!
            </div>
          )}
        </div>
      )}

      {/* Stats */}
      {activeTab === 'stats' && (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {[
            { label: 'Total Sessions', value: stats.total_sessions, color: '#F97316' },
            { label: 'Total Messages', value: stats.total_messages, color: '#10B981' },
            { label: 'Knowledge Entries', value: stats.knowledge_entries, color: '#8B5CF6' },
            { label: 'Pending Answers', value: stats.pending_unanswered, color: '#EF4444' },
            { label: 'Total Interactions', value: stats.total_interactions, color: '#F59E0B' },
            { label: 'Escalation Rate', value: `${stats.escalation_rate || 0}%`, color: '#EC4899' },
          ].map((s, i) => (
            <Card key={i} className="glass-card p-4">
              <p className="text-[11px] text-zinc-500 uppercase tracking-wider">{s.label}</p>
              <p className="text-2xl font-bold font-mono mt-1" style={{ color: s.color }}>{s.value ?? 0}</p>
            </Card>
          ))}
        </div>
      )}

      {/* Add Knowledge Dialog */}
      <Dialog open={showAddKB} onOpenChange={setShowAddKB}>
        <DialogContent className="bg-[#111111] border-white/[0.08]">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Plus className="w-5 h-5" style={{ color }} /> Add Knowledge Entry
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-2">
            <div>
              <Label className="text-zinc-400 text-xs uppercase tracking-wider">Category</Label>
              <Input value={kbForm.category} onChange={e => setKbForm(p => ({...p, category: e.target.value}))} placeholder="e.g. Platform, Trading, Rewards" className="mt-1 bg-[#0a0a0a] border-white/[0.06] text-white" data-testid="kb-category-input" />
            </div>
            <div>
              <Label className="text-zinc-400 text-xs uppercase tracking-wider">Question / Topic</Label>
              <Input value={kbForm.question} onChange={e => setKbForm(p => ({...p, question: e.target.value}))} placeholder="What is the user likely to ask?" className="mt-1 bg-[#0a0a0a] border-white/[0.06] text-white" data-testid="kb-question-input" />
            </div>
            <div>
              <Label className="text-zinc-400 text-xs uppercase tracking-wider">Answer</Label>
              <Textarea value={kbForm.answer} onChange={e => setKbForm(p => ({...p, answer: e.target.value}))} rows={4} placeholder="The correct answer the AI should give" className="mt-1 bg-[#0a0a0a] border-white/[0.06] text-white text-sm resize-none" data-testid="kb-answer-input" />
            </div>
            <Button onClick={handleAddKB} className="w-full bg-orange-500 hover:bg-orange-400 text-white" data-testid="submit-kb-btn">Add to Knowledge Base</Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Answer Unanswered Dialog */}
      <Dialog open={!!answerModal} onOpenChange={() => setAnswerModal(null)}>
        <DialogContent className="bg-[#111111] border-white/[0.08]">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Send className="w-5 h-5" style={{ color }} /> Answer & Train
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-2">
            <div className="p-3 rounded-lg bg-white/[0.03] border border-white/[0.06]">
              <p className="text-xs text-zinc-500 mb-1">User asked:</p>
              <p className="text-sm text-white">{answerModal?.question}</p>
            </div>
            <div>
              <Label className="text-zinc-400 text-xs uppercase tracking-wider">Your Answer</Label>
              <Textarea value={adminAnswer} onChange={e => setAdminAnswer(e.target.value)} rows={4} placeholder="Provide the correct answer. This will also be added to the knowledge base." className="mt-1 bg-[#0a0a0a] border-white/[0.06] text-white text-sm resize-none" data-testid="admin-answer-input" />
              <p className="text-[10px] text-zinc-600 mt-1">This answer will be saved to the knowledge base for future reference</p>
            </div>
            <Button onClick={handleAnswer} className="w-full bg-orange-500 hover:bg-orange-400 text-white gap-2" data-testid="submit-answer-btn">
              <Send className="w-4 h-4" /> Answer & Add to Knowledge Base
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AITrainingPage;
