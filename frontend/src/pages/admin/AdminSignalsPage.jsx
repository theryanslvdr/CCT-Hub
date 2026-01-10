import React, { useState, useEffect } from 'react';
import { adminAPI } from '@/lib/api';
import { formatNumber } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import { Plus, Radio, Trash2, TrendingUp, TrendingDown } from 'lucide-react';

export const AdminSignalsPage = () => {
  const [signals, setSignals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [newSignal, setNewSignal] = useState({
    product: 'MOIL10',
    trade_time: '',
    direction: 'BUY',
    notes: '',
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
      await adminAPI.createSignal(newSignal);
      toast.success('Trading signal created and activated!');
      setDialogOpen(false);
      setNewSignal({ product: 'MOIL10', trade_time: '', direction: 'BUY', notes: '' });
      loadSignals();
    } catch (error) {
      toast.error('Failed to create signal');
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

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="w-8 h-8 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" /></div>;
  }

  const activeSignal = signals.find(s => s.is_active);

  return (
    <div className="space-y-6">
      {/* Active Signal Card */}
      {activeSignal && (
        <Card className="glass-highlight border-blue-500/30">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Radio className="w-5 h-5 text-blue-400 animate-pulse" /> Active Signal
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-6">
                <div>
                  <p className="text-xs text-zinc-400">Product</p>
                  <p className="text-2xl font-bold text-white">{activeSignal.product}</p>
                </div>
                <div className={`px-6 py-3 rounded-xl text-xl font-bold ${activeSignal.direction === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
                  {activeSignal.direction}
                </div>
                <div>
                  <p className="text-xs text-zinc-400">Trade Time (UTC)</p>
                  <p className="text-2xl font-mono font-bold text-blue-400">{activeSignal.trade_time}</p>
                </div>
              </div>
              {activeSignal.notes && (
                <p className="text-zinc-400 max-w-xs">{activeSignal.notes}</p>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Create Signal Button */}
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
            <div>
              <Label className="text-zinc-300">Trade Time (UTC)</Label>
              <Input
                type="time"
                value={newSignal.trade_time}
                onChange={(e) => setNewSignal({ ...newSignal, trade_time: e.target.value })}
                className="input-dark mt-1"
                data-testid="signal-time-input"
              />
            </div>
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
                    <th>Created</th>
                    <th>Notes</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {signals.map((signal) => (
                    <tr key={signal.id}>
                      <td>
                        <span className={`status-badge ${signal.is_active ? 'status-success' : 'bg-zinc-700/50 text-zinc-400'}`}>
                          {signal.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="font-medium text-white">{signal.product}</td>
                      <td>
                        <span className={`status-badge ${signal.direction === 'BUY' ? 'direction-buy' : 'direction-sell'}`}>
                          {signal.direction}
                        </span>
                      </td>
                      <td className="font-mono">{signal.trade_time}</td>
                      <td className="font-mono text-zinc-400">{new Date(signal.created_at).toLocaleDateString()}</td>
                      <td className="text-zinc-500 max-w-[200px] truncate">{signal.notes || '-'}</td>
                      <td>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleDeleteSignal(signal.id)}
                          className="text-zinc-400 hover:text-red-400"
                          data-testid={`delete-signal-${signal.id}`}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
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
    </div>
  );
};
