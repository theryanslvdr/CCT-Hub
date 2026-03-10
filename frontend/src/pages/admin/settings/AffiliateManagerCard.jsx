import React, { useState, useEffect } from 'react';
import { adminAffiliateAPI } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import { Plus, Loader2, FileText, Trash2, ExternalLink, Code } from 'lucide-react';

const RESOURCE_CATEGORIES = [
  { value: 'conversation_starters', label: 'Conversation Starters' },
  { value: 'story_templates', label: 'Story Templates' },
  { value: 'marketing', label: 'Marketing Materials' },
  { value: 'faqs', label: 'FAQs' },
];

export const AffiliateManagerCard = () => {
  const [resources, setResources] = useState([]);
  const [chatbase, setChatbase] = useState({ bot_id: '', enabled: false });
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState({ title: '', content: '', category: 'conversation_starters', order: 0 });
  const [filter, setFilter] = useState('all');

  const loadData = async () => {
    try {
      const [resRes, cbRes] = await Promise.all([
        adminAffiliateAPI.getResources(),
        adminAffiliateAPI.getChatbase(),
      ]);
      setResources(resRes.data.resources || []);
      setChatbase(cbRes.data);
    } catch { /* ignore */ }
    setLoading(false);
  };

  useEffect(() => { loadData(); }, []);

  const resetForm = () => {
    setForm({ title: '', content: '', category: 'conversation_starters', order: 0 });
    setEditingId(null);
    setShowForm(false);
  };

  const handleSave = async () => {
    if (!form.title.trim() || !form.content.trim()) { toast.error('Title and content required'); return; }
    try {
      if (editingId) {
        await adminAffiliateAPI.updateResource(editingId, form);
        toast.success('Resource updated');
      } else {
        await adminAffiliateAPI.createResource(form);
        toast.success('Resource created');
      }
      resetForm();
      loadData();
    } catch { toast.error('Failed to save'); }
  };

  const handleEdit = (r) => {
    setForm({ title: r.title, content: r.content, category: r.category, order: r.order || 0 });
    setEditingId(r.id);
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    try {
      await adminAffiliateAPI.deleteResource(id);
      toast.success('Resource deleted');
      loadData();
    } catch { toast.error('Failed'); }
  };

  const handleChatbaseSave = async () => {
    try {
      await adminAffiliateAPI.updateChatbase(chatbase.bot_id, chatbase.enabled);
      toast.success('Chatbase config saved');
    } catch { toast.error('Failed'); }
  };

  const filtered = filter === 'all' ? resources : resources.filter(r => r.category === filter);

  return (
    <div className="space-y-6">
      <Card className="glass-card">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-white flex items-center gap-2">
                <ExternalLink className="w-5 h-5 text-cyan-400" /> Affiliate Resources
              </CardTitle>
              <p className="text-sm text-zinc-400 mt-1">Manage conversation starters, story templates, marketing materials, and FAQs for members.</p>
            </div>
            <Button size="sm" onClick={() => { resetForm(); setShowForm(true); }} className="bg-cyan-600 hover:bg-cyan-700 gap-1" data-testid="add-resource-btn">
              <Plus className="w-4 h-4" /> Add Resource
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {showForm && (
            <div className="p-4 rounded-lg bg-[#0d0d0d]/60 border border-cyan-500/30 space-y-3" data-testid="resource-form">
              <Input value={form.title} onChange={(e) => setForm(p => ({ ...p, title: e.target.value }))} placeholder="Resource title" className="input-dark" data-testid="resource-title-input" />
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label className="text-zinc-300 text-xs">Category</Label>
                  <Select value={form.category} onValueChange={(v) => setForm(p => ({ ...p, category: v }))}>
                    <SelectTrigger className="input-dark mt-1"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {RESOURCE_CATEGORIES.map(c => <SelectItem key={c.value} value={c.value}>{c.label}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label className="text-zinc-300 text-xs">Sort Order</Label>
                  <Input type="number" value={form.order} onChange={(e) => setForm(p => ({ ...p, order: parseInt(e.target.value) || 0 }))} className="input-dark mt-1" />
                </div>
              </div>
              <Textarea value={form.content} onChange={(e) => setForm(p => ({ ...p, content: e.target.value }))} placeholder="Resource content (members can copy this)" className="input-dark" rows={4} data-testid="resource-content-input" />
              <div className="flex gap-2 justify-end">
                <Button variant="ghost" size="sm" onClick={resetForm}>Cancel</Button>
                <Button size="sm" onClick={handleSave} className="bg-cyan-600 hover:bg-cyan-700" data-testid="save-resource-btn">{editingId ? 'Update' : 'Create'}</Button>
              </div>
            </div>
          )}

          <div className="flex gap-1 flex-wrap">
            <Button variant={filter === 'all' ? 'default' : 'ghost'} size="sm" onClick={() => setFilter('all')} className="text-xs">All ({resources.length})</Button>
            {RESOURCE_CATEGORIES.map(c => {
              const count = resources.filter(r => r.category === c.value).length;
              return <Button key={c.value} variant={filter === c.value ? 'default' : 'ghost'} size="sm" onClick={() => setFilter(c.value)} className="text-xs">{c.label} ({count})</Button>;
            })}
          </div>

          {loading ? (
            <div className="py-8 flex justify-center"><Loader2 className="w-5 h-5 animate-spin text-zinc-500" /></div>
          ) : filtered.length === 0 ? (
            <p className="text-sm text-zinc-500 text-center py-4">No resources yet. Click "Add Resource" to create one.</p>
          ) : (
            filtered.map(r => (
              <div key={r.id} className="p-3 rounded-lg border bg-[#0d0d0d]/40 border-white/[0.06] flex items-start justify-between gap-2" data-testid={`admin-resource-${r.id}`}>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium text-white">{r.title}</p>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#1a1a1a] text-zinc-400">{RESOURCE_CATEGORIES.find(c => c.value === r.category)?.label}</span>
                  </div>
                  <p className="text-xs text-zinc-500 mt-0.5 line-clamp-1">{r.content}</p>
                </div>
                <div className="flex gap-1 shrink-0">
                  <Button variant="ghost" size="sm" onClick={() => handleEdit(r)} className="text-zinc-400 hover:text-white"><FileText className="w-4 h-4" /></Button>
                  <Button variant="ghost" size="sm" onClick={() => handleDelete(r.id)} className="text-red-400 hover:text-red-300"><Trash2 className="w-4 h-4" /></Button>
                </div>
              </div>
            ))
          )}
        </CardContent>
      </Card>

      <Card className="glass-card">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Code className="w-5 h-5 text-cyan-400" /> ConSim (Chatbase Chatbot)
          </CardTitle>
          <p className="text-sm text-zinc-400 mt-1">Embed a Chatbase chatbot in the Affiliate Center for members to practice conversations.</p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <Label className="text-zinc-300">Enable ConSim</Label>
            <Switch checked={chatbase.enabled} onCheckedChange={(v) => setChatbase(p => ({ ...p, enabled: v }))} data-testid="chatbase-toggle" />
          </div>
          {chatbase.enabled && (
            <div>
              <Label className="text-zinc-300">Chatbase Bot ID</Label>
              <Input value={chatbase.bot_id} onChange={(e) => setChatbase(p => ({ ...p, bot_id: e.target.value }))} placeholder="e.g., abc123-def456-..." className="input-dark mt-1" data-testid="chatbase-bot-id" />
            </div>
          )}
          <Button size="sm" onClick={handleChatbaseSave} className="bg-cyan-600 hover:bg-cyan-700" data-testid="save-chatbase-btn">Save Chatbase Config</Button>
        </CardContent>
      </Card>
    </div>
  );
};
