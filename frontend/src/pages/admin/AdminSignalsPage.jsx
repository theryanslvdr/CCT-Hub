import React, { useState, useEffect } from 'react';
import { adminAPI, bveAPI } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { useBVE } from '@/contexts/BVEContext';
import { formatNumber } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { toast } from 'sonner';
import { 
  Plus, Radio, Trash2, TrendingUp, TrendingDown, Edit, Clock, Target, Zap, 
  FlaskConical, ChevronLeft, ChevronRight, Archive, Calendar, FolderOpen
} from 'lucide-react';
import api from '@/lib/api';

const tradingTimezones = [
  { value: 'Asia/Manila', label: 'Philippines (GMT+8)' },
  { value: 'Asia/Singapore', label: 'Singapore (GMT+8)' },
  { value: 'Asia/Taipei', label: 'Taiwan (GMT+8)' },
];

export const AdminSignalsPage = () => {
  const { isSuperAdmin } = useAuth();
  const { isInBVE } = useBVE();
  const [signals, setSignals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [simulateDialogOpen, setSimulateDialogOpen] = useState(false);
  const [archiveDialogOpen, setArchiveDialogOpen] = useState(false);
  const [selectedSignal, setSelectedSignal] = useState(null);
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalSignals, setTotalSignals] = useState(0);
  const pageSize = 10;
  
  // Archive state
  const [archiveData, setArchiveData] = useState([]);
  const [archiveLoading, setArchiveLoading] = useState(false);
  
  const [newSignal, setNewSignal] = useState({
    product: 'MOIL10',
    trade_time: '',
    trade_timezone: 'Asia/Manila',
    direction: 'BUY',
    profit_points: '15',
    notes: '',
    is_official: false,
    send_email: true,  // Auto-send email when official signal is created
  });
  const [editForm, setEditForm] = useState({
    trade_time: '',
    trade_timezone: '',
    direction: '',
    profit_points: '',
    notes: '',
    is_active: true,
    is_official: false,
    send_email: false,  // Don't auto-send on edit by default
  });

  useEffect(() => {
    loadSignals();
  }, [currentPage, isInBVE]);

  const loadSignals = async () => {
    try {
      setLoading(true);
      // In BVE mode, load from BVE signals collection
      if (isInBVE) {
        const res = await api.get('/bve/signals');
        setSignals(res.data);
        setTotalPages(1);
        setTotalSignals(res.data.length);
      } else {
        const res = await adminAPI.getSignalsHistory(currentPage, pageSize);
        setSignals(res.data.signals);
        setTotalPages(res.data.total_pages);
        setTotalSignals(res.data.total);
      }
    } catch (error) {
      console.error('Failed to load signals:', error);
      // Fallback to old method
      try {
        const res = await adminAPI.getSignals();
        setSignals(res.data);
      } catch (e) {
        toast.error('Failed to load signals');
      }
    } finally {
      setLoading(false);
    }
  };

  const loadArchive = async () => {
    try {
      setArchiveLoading(true);
      const res = await adminAPI.getSignalsArchive();
      setArchiveData(res.data.months || []);
    } catch (error) {
      console.error('Failed to load archive:', error);
      toast.error('Failed to load signal archive');
    } finally {
      setArchiveLoading(false);
    }
  };

  const handleOpenArchive = () => {
    loadArchive();
    setArchiveDialogOpen(true);
  };

  const handleArchiveMonth = async () => {
    try {
      const res = await adminAPI.archiveMonth();
      toast.success(res.data.message);
      loadSignals();
      loadArchive();
    } catch (error) {
      toast.error('Failed to archive signals');
    }
  };

  const handleCreateSignal = async () => {
    if (!newSignal.trade_time) {
      toast.error('Please select a trade time');
      return;
    }
    
    try {
      // In BVE mode, create signal in BVE collection
      if (isInBVE) {
        await api.post('/bve/signals', {
          ...newSignal,
          profit_multiplier: parseFloat(newSignal.profit_points) || 15,
        });
        toast.success('BVE signal created!');
      } else {
        await adminAPI.createSignal({
          ...newSignal,
          profit_points: parseFloat(newSignal.profit_points) || 15,
          is_official: newSignal.is_official,
        });
        toast.success('Trading signal created!');
      }
      setDialogOpen(false);
      setNewSignal({
        product: 'MOIL10',
        trade_time: '',
        trade_timezone: 'Asia/Manila',
        direction: 'BUY',
        profit_points: '15',
        notes: '',
        is_official: false,
      });
      loadSignals();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create signal');
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
      is_official: signal.is_official || false,
    });
    setEditDialogOpen(true);
  };

  const handleSaveEdit = async () => {
    try {
      // Use BVE API when in BVE mode, otherwise use regular admin API
      if (isInBVE) {
        await bveAPI.updateSignal(selectedSignal.id, {
          trade_time: editForm.trade_time,
          trade_timezone: editForm.trade_timezone,
          direction: editForm.direction,
          profit_points: parseFloat(editForm.profit_points) || 15,
          notes: editForm.notes,
          is_active: editForm.is_active,
        });
        toast.success('BVE signal updated!');
      } else {
        await api.put(`/admin/signals/${selectedSignal.id}`, {
          trade_time: editForm.trade_time,
          trade_timezone: editForm.trade_timezone,
          direction: editForm.direction,
          profit_points: parseFloat(editForm.profit_points) || 15,
          notes: editForm.notes,
          is_active: editForm.is_active,
          is_official: editForm.is_official,
        });
        toast.success('Signal updated!');
      }
      setEditDialogOpen(false);
      loadSignals();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update signal');
    }
  };

  const handleDeleteSignal = async (signalId) => {
    if (!confirm('Are you sure you want to delete this signal?')) return;
    
    try {
      await adminAPI.deleteSignal(signalId);
      toast.success('Signal deleted');
      loadSignals();
    } catch (error) {
      toast.error('Failed to delete signal');
    }
  };

  const handleSimulateSignal = async () => {
    if (!newSignal.trade_time) {
      toast.error('Please select a trade time');
      return;
    }
    
    try {
      await api.post('/admin/signals/simulate', {
        ...newSignal,
        profit_points: parseFloat(newSignal.profit_points) || 15,
      });
      toast.success('Simulated signal created! Check Trade Monitor.');
      setSimulateDialogOpen(false);
      setNewSignal({
        product: 'MOIL10',
        trade_time: '',
        trade_timezone: 'Asia/Manila',
        direction: 'BUY',
        profit_points: '15',
        notes: '',
      });
      loadSignals();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to simulate signal');
    }
  };

  const activeSignal = signals.find(s => s.is_active);

  // Format date for display
  const formatDate = (dateStr) => {
    try {
      return new Date(dateStr).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="space-y-6">
      {/* BVE Mode Banner */}
      {isInBVE && (
        <div className="bg-purple-500/20 border border-purple-500/30 rounded-xl p-4 flex items-center gap-3">
          <FlaskConical className="w-6 h-6 text-purple-400 animate-pulse" />
          <div>
            <h3 className="text-purple-300 font-semibold">Beta Virtual Environment Active</h3>
            <p className="text-purple-400/70 text-sm">All actions here are isolated and won't affect real data. Use "Rewind" to reset.</p>
          </div>
        </div>
      )}
      
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">
            {isInBVE ? 'BVE Trading Signals' : 'Trading Signals'}
          </h1>
          <p className="text-zinc-400">
            {isInBVE ? 'Simulated signals in Beta Virtual Environment' : 'Manage daily trading signals for members'}
          </p>
        </div>
        <div className="flex gap-2">
          {/* Archive Button - Hide in BVE mode */}
          {!isInBVE && (
            <Button 
              variant="outline" 
              onClick={handleOpenArchive} 
              className="btn-secondary gap-2"
              data-testid="open-archive-btn"
            >
              <Archive className="w-4 h-4" /> Monthly Archive
            </Button>
          )}
          
          {/* Simulate Button - Show as "Simulate New Signal" in BVE mode */}
          {(isSuperAdmin() || isInBVE) && !isInBVE && (
            <Dialog open={simulateDialogOpen} onOpenChange={setSimulateDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" className="btn-secondary gap-2" data-testid="simulate-signal-btn">
                  <FlaskConical className="w-4 h-4" /> Simulate
                </Button>
              </DialogTrigger>
              <DialogContent className="glass-card border-zinc-800">
                <DialogHeader>
                  <DialogTitle className="text-white flex items-center gap-2">
                    <FlaskConical className="w-5 h-5 text-amber-400" /> Simulate Test Signal
                  </DialogTitle>
                </DialogHeader>
                <div className="space-y-4 mt-4">
                  <p className="text-sm text-amber-400 bg-amber-500/10 p-3 rounded-lg">
                    This will create a test signal visible only in Trade Monitor. It will replace any active signal.
                  </p>
                  {/* Same form as create signal */}
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label className="text-zinc-300">Product</Label>
                      <Select value={newSignal.product} onValueChange={(v) => setNewSignal({ ...newSignal, product: v })}>
                        <SelectTrigger className="input-dark mt-1">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="MOIL10">MOIL10</SelectItem>
                          <SelectItem value="XAUUSD">XAUUSD (Gold)</SelectItem>
                          <SelectItem value="BTCUSD">BTCUSD (Bitcoin)</SelectItem>
                        </SelectContent>
                      </Select>
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
                      <Label className="text-zinc-300">Timezone</Label>
                      <Select value={newSignal.trade_timezone} onValueChange={(v) => setNewSignal({ ...newSignal, trade_timezone: v })}>
                        <SelectTrigger className="input-dark mt-1">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {tradingTimezones.map((tz) => (
                            <SelectItem key={tz.value} value={tz.value}>{tz.label}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div>
                    <Label className="text-zinc-300">Profit Points (Multiplier)</Label>
                    <Input
                      type="number"
                      value={newSignal.profit_points}
                      onChange={(e) => setNewSignal({ ...newSignal, profit_points: e.target.value })}
                      className="input-dark mt-1"
                      placeholder="15"
                    />
                  </div>
                  <div>
                    <Label className="text-zinc-300">Notes (Optional)</Label>
                    <Input
                      value={newSignal.notes}
                      onChange={(e) => setNewSignal({ ...newSignal, notes: e.target.value })}
                      className="input-dark mt-1"
                      placeholder="Any additional notes..."
                    />
                  </div>
                  <Button onClick={handleSimulateSignal} className="w-full bg-amber-500 hover:bg-amber-600 text-black" data-testid="submit-simulate-btn">
                    <FlaskConical className="w-4 h-4 mr-2" /> Create Simulated Signal
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          )}
          
          {/* Create Signal Button */}
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button className="btn-primary gap-2" data-testid="create-signal-btn">
                <Plus className="w-4 h-4" /> New Signal
              </Button>
            </DialogTrigger>
            <DialogContent className="glass-card border-zinc-800">
              <DialogHeader>
                <DialogTitle className="text-white flex items-center gap-2">
                  <Radio className="w-5 h-5 text-blue-400" /> Create Trading Signal
                </DialogTitle>
              </DialogHeader>
              <div className="space-y-4 mt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-zinc-300">Product</Label>
                    <Select value={newSignal.product} onValueChange={(v) => setNewSignal({ ...newSignal, product: v })}>
                      <SelectTrigger className="input-dark mt-1">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="MOIL10">MOIL10</SelectItem>
                        <SelectItem value="XAUUSD">XAUUSD (Gold)</SelectItem>
                        <SelectItem value="BTCUSD">BTCUSD (Bitcoin)</SelectItem>
                      </SelectContent>
                    </Select>
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
                    <Label className="text-zinc-300">Timezone</Label>
                    <Select value={newSignal.trade_timezone} onValueChange={(v) => setNewSignal({ ...newSignal, trade_timezone: v })}>
                      <SelectTrigger className="input-dark mt-1">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {tradingTimezones.map((tz) => (
                          <SelectItem key={tz.value} value={tz.value}>{tz.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div>
                  <Label className="text-zinc-300">Profit Points (Multiplier)</Label>
                  <Input
                    type="number"
                    value={newSignal.profit_points}
                    onChange={(e) => setNewSignal({ ...newSignal, profit_points: e.target.value })}
                    className="input-dark mt-1"
                    placeholder="15"
                  />
                  <p className="text-xs text-zinc-500 mt-1">Exit Value = LOT Size × Profit Points</p>
                </div>
                <div>
                  <Label className="text-zinc-300">Notes (Optional)</Label>
                  <Input
                    value={newSignal.notes}
                    onChange={(e) => setNewSignal({ ...newSignal, notes: e.target.value })}
                    className="input-dark mt-1"
                    placeholder="Market conditions, strategy notes..."
                  />
                </div>
                
                {/* Official Signal Toggle */}
                <div className="flex items-center justify-between p-3 rounded-lg bg-zinc-900/50 border border-zinc-800">
                  <div>
                    <Label className="text-zinc-300 cursor-pointer">Official Trading Signal</Label>
                    <p className="text-xs text-zinc-500 mt-0.5">Mark this as an official signal from the trading team</p>
                  </div>
                  <Switch
                    checked={newSignal.is_official}
                    onCheckedChange={(checked) => setNewSignal({ ...newSignal, is_official: checked })}
                    data-testid="official-signal-toggle"
                  />
                </div>
                
                <Button onClick={handleCreateSignal} className="w-full btn-primary" data-testid="submit-signal-btn">
                  <Radio className="w-4 h-4 mr-2" /> Publish Signal
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Active Signal Card */}
      {activeSignal && (
        <Card className="glass-highlight border-blue-500/30">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Radio className="w-5 h-5 text-blue-400 animate-pulse" /> Active Signal
              {activeSignal.is_official && (
                <span className="ml-2 px-2 py-0.5 text-xs bg-emerald-500/20 text-emerald-400 rounded-full flex items-center gap-1">
                  <Zap className="w-3 h-3" /> OFFICIAL
                </span>
              )}
              {activeSignal.is_simulated && (
                <span className="ml-2 px-2 py-0.5 text-xs bg-amber-500/20 text-amber-400 rounded-full flex items-center gap-1">
                  <FlaskConical className="w-3 h-3" /> SIMULATED
                </span>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
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
                  <Target className="w-3 h-3" /> Profit Points
                </p>
                <p className="text-2xl font-mono font-bold text-purple-400">×{activeSignal.profit_points || 15}</p>
              </div>
              <div className="flex gap-2 ml-auto">
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={async () => {
                    try {
                      // Use BVE API when in BVE mode, otherwise use regular admin API
                      if (isInBVE) {
                        await bveAPI.updateSignal(activeSignal.id, { is_active: false });
                      } else {
                        await adminAPI.updateSignal(activeSignal.id, { is_active: false });
                      }
                      toast.success('Signal deactivated');
                      loadSignals();
                    } catch (error) {
                      toast.error('Failed to deactivate signal');
                    }
                  }} 
                  className="text-amber-400 border-amber-400/30 hover:bg-amber-400/10"
                  data-testid="deactivate-signal-btn"
                >
                  <Zap className="w-4 h-4 mr-1" /> Deactivate
                </Button>
                <Button variant="outline" size="sm" onClick={() => handleEditSignal(activeSignal)} className="btn-secondary">
                  <Edit className="w-4 h-4" />
                </Button>
              </div>
            </div>
            {activeSignal.notes && (
              <p className="mt-4 text-zinc-400 p-3 bg-zinc-900/50 rounded-lg">{activeSignal.notes}</p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Signal History with Pagination */}
      <Card className="glass-card">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-white">Signal History</CardTitle>
          <p className="text-sm text-zinc-500">{totalSignals} total signals</p>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center h-32">
              <div className="w-8 h-8 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
            </div>
          ) : signals.length > 0 ? (
            <>
              <div className="overflow-x-auto">
                <table className="w-full data-table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Product</th>
                      <th>Direction</th>
                      <th>Time</th>
                      <th>Multiplier</th>
                      <th>Status</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {signals.map((signal) => (
                      <tr key={signal.id} className={signal.is_active ? 'bg-blue-500/5' : ''}>
                        <td className="font-mono text-zinc-400">
                          {formatDate(signal.created_at)}
                        </td>
                        <td className="font-medium text-white">{signal.product}</td>
                        <td>
                          <span className={`status-badge ${signal.direction === 'BUY' ? 'direction-buy' : 'direction-sell'}`}>
                            {signal.direction}
                          </span>
                        </td>
                        <td className="font-mono text-blue-400">{signal.trade_time}</td>
                        <td className="font-mono text-purple-400">×{signal.profit_points || 15}</td>
                        <td>
                          {signal.is_simulated ? (
                            <span className="status-badge bg-amber-500/20 text-amber-400 flex items-center gap-1 w-fit">
                              <FlaskConical className="w-3 h-3" /> Simulated
                            </span>
                          ) : signal.is_active ? (
                            <span className="status-badge bg-emerald-500/20 text-emerald-400">Active</span>
                          ) : (
                            <span className="status-badge bg-zinc-500/20 text-zinc-400">Completed</span>
                          )}
                        </td>
                        <td>
                          <div className="flex gap-1">
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => handleEditSignal(signal)}
                              className="text-zinc-400 hover:text-blue-400"
                            >
                              <Edit className="w-4 h-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => handleDeleteSignal(signal.id)}
                              className="text-zinc-400 hover:text-red-400"
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
              
              {/* Pagination */}
              <div className="flex items-center justify-between mt-4 pt-4 border-t border-zinc-800">
                <p className="text-sm text-zinc-500">
                  Page {currentPage} of {totalPages}
                </p>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                    disabled={currentPage === 1}
                    className="btn-secondary"
                    data-testid="prev-page-btn"
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </Button>
                  <span className="text-sm text-zinc-400 px-2">
                    {currentPage} / {totalPages}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                    disabled={currentPage === totalPages}
                    className="btn-secondary"
                    data-testid="next-page-btn"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </>
          ) : (
            <div className="text-center py-12">
              <Radio className="w-12 h-12 text-zinc-600 mx-auto mb-4" />
              <p className="text-zinc-400">No signals yet. Create your first trading signal!</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Monthly Archive Dialog */}
      <Dialog open={archiveDialogOpen} onOpenChange={setArchiveDialogOpen}>
        <DialogContent className="glass-card border-zinc-800 max-w-3xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Archive className="w-5 h-5 text-blue-400" /> Monthly Signal Archive
            </DialogTitle>
          </DialogHeader>
          <div className="mt-4">
            {archiveLoading ? (
              <div className="flex items-center justify-center h-32">
                <div className="w-8 h-8 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
              </div>
            ) : archiveData.length > 0 ? (
              <Accordion type="single" collapsible className="space-y-2">
                {archiveData.map((month) => (
                  <AccordionItem 
                    key={month.month_key} 
                    value={month.month_key}
                    className="glass-card border border-zinc-800 rounded-lg overflow-hidden"
                  >
                    <AccordionTrigger className="px-4 py-3 hover:bg-zinc-800/50">
                      <div className="flex items-center gap-3">
                        <Calendar className="w-5 h-5 text-blue-400" />
                        <span className="text-white font-medium">{month.month_label}</span>
                        <span className="text-xs text-zinc-500 bg-zinc-800 px-2 py-0.5 rounded-full">
                          {month.signals.length} signals
                        </span>
                      </div>
                    </AccordionTrigger>
                    <AccordionContent className="px-4 pb-4">
                      <div className="space-y-2">
                        {month.signals.map((signal, index) => (
                          <div 
                            key={signal.id || index} 
                            className="p-3 rounded-lg bg-zinc-900/50 flex items-center justify-between"
                          >
                            <div className="flex items-center gap-4">
                              <span className="text-xs text-zinc-500 font-mono">
                                {new Date(signal.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                              </span>
                              <span className="font-medium text-white">{signal.product}</span>
                              <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                                signal.direction === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'
                              }`}>
                                {signal.direction}
                              </span>
                              <span className="text-blue-400 font-mono">{signal.trade_time}</span>
                              <span className="text-purple-400 font-mono">×{signal.profit_points || 15}</span>
                            </div>
                            {signal.is_simulated && (
                              <span className="px-2 py-0.5 text-xs bg-amber-500/20 text-amber-400 rounded-full flex items-center gap-1">
                                <FlaskConical className="w-3 h-3" /> Simulated
                              </span>
                            )}
                          </div>
                        ))}
                      </div>
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            ) : (
              <div className="text-center py-12">
                <FolderOpen className="w-12 h-12 text-zinc-600 mx-auto mb-4" />
                <p className="text-zinc-400">No archived signals yet.</p>
              </div>
            )}
            
            {/* Archive Action */}
            {isSuperAdmin() && (
              <div className="mt-6 pt-4 border-t border-zinc-800">
                <Button 
                  onClick={handleArchiveMonth} 
                  variant="outline" 
                  className="btn-secondary w-full gap-2"
                >
                  <Archive className="w-4 h-4" /> Archive Current Month's Inactive Signals
                </Button>
                <p className="text-xs text-zinc-500 mt-2 text-center">
                  This will mark all inactive signals from the current month as archived.
                </p>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>

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
                      <SelectItem key={tz.value} value={tz.value}>{tz.label}</SelectItem>
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
                <Label className="text-zinc-300">Profit Points</Label>
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
                className="input-dark mt-1"
              />
            </div>
            <div className="flex items-center justify-between p-3 rounded-lg bg-zinc-900/50">
              <Label className="text-zinc-300">Active Signal</Label>
              <Switch
                checked={editForm.is_active}
                onCheckedChange={(v) => setEditForm({ ...editForm, is_active: v })}
              />
            </div>
            <div className="flex items-center justify-between p-3 rounded-lg bg-zinc-900/50 border border-zinc-800">
              <div>
                <Label className="text-zinc-300">Official Trading Signal</Label>
                <p className="text-xs text-zinc-500 mt-0.5">Mark this as an official signal</p>
              </div>
              <Switch
                checked={editForm.is_official}
                onCheckedChange={(v) => setEditForm({ ...editForm, is_official: v })}
                data-testid="edit-official-signal-toggle"
              />
            </div>
            <Button onClick={handleSaveEdit} className="w-full btn-primary">
              Save Changes
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};
