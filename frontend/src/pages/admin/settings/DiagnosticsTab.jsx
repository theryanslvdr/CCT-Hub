import React, { useState, useEffect } from 'react';
import { adminAPI, rewardsAPI } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { toast } from 'sonner';
import {
  Database, Loader2, RefreshCw, Search, CheckCircle2, XCircle,
  ArrowRightLeft, Heart, Zap
} from 'lucide-react';

function RewardsPlatformSync() {
  const [syncStatus, setSyncStatus] = useState(null);
  const [syncing, setSyncing] = useState(false);

  const loadSyncStatus = async () => {
    try {
      const res = await rewardsAPI.adminGetSyncStatus();
      setSyncStatus(res.data);
    } catch (error) {
      console.error('Failed to load sync status:', error);
    }
  };

  const handleBatchSync = async () => {
    setSyncing(true);
    try {
      const res = await rewardsAPI.batchSync();
      toast.success(`Synced ${res.data.synced_count || 0} users to rewards platform`);
      loadSyncStatus();
    } catch (error) {
      toast.error('Failed to batch sync');
    } finally {
      setSyncing(false);
    }
  };

  useEffect(() => {
    loadSyncStatus();
  }, []);

  return (
    <div className="space-y-4">
      <h3 className="text-white font-medium flex items-center gap-2">
        <ArrowRightLeft className="w-4 h-4 text-blue-400" /> Rewards Platform Sync
      </h3>
      {syncStatus && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="p-3 rounded-lg bg-zinc-800/50 border border-zinc-700 text-center">
            <p className="text-lg font-bold text-white">{syncStatus.total_users || 0}</p>
            <p className="text-[10px] text-zinc-500 uppercase">Total Users</p>
          </div>
          <div className="p-3 rounded-lg bg-zinc-800/50 border border-zinc-700 text-center">
            <p className="text-lg font-bold text-emerald-400">{syncStatus.synced_users || 0}</p>
            <p className="text-[10px] text-zinc-500 uppercase">Synced</p>
          </div>
          <div className="p-3 rounded-lg bg-zinc-800/50 border border-zinc-700 text-center">
            <p className="text-lg font-bold text-amber-400">{syncStatus.pending_users || 0}</p>
            <p className="text-[10px] text-zinc-500 uppercase">Pending</p>
          </div>
          <div className="p-3 rounded-lg bg-zinc-800/50 border border-zinc-700 text-center">
            <p className="text-lg font-bold text-red-400">{syncStatus.failed_users || 0}</p>
            <p className="text-[10px] text-zinc-500 uppercase">Failed</p>
          </div>
        </div>
      )}
      <Button
        onClick={handleBatchSync}
        disabled={syncing}
        className="gap-2 bg-blue-600 hover:bg-blue-700"
      >
        {syncing ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
        Batch Sync to Rewards Platform
      </Button>
    </div>
  );
}

