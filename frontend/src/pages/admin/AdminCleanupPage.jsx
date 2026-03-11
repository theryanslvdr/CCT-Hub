import React, { useState, useEffect, useCallback } from 'react';
import { adminAPI } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Shield, AlertTriangle, UserX, UserCheck, Camera, Clock,
  CheckCircle2, XCircle, ChevronRight, RefreshCw
} from 'lucide-react';
import { toast } from 'sonner';

export const AdminCleanupPage = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [pendingRegs, setPendingRegs] = useState([]);
  const [actioning, setActioning] = useState(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [cleanupRes, regsRes] = await Promise.all([
        adminAPI.getCleanupOverview(),
        adminAPI.getPendingRegistrations(),
      ]);
      setData(cleanupRes.data);
      setPendingRegs(regsRes.data.pending || []);
    } catch {
      toast.error('Failed to load cleanup data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const handleApproveReg = async (userId) => {
    setActioning(userId);
    try {
      await adminAPI.approveRegistration(userId);
      toast.success('Registration approved');
      loadData();
    } catch { toast.error('Failed to approve'); }
    setActioning(null);
  };

  const handleRejectReg = async (userId) => {
    if (!window.confirm('Reject and suspend this user?')) return;
    setActioning(userId);
    try {
      await adminAPI.rejectRegistration(userId);
      toast.success('Registration rejected — user suspended');
      loadData();
    } catch { toast.error('Failed to reject'); }
    setActioning(null);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="w-6 h-6 border-2 border-orange-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-6xl mx-auto" data-testid="admin-cleanup-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Admin Cleanup</h1>
          <p className="text-sm text-zinc-400 mt-1">One-stop review hub for all admin actions</p>
        </div>
        <Button variant="outline" size="sm" onClick={loadData} className="text-zinc-400 border-zinc-700" data-testid="refresh-cleanup">
          <RefreshCw className="w-4 h-4 mr-1" /> Refresh
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {[
          { label: 'Pending Proofs', count: data?.pending_proofs || 0, icon: Camera, color: 'blue' },
          { label: 'Fraud Warnings', count: data?.fraud_warning_count || 0, icon: Shield, color: 'red' },
          { label: 'In Danger', count: data?.in_danger_count || 0, icon: AlertTriangle, color: 'amber' },
          { label: 'Auto-Suspended', count: data?.auto_suspended_count || 0, icon: UserX, color: 'rose' },
          { label: 'Pending Signups', count: data?.pending_registrations || 0, icon: UserCheck, color: 'cyan' },
        ].map((item) => (
          <Card key={item.label} className="glass-card" data-testid={`cleanup-stat-${item.label.toLowerCase().replace(/\s/g, '-')}`}>
            <CardContent className="p-4 text-center">
              <item.icon className={`w-6 h-6 mx-auto mb-2 text-${item.color}-400`} />
              <p className={`text-2xl font-bold font-mono text-${item.color}-400`}>{item.count}</p>
              <p className="text-[10px] text-zinc-500 mt-1">{item.label}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Flagged Registrations */}
      {pendingRegs.length > 0 && (
        <Card className="glass-card border-cyan-500/20">
          <CardHeader className="pb-2">
            <CardTitle className="text-white text-base flex items-center gap-2">
              <UserCheck className="w-4 h-4 text-cyan-400" /> Pending Registration Approvals
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-white/[0.04]">
              {pendingRegs.map(r => (
                <div key={r.id} className="px-4 py-3" data-testid={`pending-reg-${r.id}`}>
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1">
                      <p className="text-sm font-medium text-white">{r.full_name}</p>
                      <p className="text-xs text-zinc-500">{r.email}</p>
                      <div className="mt-1.5 space-y-1">
                        {(r.registration_flags || []).map((flag, i) => (
                          <p key={i} className="text-[11px] text-red-400 flex items-center gap-1">
                            <AlertTriangle className="w-3 h-3 shrink-0" /> {flag}
                          </p>
                        ))}
                      </div>
                    </div>
                    <div className="flex gap-2 shrink-0">
                      <Button
                        size="sm"
                        onClick={() => handleApproveReg(r.id)}
                        disabled={actioning === r.id}
                        className="bg-emerald-600 hover:bg-emerald-700 text-white h-8 text-xs"
                        data-testid={`approve-reg-${r.id}`}
                      >
                        <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Approve
                      </Button>
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={() => handleRejectReg(r.id)}
                        disabled={actioning === r.id}
                        className="h-8 text-xs"
                        data-testid={`reject-reg-${r.id}`}
                      >
                        <XCircle className="w-3.5 h-3.5 mr-1" /> Reject
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Fraud Warnings */}
      {(data?.fraud_warnings || []).length > 0 && (
        <Card className="glass-card border-red-500/20">
          <CardHeader className="pb-2">
            <CardTitle className="text-white text-base flex items-center gap-2">
              <Shield className="w-4 h-4 text-red-400" /> Active Fraud Warnings
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-white/[0.04]">
              {data.fraud_warnings.map(w => (
                <div key={w.user_id} className="px-4 py-3 flex items-center justify-between" data-testid={`fraud-warning-${w.user_id}`}>
                  <div>
                    <p className="text-sm font-medium text-white">{w.user_name}</p>
                    <p className="text-xs text-zinc-500">{w.user_email}</p>
                  </div>
                  <div className="text-right">
                    <span className="text-xs text-red-400 font-mono">{w.fraud_count} rejection{w.fraud_count !== 1 ? 's' : ''}</span>
                    {w.acknowledged ? (
                      <p className="text-[10px] text-amber-400 flex items-center gap-1 justify-end mt-0.5">
                        <Clock className="w-2.5 h-2.5" /> Countdown: {new Date(w.countdown_end).toLocaleDateString()}
                      </p>
                    ) : (
                      <p className="text-[10px] text-zinc-500 mt-0.5">Not yet acknowledged</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* In Danger Members */}
      {(data?.in_danger || []).length > 0 && (
        <Card className="glass-card border-amber-500/20">
          <CardHeader className="pb-2">
            <CardTitle className="text-white text-base flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-400" /> Members In Danger
              <span className="text-xs text-zinc-500 font-normal ml-1">No trades in 7+ days</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-white/[0.04]">
              {data.in_danger.map(m => (
                <div key={m.id} className="px-4 py-2.5 flex items-center justify-between" data-testid={`in-danger-${m.id}`}>
                  <div>
                    <p className="text-sm text-white">{m.name}</p>
                    <p className="text-xs text-zinc-500">{m.email}</p>
                  </div>
                  <ChevronRight className="w-4 h-4 text-zinc-600" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Auto-Suspended */}
      {(data?.auto_suspended || []).length > 0 && (
        <Card className="glass-card border-rose-500/20">
          <CardHeader className="pb-2">
            <CardTitle className="text-white text-base flex items-center gap-2">
              <UserX className="w-4 h-4 text-rose-400" /> Auto-Suspended Members
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-white/[0.04]">
              {data.auto_suspended.map(m => (
                <div key={m.id} className="px-4 py-2.5" data-testid={`auto-suspended-${m.id}`}>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-white">{m.full_name}</p>
                      <p className="text-xs text-zinc-500">{m.email}</p>
                    </div>
                    <p className="text-[10px] text-zinc-500">{m.suspended_at ? new Date(m.suspended_at).toLocaleDateString() : ''}</p>
                  </div>
                  {m.suspension_reason && <p className="text-[10px] text-rose-400 mt-1">{m.suspension_reason}</p>}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* All clear */}
      {!data?.pending_proofs && !data?.fraud_warning_count && !data?.in_danger_count && !data?.auto_suspended_count && !data?.pending_registrations && (
        <Card className="glass-card">
          <CardContent className="py-16 text-center">
            <CheckCircle2 className="w-12 h-12 mx-auto mb-3 text-emerald-500/50" />
            <p className="text-zinc-400 text-lg">All Clear</p>
            <p className="text-sm text-zinc-500 mt-1">No pending items requiring your attention</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default AdminCleanupPage;
