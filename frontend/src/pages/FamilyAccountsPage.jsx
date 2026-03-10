import React, { useState, useEffect, useCallback } from 'react';
import { familyAPI, profitAPI } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import { Users, Plus, TrendingUp, DollarSign, ArrowLeft, ChevronRight, Clock, Check, X, UserPlus, Wallet, BarChart3 } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

const formatCurrency = (val) => `$${(val || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

// Family Member Card
function MemberCard({ member, onView, onEdit, onRemove }) {
  const profitPct = member.starting_amount > 0
    ? ((member.profit / member.starting_amount) * 100).toFixed(1)
    : '0.0';

  return (
    <Card data-testid={`family-member-card-${member.id}`} className="bg-[#0d0d0d]/60 border-white/[0.06] hover:border-orange-500/40 transition-all cursor-pointer group">
      <CardContent className="p-5" onClick={() => onView(member)}>
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-orange-500 to-purple-600 flex items-center justify-center text-white font-bold text-sm">
              {member.name?.charAt(0)?.toUpperCase() || '?'}
            </div>
            <div>
              <h3 className="text-white font-semibold text-base">{member.name}</h3>
              <p className="text-zinc-500 text-xs capitalize">{member.relationship}</p>
            </div>
          </div>
          <ChevronRight className="w-4 h-4 text-zinc-600 group-hover:text-orange-400 transition-colors" />
        </div>
        <div className="grid grid-cols-3 gap-3">
          <div>
            <p className="text-zinc-500 text-xs mb-0.5">Account Value</p>
            <p className="text-white font-semibold text-sm">{formatCurrency(member.account_value)}</p>
          </div>
          <div>
            <p className="text-zinc-500 text-xs mb-0.5">Profit</p>
            <p className={`font-semibold text-sm ${member.profit >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
              {formatCurrency(member.profit)}
            </p>
          </div>
          <div>
            <p className="text-zinc-500 text-xs mb-0.5">Growth</p>
            <p className={`font-semibold text-sm ${member.profit >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
              {profitPct}%
            </p>
          </div>
        </div>
        {member.email && (
          <p className="text-zinc-600 text-xs mt-3 truncate">{member.email}</p>
        )}
        <div className="flex gap-2 mt-4 pt-3 border-t border-white/[0.06]">
          <Button variant="ghost" size="sm" className="text-zinc-400 hover:text-white text-xs h-7 px-2"
            onClick={(e) => { e.stopPropagation(); onEdit(member); }} data-testid={`edit-member-${member.id}`}>
            Edit
          </Button>
          <Button variant="ghost" size="sm" className="text-red-400/60 hover:text-red-400 text-xs h-7 px-2"
            onClick={(e) => { e.stopPropagation(); onRemove(member); }} data-testid={`remove-member-${member.id}`}>
            Remove
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

// Add/Edit Family Member Dialog
function MemberFormDialog({ open, onClose, onSubmit, editMember }) {
  const [name, setName] = useState('');
  const [relationship, setRelationship] = useState('');
  const [email, setEmail] = useState('');
  const [startingAmount, setStartingAmount] = useState('');
  const [startDate, setStartDate] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (editMember) {
      setName(editMember.name || '');
      setRelationship(editMember.relationship || '');
      setEmail(editMember.email || '');
      setStartingAmount('');
      setStartDate('');
    } else {
      setName(''); setRelationship(''); setEmail('');
      setStartingAmount(''); setStartDate('');
    }
  }, [editMember, open]);

  const handleSubmit = async () => {
    if (!name || !relationship) {
      toast.error('Name and relationship are required');
      return;
    }
    if (!editMember && (!startingAmount || parseFloat(startingAmount) <= 0)) {
      toast.error('Starting amount is required');
      return;
    }
    if (!editMember && !startDate) {
      toast.error('Deposit date is required');
      return;
    }
    setLoading(true);
    try {
      const payload = editMember
        ? { name, relationship, email: email || null }
        : { name, relationship, email: email || null, starting_amount: parseFloat(startingAmount), deposit_date: startDate || undefined };
      await onSubmit(payload, editMember?.id);
      onClose();
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Failed to save');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="bg-[#0d0d0d] border-white/[0.06] text-white max-w-md" data-testid="family-member-form-dialog">
        <DialogHeader>
          <DialogTitle className="text-white">{editMember ? 'Edit Family Member' : 'Add Family Member'}</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-2">
          <div>
            <Label className="text-zinc-400 text-xs">Name *</Label>
            <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Full name"
              className="bg-[#1a1a1a] border-white/[0.08] text-white mt-1" data-testid="member-name-input" />
          </div>
          <div>
            <Label className="text-zinc-400 text-xs">Relationship *</Label>
            <Select value={relationship} onValueChange={setRelationship}>
              <SelectTrigger className="bg-[#1a1a1a] border-white/[0.08] text-white mt-1" data-testid="member-relationship-select">
                <SelectValue placeholder="Select relationship" />
              </SelectTrigger>
              <SelectContent className="bg-[#1a1a1a] border-white/[0.08]">
                {['spouse', 'child', 'sibling', 'parent', 'other'].map(r => (
                  <SelectItem key={r} value={r} className="text-white capitalize">{r}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="text-zinc-400 text-xs">Email (optional)</Label>
            <Input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="email@example.com"
              className="bg-[#1a1a1a] border-white/[0.08] text-white mt-1" data-testid="member-email-input" />
          </div>
          {!editMember && (
            <>
              <div>
                <Label className="text-zinc-400 text-xs">Starting Amount ($) *</Label>
                <Input type="number" value={startingAmount} onChange={(e) => setStartingAmount(e.target.value)} placeholder="1000"
                  className="bg-[#1a1a1a] border-white/[0.08] text-white mt-1" data-testid="member-starting-amount-input" />
              </div>
              <div>
                <Label className="text-zinc-400 text-xs">Deposit Date *</Label>
                <Input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)}
                  className="bg-[#1a1a1a] border-white/[0.08] text-white mt-1" data-testid="member-deposit-date-input" />
                <p className="text-zinc-500 text-[11px] mt-1">Trading starts on the next trading day after this date</p>
              </div>
            </>
          )}
        </div>
        <DialogFooter>
          <Button variant="ghost" onClick={onClose} className="text-zinc-400">Cancel</Button>
          <Button onClick={handleSubmit} disabled={loading} className="bg-orange-600 hover:bg-orange-700" data-testid="member-form-submit">
            {loading ? 'Saving...' : editMember ? 'Save Changes' : 'Add Member'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// Withdrawal Request Dialog
function WithdrawalDialog({ open, onClose, member, onSubmit }) {
  const [amount, setAmount] = useState('');
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!amount || parseFloat(amount) <= 0) {
      toast.error('Enter a valid amount');
      return;
    }
    setLoading(true);
    try {
      await onSubmit(member.id, { amount: parseFloat(amount), notes });
      onClose();
      toast.success('Withdrawal request submitted');
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Failed to request withdrawal');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="bg-[#0d0d0d] border-white/[0.06] text-white max-w-sm" data-testid="withdrawal-dialog">
        <DialogHeader>
          <DialogTitle className="text-white">Request Withdrawal for {member?.name}</DialogTitle>
        </DialogHeader>
        <p className="text-zinc-400 text-sm">Account Value: {formatCurrency(member?.account_value)}</p>
        <div className="space-y-3 py-2">
          <div>
            <Label className="text-zinc-400 text-xs">Amount ($)</Label>
            <Input type="number" value={amount} onChange={(e) => setAmount(e.target.value)} placeholder="500"
              className="bg-[#1a1a1a] border-white/[0.08] text-white mt-1" data-testid="withdrawal-amount-input" />
          </div>
          <div>
            <Label className="text-zinc-400 text-xs">Notes (optional)</Label>
            <Input value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Reason for withdrawal"
              className="bg-[#1a1a1a] border-white/[0.08] text-white mt-1" />
          </div>
        </div>
        <DialogFooter>
          <Button variant="ghost" onClick={onClose} className="text-zinc-400">Cancel</Button>
          <Button onClick={handleSubmit} disabled={loading} className="bg-orange-600 hover:bg-orange-700" data-testid="submit-withdrawal-btn">
            {loading ? 'Submitting...' : 'Submit Request'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// Family Member Detail View (Profit Tracker)
function MemberDetailView({ member, onBack, isAdminSimulation, parentUserId }) {
  const [projections, setProjections] = useState([]);
  const [currentBalance, setCurrentBalance] = useState(0);
  const [loading, setLoading] = useState(true);
  const [selectedMonth, setSelectedMonth] = useState(() => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  });

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const res = isAdminSimulation && parentUserId
          ? await familyAPI.adminGetMemberProjections(parentUserId, member.id)
          : await familyAPI.getMemberProjections(member.id);
        setProjections(res.data.projections || []);
        setCurrentBalance(res.data.current_balance || 0);
      } catch (err) {
        toast.error('Failed to load projections');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [member.id, isAdminSimulation, parentUserId]);

  const filteredProjections = projections.filter(p => p.date?.startsWith(selectedMonth));
  const tradedDays = filteredProjections.filter(p => p.manager_traded).length;
  const monthProfit = filteredProjections.filter(p => p.manager_traded && new Date(p.date) <= new Date())
    .reduce((sum, p) => sum + (p.daily_profit || 0), 0);

  const availableMonths = [...new Set(projections.map(p => p.date?.slice(0, 7)))].sort();

  return (
    <div data-testid="family-member-detail-view">
      <Button variant="ghost" onClick={onBack} className="text-zinc-400 hover:text-white mb-4 -ml-2" data-testid="back-to-family-btn">
        <ArrowLeft className="w-4 h-4 mr-2" /> Back to Family Accounts
      </Button>

      <div className="flex items-center gap-3 mb-6">
        <div className="w-12 h-12 rounded-full bg-gradient-to-br from-orange-500 to-purple-600 flex items-center justify-center text-white font-bold text-lg">
          {member.name?.charAt(0)?.toUpperCase()}
        </div>
        <div>
          <h2 className="text-xl font-bold text-white">{member.name}</h2>
          <p className="text-zinc-500 text-sm capitalize">{member.relationship}</p>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        <Card className="bg-[#0d0d0d]/60 border-white/[0.06]">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-1">
              <Wallet className="w-4 h-4 text-orange-400" />
              <p className="text-zinc-500 text-xs">Account Value</p>
            </div>
            <p className="text-white font-bold text-lg">{formatCurrency(currentBalance)}</p>
          </CardContent>
        </Card>
        <Card className="bg-[#0d0d0d]/60 border-white/[0.06]">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-1">
              <TrendingUp className="w-4 h-4 text-emerald-400" />
              <p className="text-zinc-500 text-xs">Total Profit</p>
            </div>
            <p className="text-emerald-400 font-bold text-lg">{formatCurrency(currentBalance - member.starting_amount)}</p>
          </CardContent>
        </Card>
        <Card className="bg-[#0d0d0d]/60 border-white/[0.06]">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-1">
              <DollarSign className="w-4 h-4 text-amber-400" />
              <p className="text-zinc-500 text-xs">Starting Amount</p>
            </div>
            <p className="text-white font-bold text-lg">{formatCurrency(member.starting_amount)}</p>
          </CardContent>
        </Card>
        <Card className="bg-[#0d0d0d]/60 border-white/[0.06]">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-1">
              <BarChart3 className="w-4 h-4 text-purple-400" />
              <p className="text-zinc-500 text-xs">Month Profit</p>
            </div>
            <p className="text-purple-400 font-bold text-lg">{formatCurrency(monthProfit)}</p>
          </CardContent>
        </Card>
      </div>

      {/* Month Selector */}
      <div className="flex items-center gap-3 mb-4">
        <Label className="text-zinc-400 text-sm">Month:</Label>
        <Select value={selectedMonth} onValueChange={setSelectedMonth}>
          <SelectTrigger className="w-[180px] bg-[#1a1a1a] border-white/[0.08] text-white" data-testid="month-selector">
            <SelectValue />
          </SelectTrigger>
          <SelectContent className="bg-[#1a1a1a] border-white/[0.08]">
            {availableMonths.map(m => (
              <SelectItem key={m} value={m} className="text-white">{m}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <span className="text-zinc-500 text-xs">{tradedDays} trading days</span>
      </div>

      {/* Projections Table */}
      <Card className="bg-[#0d0d0d]/60 border-white/[0.06]">
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-6 h-6 border-2 border-orange-500 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm" data-testid="projections-table">
                <thead>
                  <tr className="border-b border-white/[0.06] text-zinc-500 text-xs">
                    <th className="text-left p-3">Date</th>
                    <th className="text-right p-3">Balance Before</th>
                    <th className="text-center p-3">Manager Traded</th>
                    <th className="text-right p-3">LOT Size</th>
                    <th className="text-right p-3">Daily Profit</th>
                    <th className="text-right p-3">Balance After</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredProjections.map((p, i) => {
                    const isPast = new Date(p.date) <= new Date();
                    return (
                      <tr key={i} className={`border-b border-white/[0.06]/50 ${isPast ? '' : 'opacity-50'}`}>
                        <td className="p-3 text-white font-mono text-xs">{p.date}</td>
                        <td className="p-3 text-right text-zinc-300 font-mono text-xs">{formatCurrency(p.start_value)}</td>
                        <td className="p-3 text-center">
                          {p.manager_traded
                            ? <span className="text-emerald-400 font-bold">&#10003;</span>
                            : <span className="text-red-400/60">&#10007;</span>
                          }
                        </td>
                        <td className="p-3 text-right text-zinc-300 font-mono text-xs">{p.lot_size?.toFixed(2)}</td>
                        <td className="p-3 text-right font-mono text-xs">
                          {p.manager_traded && isPast
                            ? <span className="text-emerald-400">+{formatCurrency(p.daily_profit)}</span>
                            : <span className="text-zinc-600">--</span>
                          }
                        </td>
                        <td className="p-3 text-right text-white font-mono text-xs">{formatCurrency(p.account_value)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              {filteredProjections.length === 0 && (
                <p className="text-zinc-500 text-center py-8 text-sm">No projections for this month</p>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// Withdrawal Management Section
function WithdrawalsSection({ withdrawals, onApprove, onReject }) {
  const pending = withdrawals.filter(w => w.status === 'pending_parent_approval');
  const others = withdrawals.filter(w => w.status !== 'pending_parent_approval');

  const statusLabel = (s) => ({
    'pending_parent_approval': 'Awaiting Your Approval',
    'pending_admin_approval': 'Awaiting Admin Approval',
    'approved': 'Approved',
    'rejected_by_parent': 'Rejected by You',
    'rejected_by_admin': 'Rejected by Admin'
  }[s] || s);

  const statusColor = (s) => ({
    'pending_parent_approval': 'text-amber-400',
    'pending_admin_approval': 'text-orange-400',
    'approved': 'text-emerald-400',
    'rejected_by_parent': 'text-red-400',
    'rejected_by_admin': 'text-red-400'
  }[s] || 'text-zinc-400');

  return (
    <div className="space-y-3" data-testid="withdrawals-section">
      {pending.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-amber-400 text-xs font-semibold uppercase tracking-wider">Pending Your Approval</h4>
          {pending.map(w => (
            <Card key={w.id} className="bg-amber-500/5 border-amber-500/20">
              <CardContent className="p-4 flex items-center justify-between">
                <div>
                  <p className="text-white font-medium text-sm">{w.family_member_name} - {formatCurrency(w.amount)}</p>
                  {w.notes && <p className="text-zinc-500 text-xs mt-1">{w.notes}</p>}
                </div>
                <div className="flex gap-2">
                  <Button size="sm" className="bg-emerald-600 hover:bg-emerald-700 h-7 px-3 text-xs"
                    onClick={() => onApprove(w.id)} data-testid={`approve-withdrawal-${w.id}`}>
                    <Check className="w-3 h-3 mr-1" /> Approve
                  </Button>
                  <Button size="sm" variant="ghost" className="text-red-400 hover:text-red-300 h-7 px-3 text-xs"
                    onClick={() => onReject(w.id)} data-testid={`reject-withdrawal-${w.id}`}>
                    <X className="w-3 h-3 mr-1" /> Reject
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
      {others.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-zinc-500 text-xs font-semibold uppercase tracking-wider">History</h4>
          {others.map(w => (
            <Card key={w.id} className="bg-[#0d0d0d]/40 border-white/[0.06]">
              <CardContent className="p-3 flex items-center justify-between">
                <div>
                  <p className="text-zinc-300 text-sm">{w.family_member_name} - {formatCurrency(w.amount)}</p>
                  <p className={`text-xs ${statusColor(w.status)}`}>{statusLabel(w.status)}</p>
                </div>
                <p className="text-zinc-600 text-xs">{new Date(w.created_at).toLocaleDateString()}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
      {withdrawals.length === 0 && (
        <p className="text-zinc-500 text-sm text-center py-4">No withdrawal requests yet</p>
      )}
    </div>
  );
}

// Main Family Accounts Page
export default function FamilyAccountsPage() {
  const { user, simulatedView } = useAuth();
  const [members, setMembers] = useState([]);
  const [withdrawals, setWithdrawals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editMember, setEditMember] = useState(null);
  const [viewingMember, setViewingMember] = useState(null);
  const [showWithdrawal, setShowWithdrawal] = useState(null);
  const [activeTab, setActiveTab] = useState('members');

  const isSimulating = !!simulatedView;
  const isAdminSimulation = isSimulating && user?.role === 'master_admin';
  const effectiveLicenseType = simulatedView?.license_type || user?.license_type;
  // For admin simulation, we need the REAL licensee user_id (not admin's)
  const simulatedUserId = simulatedView?.memberId || simulatedView?.id;
  const effectiveUserId = simulatedUserId || user?.id;
  const isDemoSimulation = isAdminSimulation && !simulatedUserId;

  const loadData = useCallback(async () => {
    if (isDemoSimulation) {
      setLoading(false);
      return; // Can't load real family data in demo mode
    }
    try {
      const [membersRes, withdrawalsRes] = await Promise.all([
        isAdminSimulation && simulatedUserId
          ? familyAPI.adminGetMembers(simulatedUserId)
          : familyAPI.getMembers(),
        isAdminSimulation
          ? familyAPI.adminGetWithdrawals().catch(() => ({ data: { withdrawals: [] } }))
          : familyAPI.getWithdrawals().catch(() => ({ data: { withdrawals: [] } }))
      ]);
      setMembers(membersRes.data.family_members || []);
      setWithdrawals(withdrawalsRes.data.withdrawals || []);
    } catch (err) {
      if (err?.response?.status !== 403) {
        toast.error(err?.response?.data?.detail || 'Failed to load family accounts');
      }
    } finally {
      setLoading(false);
    }
  }, [isAdminSimulation, simulatedUserId, isDemoSimulation]);

  useEffect(() => { loadData(); }, [loadData]);

  const handleAddOrEdit = async (data, memberId) => {
    if (memberId) {
      // Use admin endpoint for updates when simulating
      if (isAdminSimulation && simulatedUserId) {
        await familyAPI.adminUpdateMember(simulatedUserId, memberId, data);
      } else {
        await familyAPI.updateMember(memberId, data);
      }
      toast.success('Family member updated');
    } else {
      // Use admin endpoint when simulating a real licensee
      if (isAdminSimulation && simulatedUserId) {
        await familyAPI.adminAddMember(simulatedUserId, data);
      } else {
        await familyAPI.addMember(data);
      }
      toast.success('Family member added');
    }
    loadData();
  };

  const handleRemove = async (member) => {
    if (!window.confirm(`Remove ${member.name} from family accounts?`)) return;
    try {
      if (isAdminSimulation && simulatedUserId) {
        await familyAPI.adminRemoveMember(simulatedUserId, member.id);
      } else {
        await familyAPI.removeMember(member.id);
      }
      toast.success('Family member removed');
      loadData();
    } catch (err) {
      toast.error('Failed to remove member');
    }
  };

  const handleApproveWithdrawal = async (id) => {
    try {
      await familyAPI.approveWithdrawal(id);
      toast.success('Withdrawal approved and sent to admin');
      loadData();
    } catch (err) {
      toast.error('Failed to approve withdrawal');
    }
  };

  const handleRejectWithdrawal = async (id) => {
    try {
      await familyAPI.rejectWithdrawal(id, 'Rejected by parent');
      toast.success('Withdrawal rejected');
      loadData();
    } catch (err) {
      toast.error('Failed to reject withdrawal');
    }
  };

  const handleWithdrawalRequest = async (memberId, data) => {
    await familyAPI.requestWithdrawal(memberId, data);
    loadData();
  };

  // Portfolio summary
  const totalFamilyValue = members.reduce((sum, m) => sum + (m.account_value || 0), 0);
  const totalFamilyProfit = members.reduce((sum, m) => sum + (m.profit || 0), 0);
  const pendingWithdrawals = withdrawals.filter(w => w.status === 'pending_parent_approval').length;

  if (viewingMember) {
    return (
      <div className="max-w-5xl mx-auto p-4 md:p-6" data-testid="family-accounts-page">
        <MemberDetailView member={viewingMember} onBack={() => setViewingMember(null)}
          isAdminSimulation={isAdminSimulation} parentUserId={simulatedUserId || effectiveUserId} />
        {!isAdminSimulation && (
          <div className="mt-4">
            <Button variant="outline" className="border-white/[0.08] text-zinc-300 hover:text-white"
              onClick={() => setShowWithdrawal(viewingMember)} data-testid="request-withdrawal-btn">
              <DollarSign className="w-4 h-4 mr-2" /> Request Withdrawal
            </Button>
          </div>
        )}
        <WithdrawalDialog open={!!showWithdrawal} onClose={() => setShowWithdrawal(null)}
          member={showWithdrawal} onSubmit={handleWithdrawalRequest} />
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto p-4 md:p-6" data-testid="family-accounts-page">
      {/* Demo mode warning */}
      {isDemoSimulation && (
        <div className="mb-6 p-4 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400">
          <p className="font-medium">Demo Mode</p>
          <p className="text-sm mt-1">To manage family members, select a specific Honorary FA licensee from the Simulate View dropdown.</p>
        </div>
      )}
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Users className="w-6 h-6 text-orange-400" /> Family Accounts
          </h1>
          <p className="text-zinc-500 text-sm mt-1">Manage family members under your license</p>
        </div>
        {(!isAdminSimulation || (isAdminSimulation && simulatedUserId)) && !isDemoSimulation && (
          <Button onClick={() => { setEditMember(null); setShowForm(true); }}
            className="bg-orange-600 hover:bg-orange-700" data-testid="add-family-member-btn">
            <UserPlus className="w-4 h-4 mr-2" /> Add Member
          </Button>
        )}
      </div>

      {/* Portfolio Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        <Card className="bg-[#0d0d0d]/60 border-white/[0.06]">
          <CardContent className="p-4">
            <p className="text-zinc-500 text-xs">Total Members</p>
            <p className="text-white font-bold text-2xl">{members.length}</p>
          </CardContent>
        </Card>
        <Card className="bg-[#0d0d0d]/60 border-white/[0.06]">
          <CardContent className="p-4">
            <p className="text-zinc-500 text-xs">Family Portfolio</p>
            <p className="text-white font-bold text-lg">{formatCurrency(totalFamilyValue)}</p>
          </CardContent>
        </Card>
        <Card className="bg-[#0d0d0d]/60 border-white/[0.06]">
          <CardContent className="p-4">
            <p className="text-zinc-500 text-xs">Total Profit</p>
            <p className="text-emerald-400 font-bold text-lg">{formatCurrency(totalFamilyProfit)}</p>
          </CardContent>
        </Card>
        <Card className="bg-[#0d0d0d]/60 border-white/[0.06]">
          <CardContent className="p-4">
            <p className="text-zinc-500 text-xs">Pending Approvals</p>
            <p className={`font-bold text-2xl ${pendingWithdrawals > 0 ? 'text-amber-400' : 'text-zinc-600'}`}>
              {pendingWithdrawals}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-4 border-b border-white/[0.06] pb-1">
        {['members', 'withdrawals'].map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
              activeTab === tab ? 'text-white bg-[#1a1a1a]' : 'text-zinc-500 hover:text-zinc-300'
            }`} data-testid={`tab-${tab}`}>
            {tab === 'members' ? `Family Members (${members.length})` : `Withdrawals${pendingWithdrawals > 0 ? ` (${pendingWithdrawals})` : ''}`}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-16">
          <div className="w-8 h-8 border-2 border-orange-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : activeTab === 'members' ? (
        <div>
          {members.length === 0 ? (
            <Card className="bg-[#0d0d0d]/40 border-white/[0.06] border-dashed">
              <CardContent className="flex flex-col items-center justify-center py-16">
                <Users className="w-12 h-12 text-zinc-600 mb-4" />
                <p className="text-zinc-400 text-base mb-2">No family members yet</p>
                <p className="text-zinc-600 text-sm mb-6">Add your first family member to get started</p>
                <Button onClick={() => setShowForm(true)} className="bg-orange-600 hover:bg-orange-700">
                  <UserPlus className="w-4 h-4 mr-2" /> Add Family Member
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {members.map(m => (
                <MemberCard key={m.id} member={m}
                  onView={setViewingMember}
                  onEdit={(member) => { setEditMember(member); setShowForm(true); }}
                  onRemove={handleRemove}
                />
              ))}
            </div>
          )}
        </div>
      ) : (
        <WithdrawalsSection withdrawals={withdrawals}
          onApprove={handleApproveWithdrawal} onReject={handleRejectWithdrawal} />
      )}

      {/* Dialogs */}
      <MemberFormDialog open={showForm} onClose={() => { setShowForm(false); setEditMember(null); }}
        onSubmit={handleAddOrEdit} editMember={editMember} />
    </div>
  );
}
