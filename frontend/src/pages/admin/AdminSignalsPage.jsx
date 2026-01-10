import React, { useState, useEffect } from 'react';
import { adminAPI } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { formatNumber } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { toast } from 'sonner';
import { Plus, Radio, Trash2, TrendingUp, TrendingDown, Edit, Clock, Target, Zap, FlaskConical } from 'lucide-react';
import api from '@/lib/api';

const tradingTimezones = [
  { value: 'Asia/Manila', label: 'Philippines (GMT+8)' },
  { value: 'Asia/Singapore', label: 'Singapore (GMT+8)' },
  { value: 'Asia/Taipei', label: 'Taiwan (GMT+8)' },
];

export const AdminSignalsPage = () => {
  const { isSuperAdmin } = useAuth();
  const [signals, setSignals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [simulateDialogOpen, setSimulateDialogOpen] = useState(false);
  const [selectedSignal, setSelectedSignal] = useState(null);
  const [newSignal, setNewSignal] = useState({
    product: 'MOIL10',
    trade_time: '',
    trade_timezone: 'Asia/Manila',
    direction: 'BUY',
    profit_points: '15',
    notes: '',
  });
  const [editForm, setEditForm] = useState({
    trade_time: '',
    trade_timezone: '',
    direction: '',
    profit_points: '',
    notes: '',
    is_active: true,
  });

  useEffect(() => {
    loadSignals();
  }, []);

  const loadSignals = async () => {
    try {
      const res = await adminAPI.getSignals();
      setSignals(res.data);
    } catch (error) {
      console.error('Failed to load signals:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSignal = async () => {
    if (!newSignal.trade_time) {
      toast.error('Please set the trade time');
      return;
    }

    try {
      await adminAPI.createSignal({
        ...newSignal,
        profit_points: parseFloat(newSignal.profit_points) || 15,
      });
      toast.success('Trading signal created and activated!');
      setDialogOpen(false);
      setNewSignal({ product: 'MOIL10', trade_time: '', trade_timezone: 'Asia/Manila', direction: 'BUY', profit_points: '15', notes: '' });
      loadSignals();
    } catch (error) {
      toast.error('Failed to create signal');
    }
  };

  const handleEditSignal = (signal) => {
    setSelectedSignal(signal);
    setEditForm({
      trade_time: signal.trade_time,
      trade_timezone: signal.trade_timezone || 'Asia/Manila',
      direction: signal.direction,
      profit_points: signal.profit_points?.toString() || '15',
      notes: signal.notes || '',
      is_active: signal.is_active,
    });
    setEditDialogOpen(true);
  };

  const handleSaveEdit = async () => {
    try {
      await api.put(`/admin/signals/${selectedSignal.id}`, {
        trade_time: editForm.trade_time,
        trade_timezone: editForm.trade_timezone,
        direction: editForm.direction,
        profit_points: parseFloat(editForm.profit_points) || 15,
        notes: editForm.notes,
        is_active: editForm.is_active,
      });
      toast.success('Signal updated!');
      setEditDialogOpen(false);
      loadSignals();
    } catch (error) {
      toast.error('Failed to update signal');
    }
  };

  const handleSimulateSignal = async () => {
    if (!newSignal.trade_time) {
      toast.error('Please set the trade time');
      return;
    }

    try {
      await api.post('/admin/signals/simulate', {
        ...newSignal,
        profit_points: parseFloat(newSignal.profit_points) || 15,
      });
      toast.success('Simulated signal created! (Super Admin testing only)');
      setSimulateDialogOpen(false);
      setNewSignal({ product: 'MOIL10', trade_time: '', trade_timezone: 'Asia/Manila', direction: 'BUY', profit_points: '15', notes: '' });
      loadSignals();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create simulated signal');
    }
  };

  const handleDeleteSignal = async (id) => {
    if (!window.confirm('Are you sure you want to delete this signal?')) return;
    
    try {
      await adminAPI.deleteSignal(id);
      toast.success('Signal deleted');
      loadSignals();
    } catch (error) {
      toast.error('Failed to delete signal');
    }
  };

  const handleToggleActive = async (signal) => {
    try {
      await api.put(`/admin/signals/${signal.id}`, {
        is_active: !signal.is_active,
      });
      toast.success(signal.is_active ? 'Signal deactivated' : 'Signal activated');
      loadSignals();
    } catch (error) {
      toast.error('Failed to toggle signal');
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="w-8 h-8 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" /></div>;
  }

  const activeSignal = signals.find(s => s.is_active);

  return (
    <div className="space-y-6">
      {/* Active Signal Card */}
      {activeSignal && (
        <Card className={`glass-highlight ${activeSignal.is_simulated ? 'border-amber-500/30' : 'border-blue-500/30'}`}>
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Radio className="w-5 h-5 text-blue-400 animate-pulse" /> 
              Active Signal
              {activeSignal.is_simulated && (
                <span className="ml-2 px-2 py-0.5 text-xs bg-amber-500/20 text-amber-400 rounded-full flex items-center gap-1">
                  <FlaskConical className="w-3 h-3" /> SIMULATED
                </span>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
              <div className="flex flex-wrap items-center gap-6">
                <div>
                  <p className="text-xs text-zinc-400">Product</p>
                  <p className="text-2xl font-bold text-white">{activeSignal.product}</p>
                </div>
                <div className={`px-6 py-3 rounded-xl text-xl font-bold ${activeSignal.direction === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
                  {activeSignal.direction === 'BUY' ? <TrendingUp className="inline w-5 h-5 mr-2" /> : <TrendingDown className="inline w-5 h-5 mr-2" />}
                  {activeSignal.direction}
                </div>
                <div>
                  <p className="text-xs text-zinc-400 flex items-center gap-1">
                    <Clock className="w-3 h-3" /> Trade Time ({activeSignal.trade_timezone || 'Asia/Manila'})
                  </p>
                  <p className="text-2xl font-mono font-bold text-blue-400">{activeSignal.trade_time}</p>
                </div>
                <div>
                  <p className="text-xs text-zinc-400 flex items-center gap-1">
                    <Target className="w-3 h-3" /> Profit Multiplier
                  </p>
                  <p className="text-2xl font-mono font-bold text-cyan-400">×{activeSignal.profit_points || 15}</p>
                </div>
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleEditSignal(activeSignal)}
                  className="btn-secondary"
                >
                  <Edit className="w-4 h-4 mr-1" /> Edit
                </Button>
              </div>
            </div>
            {activeSignal.notes && (
              <p className="text-zinc-400 mt-4 p-3 bg-zinc-900/50 rounded-lg">{activeSignal.notes}</p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Action Buttons */}
      <div className="flex flex-wrap gap-4">
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button className="btn-primary gap-2" data-testid="create-signal-button">
              <Plus className="w-4 h-4" /> Create New Signal
            </Button>
          </DialogTrigger>
          <DialogContent className="glass-card border-zinc-800">
            <DialogHeader>
              <DialogTitle className="text-white">Create Trading Signal</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 mt-4">
              <div>
                <Label className="text-zinc-300">Product</Label>
                <Select value={newSignal.product} onValueChange={(v) => setNewSignal({ ...newSignal, product: v })}>
                  <SelectTrigger className="input-dark mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="MOIL10">MOIL10</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-zinc-300">Trade Time</Label>
                  <Input
                    type="time"
                    value={newSignal.trade_time}
                    onChange={(e) => setNewSignal({ ...newSignal, trade_time: e.target.value })}
                    className="input-dark mt-1"
                    data-testid="signal-time-input"
                  />
                </div>
                <div>
                  <Label className="text-zinc-300">Timezone</Label>
                  <Select value={newSignal.trade_timezone} onValueChange={(v) => setNewSignal({ ...newSignal, trade_timezone: v })}>
                    <SelectTrigger className="input-dark mt-1">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {tradingTimezones.map((tz) => (
                        <SelectItem key={tz.value} value={tz.value}>
                          {tz.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-zinc-300">Direction</Label>
                  <Select value={newSignal.direction} onValueChange={(v) => setNewSignal({ ...newSignal, direction: v })}>
                    <SelectTrigger className="input-dark mt-1">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="BUY">
                        <span className="flex items-center gap-2">
                          <TrendingUp className="w-4 h-4 text-emerald-400" /> BUY
                        </span>
                      </SelectItem>
                      <SelectItem value="SELL">
                        <span className="flex items-center gap-2">
                          <TrendingDown className="w-4 h-4 text-red-400" /> SELL
                        </span>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label className="text-zinc-300">Profit Multiplier (×)</Label>
                  <Input
                    type="number"
                    value={newSignal.profit_points}
                    onChange={(e) => setNewSignal({ ...newSignal, profit_points: e.target.value })}
                    placeholder="15"
                    className="input-dark mt-1"
                    data-testid="profit-points-input"
                  />
                  <p className="text-xs text-zinc-500 mt-1">Exit Value = LOT × {newSignal.profit_points || 15}</p>
                </div>
              </div>
              <div>
                <Label className="text-zinc-300">Notes (optional)</Label>
                <Input
                  value={newSignal.notes}
                  onChange={(e) => setNewSignal({ ...newSignal, notes: e.target.value })}
                  placeholder="Add notes for traders..."
                  className="input-dark mt-1"
                />
              </div>
              <Button onClick={handleCreateSignal} className="w-full btn-primary" data-testid="confirm-create-signal">
                Create & Activate Signal
              </Button>
              <p className="text-xs text-zinc-500 text-center">
                Creating a new signal will deactivate any existing active signal.
              </p>
            </div>
          </DialogContent>
        </Dialog>

        {isSuperAdmin && (
          <Dialog open={simulateDialogOpen} onOpenChange={setSimulateDialogOpen}>
            <DialogTrigger asChild>
              <Button className="btn-secondary gap-2" data-testid="simulate-signal-button">
                <FlaskConical className="w-4 h-4" /> Simulate Signal
              </Button>
            </DialogTrigger>
            <DialogContent className="glass-card border-zinc-800">
              <DialogHeader>
                <DialogTitle className="text-white flex items-center gap-2">
                  <FlaskConical className="w-5 h-5 text-amber-400" /> Create Simulated Signal
                </DialogTitle>
              </DialogHeader>
              <div className="p-3 mb-4 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-400 text-sm">
                <strong>Super Admin Only:</strong> Simulated signals are for testing purposes and will be marked as "[SIMULATED]".
              </div>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-zinc-300">Trade Time</Label>
                    <Input
                      type="time"
                      value={newSignal.trade_time}
                      onChange={(e) => setNewSignal({ ...newSignal, trade_time: e.target.value })}
                      className="input-dark mt-1"
                    />
                  </div>
                  <div>
                    <Label className="text-zinc-300">Direction</Label>
                    <Select value={newSignal.direction} onValueChange={(v) => setNewSignal({ ...newSignal, direction: v })}>
                      <SelectTrigger className="input-dark mt-1">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="BUY">BUY</SelectItem>
                        <SelectItem value="SELL">SELL</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div>
                  <Label className="text-zinc-300">Notes</Label>
                  <Input
                    value={newSignal.notes}
                    onChange={(e) => setNewSignal({ ...newSignal, notes: e.target.value })}
                    placeholder="Test scenario..."
                    className="input-dark mt-1"
                  />
                </div>
                <Button onClick={handleSimulateSignal} className="w-full bg-amber-500 hover:bg-amber-600 text-black">
                  Create Simulated Signal
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        )}
      </div>

      {/* Signals History */}
      <Card className="glass-card">
        <CardHeader>
          <CardTitle className="text-white">Signal History</CardTitle>
        </CardHeader>
        <CardContent>
          {signals.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full data-table">
                <thead>
                  <tr>
                    <th>Status</th>
                    <th>Product</th>
                    <th>Direction</th>
                    <th>Trade Time</th>
                    <th>Timezone</th>
                    <th>Multiplier</th>
                    <th>Created</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {signals.map((signal) => (
                    <tr key={signal.id} className={signal.is_simulated ? 'bg-amber-500/5' : ''}>
                      <td>
                        <div className="flex items-center gap-2">
                          <span className={`status-badge ${signal.is_active ? 'status-success' : 'bg-zinc-700/50 text-zinc-400'}`}>
                            {signal.is_active ? 'Active' : 'Inactive'}
                          </span>
                          {signal.is_simulated && (
                            <span className="text-amber-400" title="Simulated">
                              <FlaskConical className="w-4 h-4" />
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="font-medium text-white">{signal.product}</td>
                      <td>
                        <span className={`status-badge ${signal.direction === 'BUY' ? 'direction-buy' : 'direction-sell'}`}>
                          {signal.direction}
                        </span>
                      </td>
                      <td className="font-mono">{signal.trade_time}</td>
                      <td className="text-zinc-400 text-sm">{signal.trade_timezone || 'Asia/Manila'}</td>
                      <td className="font-mono text-cyan-400">×{signal.profit_points || 15}</td>
                      <td className="font-mono text-zinc-400">{new Date(signal.created_at).toLocaleDateString()}</td>
                      <td>
                        <div className="flex gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleEditSignal(signal)}
                            className="text-zinc-400 hover:text-blue-400"
                            data-testid={`edit-signal-${signal.id}`}
                          >
                            <Edit className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleToggleActive(signal)}
                            className={signal.is_active ? 'text-emerald-400 hover:text-emerald-300' : 'text-zinc-400 hover:text-emerald-400'}
                            title={signal.is_active ? 'Deactivate' : 'Activate'}
                          >
                            <Zap className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleDeleteSignal(signal.id)}
                            className="text-zinc-400 hover:text-red-400"
                            data-testid={`delete-signal-${signal.id}`}
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-8 text-zinc-500">
              No signals created yet. Create your first trading signal!
            </div>
          )}
        </CardContent>
      </Card>

      {/* Edit Signal Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent className="glass-card border-zinc-800">
          <DialogHeader>
            <DialogTitle className="text-white">Edit Signal</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-zinc-300">Trade Time</Label>
                <Input
                  type="time"
                  value={editForm.trade_time}
                  onChange={(e) => setEditForm({ ...editForm, trade_time: e.target.value })}
                  className="input-dark mt-1"
                />
              </div>
              <div>
                <Label className="text-zinc-300">Timezone</Label>
                <Select value={editForm.trade_timezone} onValueChange={(v) => setEditForm({ ...editForm, trade_timezone: v })}>
                  <SelectTrigger className="input-dark mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {tradingTimezones.map((tz) => (
                      <SelectItem key={tz.value} value={tz.value}>
                        {tz.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-zinc-300">Direction</Label>
                <Select value={editForm.direction} onValueChange={(v) => setEditForm({ ...editForm, direction: v })}>
                  <SelectTrigger className="input-dark mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="BUY">BUY</SelectItem>
                    <SelectItem value="SELL">SELL</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="text-zinc-300">Profit Multiplier (×)</Label>
                <Input
                  type="number"
                  value={editForm.profit_points}
                  onChange={(e) => setEditForm({ ...editForm, profit_points: e.target.value })}
                  className="input-dark mt-1"
                />
              </div>
            </div>
            <div>
              <Label className="text-zinc-300">Notes</Label>
              <Input
                value={editForm.notes}
                onChange={(e) => setEditForm({ ...editForm, notes: e.target.value })}
                placeholder="Add notes..."
                className="input-dark mt-1"
              />
            </div>
            <div className="flex items-center justify-between p-3 rounded-lg bg-zinc-900/50">
              <Label className="text-zinc-300">Active</Label>
              <Switch
                checked={editForm.is_active}
                onCheckedChange={(v) => setEditForm({ ...editForm, is_active: v })}
              />
            </div>
            <Button onClick={handleSaveEdit} className="w-full btn-primary" data-testid="save-signal-edit">
              Save Changes
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};
