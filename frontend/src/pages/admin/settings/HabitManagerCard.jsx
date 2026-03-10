import React, { useState, useEffect } from 'react';
import { adminHabitAPI } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import { Plus, Loader2, FileText, XCircle, CheckCircle2, Clock } from 'lucide-react';

const ACTION_TYPES = [
  { value: 'send_invite', label: 'Send Invite (copy message)' },
  { value: 'link_click', label: 'Visit Link' },
  { value: 'generic', label: 'Generic Task' },
];

export const HabitManagerCard = () => {
  const [habits, setHabits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    title: '', description: '', action_type: 'generic',
    action_data: '', is_gate: true, validity_days: 1
  });

  const loadHabits = async () => {
    try {
      const res = await adminHabitAPI.getHabits();
      setHabits(res.data.habits || []);
    } catch (err) {
      console.error('Load habits error:', err);
    }
    setLoading(false);
  };

  useEffect(() => { loadHabits(); }, []);

  const resetForm = () => {
    setForm({ title: '', description: '', action_type: 'generic', action_data: '', is_gate: true, validity_days: 1 });
    setEditingId(null);
    setShowForm(false);
    setSaving(false);
  };

  const handleSave = async () => {
    if (!form.title.trim()) { toast.error('Title is required'); return; }
    setSaving(true);
    try {
      if (editingId) {
        await adminHabitAPI.updateHabit(editingId, form);
        toast.success('Habit updated');
      } else {
        await adminHabitAPI.createHabit(form);
        toast.success('Habit created');
      }
      resetForm();
      loadHabits();
    } catch (err) {
      const detail = err?.response?.data?.detail || err?.message || 'Unknown error';
      console.error('Save habit error:', err?.response?.status, detail);
      toast.error(`Failed to save habit: ${detail}`);
      setSaving(false);
    }
  };

  const handleEdit = (h) => {
    setForm({
      title: h.title, description: h.description || '',
      action_type: h.action_type, action_data: h.action_data || '',
      is_gate: h.is_gate, validity_days: h.validity_days || 1
    });
    setEditingId(h.id);
    setShowForm(true);
  };

  const handleToggleActive = async (h) => {
    try {
      if (h.active) {
        await adminHabitAPI.deleteHabit(h.id);
        toast.success('Habit deactivated');
      } else {
        await adminHabitAPI.activateHabit(h.id);
        toast.success('Habit activated');
      }
      loadHabits();
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Failed');
    }
  };

  return (
    <Card className="glass-card">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-white flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-teal-400" /> Manage Habits
            </CardTitle>
            <p className="text-sm text-zinc-400 mt-1">Daily tasks members complete to unlock the trading signal (soft gate).</p>
          </div>
          <Button size="sm" onClick={() => { resetForm(); setShowForm(true); }} className="bg-teal-600 hover:bg-teal-700 gap-1" data-testid="add-habit-btn">
            <Plus className="w-4 h-4" /> Add Habit
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {showForm && (
          <div className="p-4 rounded-lg bg-[#0d0d0d]/60 border border-teal-500/30 space-y-3" data-testid="habit-form">
            <Input value={form.title} onChange={(e) => setForm(p => ({ ...p, title: e.target.value }))} placeholder="Habit title (e.g., Send 1 invite today)" className="input-dark" data-testid="habit-title-input" />
            <Textarea value={form.description} onChange={(e) => setForm(p => ({ ...p, description: e.target.value }))} placeholder="Description (optional)" className="input-dark" rows={2} />
            <div className="grid grid-cols-3 gap-3">
              <div>
                <Label className="text-zinc-300 text-xs">Action Type</Label>
                <Select value={form.action_type} onValueChange={(v) => setForm(p => ({ ...p, action_type: v }))}>
                  <SelectTrigger className="input-dark mt-1"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {ACTION_TYPES.map(t => <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="text-zinc-300 text-xs flex items-center gap-1"><Clock className="w-3 h-3" /> Valid for (days)</Label>
                <Input
                  type="number" min={1} max={365}
                  value={form.validity_days}
                  onChange={(e) => setForm(p => ({ ...p, validity_days: Math.max(1, parseInt(e.target.value) || 1) }))}
                  className="input-dark mt-1"
                  data-testid="habit-validity-days"
                />
                <p className="text-[10px] text-zinc-500 mt-0.5">Signal stays unlocked this many days after completion</p>
              </div>
              <div className="flex items-center gap-2 pt-5">
                <Switch checked={form.is_gate} onCheckedChange={(v) => setForm(p => ({ ...p, is_gate: v }))} />
                <Label className="text-zinc-300 text-sm">Gate (unlocks signal)</Label>
              </div>
            </div>
            {form.action_type !== 'generic' && (
              <Textarea value={form.action_data} onChange={(e) => setForm(p => ({ ...p, action_data: e.target.value }))} placeholder={form.action_type === 'send_invite' ? 'Pre-written invite message...' : 'URL to visit...'} className="input-dark" rows={3} data-testid="habit-action-data" />
            )}
            <div className="flex gap-2 justify-end">
              <Button variant="ghost" size="sm" onClick={resetForm}>Cancel</Button>
              <Button size="sm" onClick={handleSave} disabled={saving} className="bg-teal-600 hover:bg-teal-700" data-testid="save-habit-btn">
                {saving ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : null}
                {editingId ? 'Update' : 'Create'}
              </Button>
            </div>
          </div>
        )}

        {loading ? (
          <div className="py-8 flex justify-center"><Loader2 className="w-5 h-5 animate-spin text-zinc-500" /></div>
        ) : habits.length === 0 ? (
          <p className="text-sm text-zinc-500 text-center py-4">No habits created yet. Click "Add Habit" to create one.</p>
        ) : (
          habits.map(h => (
            <div key={h.id} className={`p-3 rounded-lg border flex items-center justify-between ${h.active ? 'bg-[#0d0d0d]/40 border-white/[0.06]' : 'bg-[#0d0d0d]/20 border-white/[0.06]/50 opacity-60'}`} data-testid={`admin-habit-${h.id}`}>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-medium text-white">{h.title}</p>
                  {h.is_gate && <span className="text-[10px] px-1.5 py-0.5 rounded bg-orange-500/20 text-orange-400">Gate</span>}
                  {(h.validity_days || 1) > 1 && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-orange-500/10 text-orange-400 flex items-center gap-0.5">
                      <Clock className="w-2.5 h-2.5" /> {h.validity_days}d
                    </span>
                  )}
                  {!h.active && <span className="text-[10px] px-1.5 py-0.5 rounded bg-red-500/20 text-red-400">Inactive</span>}
                </div>
                <p className="text-xs text-zinc-500 mt-0.5">{ACTION_TYPES.find(t => t.value === h.action_type)?.label || h.action_type}</p>
              </div>
              <div className="flex gap-1 shrink-0">
                <Button variant="ghost" size="sm" onClick={() => handleEdit(h)} className="text-zinc-400 hover:text-white"><FileText className="w-4 h-4" /></Button>
                <Button variant="ghost" size="sm" onClick={() => handleToggleActive(h)} className={h.active ? 'text-red-400 hover:text-red-300' : 'text-emerald-400 hover:text-emerald-300'}>
                  {h.active ? <XCircle className="w-4 h-4" /> : <CheckCircle2 className="w-4 h-4" />}
                </Button>
              </div>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
};