function ScanAllMembersButton() {
  const [scanning, setScanning] = useState(false);
  const [result, setResult] = useState(null);

  const handleScanAll = async () => {
    setScanning(true);
    setResult(null);
    try {
      const res = await rewardsAPI.retroactiveScanAll();
      setResult(res.data);
      const scanned = res.data.scanned || 0;
      const totalBadges = (res.data.results || []).reduce((sum, r) => sum + (r.badges_awarded || 0), 0);
      toast.success(`Scanned ${scanned} members. ${totalBadges} total badges awarded.`);
    } catch (error) {
      toast.error('Failed to scan members');
    } finally {
      setScanning(false);
    }
  };

  return (
    <div className="space-y-3">
      <h3 className="text-white font-medium flex items-center gap-2">
        <Zap className="w-4 h-4 text-amber-400" /> Retroactive Achievement Scan
      </h3>
      <p className="text-xs text-zinc-500">Scan all members and award any badges they've historically earned.</p>
      <Button
        onClick={handleScanAll}
        disabled={scanning}
        className="gap-2 bg-amber-600 hover:bg-amber-700"
        data-testid="scan-all-members-btn"
      >
        {scanning ? <><Loader2 className="w-4 h-4 animate-spin" /> Scanning...</> : <><Zap className="w-4 h-4" /> Scan All Members</>}
      </Button>
      {result && (
        <div className="p-3 rounded-lg bg-zinc-800/50 border border-zinc-700 text-xs text-zinc-400">
          <p>Scanned: {result.scanned} members</p>
          {result.results?.filter((r) => r.badges_awarded > 0).length > 0 && (
            <div className="mt-1">
              {result.results
                .filter((r) => r.badges_awarded > 0)
                .map((r, i) => (
                  <p key={i} className="text-emerald-400">
                    {r.user_id.slice(0, 8)}...: +{r.badges_awarded} badges
                  </p>
                ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function DiagnosticsTab() {
  const [diagnosticEmail, setDiagnosticEmail] = useState('');
  const [diagnosticResult, setDiagnosticResult] = useState(null);
  const [runningDiagnostic, setRunningDiagnostic] = useState(false);
  const [syncingUser, setSyncingUser] = useState(false);
  const [batchSyncing, setBatchSyncing] = useState(false);
  const [batchSyncResults, setBatchSyncResults] = useState(null);
  const [healthCheckResults, setHealthCheckResults] = useState(null);
  const [runningHealthCheck, setRunningHealthCheck] = useState(false);
  const [lastSyncDate, setLastSyncDate] = useState(null);
  const [nextSyncRecommended, setNextSyncRecommended] = useState(null);

  useEffect(() => {
    const stored = localStorage.getItem('lastLicenseeSyncDate');
    if (stored) {
      const d = new Date(stored);
      setLastSyncDate(d);
      const next = new Date(d);
      next.setDate(next.getDate() + 7);
      setNextSyncRecommended(next);
    }
  }, []);

  const runDiagnostic = async (email) => {
    if (!email) {
      toast.error('Please enter an email address');
      return;
    }
    setRunningDiagnostic(true);
    setDiagnosticResult(null);
    try {
      const response = await fetch(`/api/diagnostic/licensee/${encodeURIComponent(email)}`);
      const data = await response.json();
      setDiagnosticResult(data);
      if (data.errors && data.errors.length > 0) {
        toast.error(`Diagnostic found ${data.errors.length} issue(s)`);
      } else if (data.calculated_value) {
        toast.success(`Diagnostic complete: Account value should be $${data.calculated_value.toLocaleString()}`);
      }
    } catch (error) {
      toast.error('Failed to run diagnostic: ' + error.message);
      setDiagnosticResult({ error: error.message });
    } finally {
      setRunningDiagnostic(false);
    }
  };

  const forceSync = async (userId) => {
    if (!userId) {
      toast.error('No user ID provided');
      return;
    }
    setSyncingUser(true);
    try {
      const response = await adminAPI.forceSyncLicensee(userId);
      toast.success('User data synced successfully!');
      setDiagnosticResult((prev) => ({
        ...prev,
        sync_result: response.data,
        synced_at: new Date().toISOString(),
      }));
    } catch (error) {
      toast.error('Failed to sync: ' + (error.response?.data?.detail || error.message));
    } finally {
      setSyncingUser(false);
    }
  };

  const runHealthCheck = async () => {
    setRunningHealthCheck(true);
    setHealthCheckResults(null);
    try {
      const response = await adminAPI.licenseeHealthCheck();
      setHealthCheckResults(response.data);
      if (response.data.broken > 0) {
        toast.warning(`Found ${response.data.broken} licensee(s) with issues`);
      } else {
        toast.success(`All ${response.data.ok} licensees are healthy!`);
      }
    } catch (error) {
      toast.error('Health check failed: ' + (error.response?.data?.detail || error.message));
    } finally {
      setRunningHealthCheck(false);
    }
  };

  const batchSyncAll = async () => {
    setBatchSyncing(true);
    setBatchSyncResults(null);
    try {
      const response = await adminAPI.batchSyncAllLicensees();
      setBatchSyncResults(response.data);
      const now = new Date();
      localStorage.setItem('lastLicenseeSyncDate', now.toISOString());
      setLastSyncDate(now);
      const nextSync = new Date(now);
      nextSync.setDate(nextSync.getDate() + 7);
      setNextSyncRecommended(nextSync);
      toast.success(`Batch sync complete! ${response.data.synced} licensees updated.`);
    } catch (error) {
      toast.error('Batch sync failed: ' + (error.response?.data?.detail || error.message));
    } finally {
      setBatchSyncing(false);
    }
  };

  return (
    <Card className="glass-card">
      <CardHeader>
        <CardTitle className="text-white flex items-center gap-2">
          <Database className="w-5 h-5 text-orange-400" /> System Diagnostics
        </CardTitle>
        <p className="text-sm text-zinc-400">Diagnose and fix licensee calculation issues. Run health checks and sync data.</p>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Sync Status Banner */}
        <div
          className={`rounded-lg p-4 border ${
            !lastSyncDate
              ? 'bg-amber-500/10 border-amber-500/30'
              : nextSyncRecommended && new Date() > nextSyncRecommended
              ? 'bg-red-500/10 border-red-500/30'
              : 'bg-emerald-500/10 border-emerald-500/30'
          }`}
        >
          <div className="flex items-center justify-between">
            <div>
              <p
                className={`font-medium ${
                  !lastSyncDate
                    ? 'text-amber-400'
                    : nextSyncRecommended && new Date() > nextSyncRecommended
                    ? 'text-red-400'
                    : 'text-emerald-400'
                }`}
              >
                {!lastSyncDate
                  ? 'Never synced - Recommended to run batch sync'
                  : nextSyncRecommended && new Date() > nextSyncRecommended
                  ? 'Sync overdue - Please run batch sync'
                  : 'System in sync'}
              </p>
              <p className="text-sm text-zinc-400 mt-1">
                {lastSyncDate
                  ? `Last sync: ${lastSyncDate.toLocaleDateString()} ${lastSyncDate.toLocaleTimeString()}`
                  : 'No sync history found'}
                {nextSyncRecommended && (
                  <span className="ml-2">Next recommended: {nextSyncRecommended.toLocaleDateString()}</span>
                )}
              </p>
            </div>
            <Button
              onClick={batchSyncAll}
              disabled={batchSyncing}
              className="gap-2 bg-orange-600 hover:bg-orange-700"
              data-testid="batch-sync-all-btn"
            >
              {batchSyncing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" /> Syncing...
                </>
              ) : (
                <>
                  <RefreshCw className="w-4 h-4" /> Batch Sync All
                </>
              )}
            </Button>
          </div>
        </div>

        {batchSyncResults && (
          <div className="p-4 rounded-lg bg-zinc-800/50 border border-zinc-700 text-sm">
            <p className="text-emerald-400 font-medium mb-2">Batch Sync Results:</p>
            <div className="grid grid-cols-3 gap-3">
              <div className="text-center">
                <p className="text-2xl font-bold text-white">{batchSyncResults.synced}</p>
                <p className="text-xs text-zinc-500">Synced</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-red-400">{batchSyncResults.failed}</p>
                <p className="text-xs text-zinc-500">Failed</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-zinc-400">{batchSyncResults.skipped || 0}</p>
                <p className="text-xs text-zinc-500">Skipped</p>
              </div>
            </div>
          </div>
        )}

        {/* Health Check */}
        <div className="flex items-center gap-3">
          <Button
            onClick={runHealthCheck}
            disabled={runningHealthCheck}
            variant="outline"
            className="btn-secondary gap-2"
            data-testid="health-check-btn"
          >
            {runningHealthCheck ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Heart className="w-4 h-4 text-red-400" />
            )}
            Run Health Check
          </Button>
          {healthCheckResults && (
            <div className="text-sm">
              <span className="text-emerald-400">{healthCheckResults.ok} OK</span>
              {healthCheckResults.broken > 0 && (
                <span className="text-red-400 ml-2">{healthCheckResults.broken} Issues</span>
              )}
            </div>
          )}
        </div>

        {/* Diagnostic Search */}
        <div>
          <p className="text-sm font-medium text-zinc-300 mb-2">Licensee Diagnostic</p>
          <div className="flex gap-2">
            <Input
              value={diagnosticEmail}
              onChange={(e) => setDiagnosticEmail(e.target.value)}
              placeholder="Enter licensee email..."
              className="input-dark flex-1"
              data-testid="diagnostic-email-input"
            />
            <Button
              onClick={() => runDiagnostic(diagnosticEmail)}
              disabled={runningDiagnostic || !diagnosticEmail.trim()}
              className="gap-2 bg-orange-600 hover:bg-orange-700"
              data-testid="run-diagnostic-btn"
            >
              {runningDiagnostic ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
              Diagnose
            </Button>
          </div>
        </div>

        {diagnosticResult && !diagnosticResult.error && (
          <div className="p-4 rounded-lg bg-zinc-800/50 border border-zinc-700 text-sm space-y-3">
            <div className="flex items-center justify-between">
              <p className="text-white font-medium">{diagnosticResult.email}</p>
              {diagnosticResult.user_id && (
                <Button
                  onClick={() => forceSync(diagnosticResult.user_id)}
                  disabled={syncingUser}
                  size="sm"
                  className="gap-2 bg-blue-600 hover:bg-blue-700"
                  data-testid="force-sync-btn"
                >
                  {syncingUser ? <Loader2 className="w-3 h-3 animate-spin" /> : <RefreshCw className="w-3 h-3" />}
                  Force Sync
                </Button>
              )}
            </div>
            {diagnosticResult.calculated_value !== undefined && (
              <p className="text-zinc-400">
                Calculated Value:{' '}
                <span className="text-emerald-400 font-bold">
                  ${diagnosticResult.calculated_value?.toLocaleString()}
                </span>
              </p>
            )}
            {diagnosticResult.errors?.length > 0 && (
              <div className="space-y-1">
                {diagnosticResult.errors.map((err, i) => (
                  <div key={i} className="flex items-center gap-2 text-red-400">
                    <XCircle className="w-3 h-3 shrink-0" />
                    <span className="text-xs">{err}</span>
                  </div>
                ))}
              </div>
            )}
            {diagnosticResult.synced_at && (
              <p className="text-xs text-emerald-400">
                <CheckCircle2 className="w-3 h-3 inline mr-1" />
                Synced at {new Date(diagnosticResult.synced_at).toLocaleString()}
              </p>
            )}
            {diagnosticResult.details && (
              <details className="text-xs">
                <summary className="text-zinc-400 cursor-pointer hover:text-zinc-300">Raw diagnostic data</summary>
                <pre className="mt-2 p-2 bg-zinc-900 rounded text-zinc-500 overflow-auto max-h-48">
                  {JSON.stringify(diagnosticResult.details, null, 2)}
                </pre>
              </details>
            )}
          </div>
        )}

        <div className="border-t border-zinc-800 my-4" />

        {/* Rewards Platform Sync Section */}
        <RewardsPlatformSync />

        <div className="border-t border-zinc-800 my-4" />

        {/* Scan All Members */}
        <ScanAllMembersButton />
      </CardContent>
    </Card>
  );
}
