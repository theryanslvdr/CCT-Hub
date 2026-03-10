import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import api from '@/lib/api';
import {
  Activity, Database, Wifi, Clock, Cpu, HardDrive, MemoryStick,
  Users, Globe, RefreshCw, Server, Zap, AlertTriangle, CheckCircle2,
  XCircle, ChevronDown, ChevronUp, Gauge
} from 'lucide-react';

const MetricCard = ({ icon: Icon, title, value, subtitle, status, className = '' }) => (
  <Card className={`glass-card border-white/[0.06]/50 ${className}`} data-testid={`metric-${title.toLowerCase().replace(/\s/g, '-')}`}>
    <CardContent className="p-4">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2 mb-2">
          <div className={`p-1.5 rounded-lg ${
            status === 'good' ? 'bg-emerald-500/15 text-emerald-400' :
            status === 'warn' ? 'bg-amber-500/15 text-amber-400' :
            status === 'bad' ? 'bg-red-500/15 text-red-400' :
            'bg-orange-500/10 text-orange-400'
          }`}>
            <Icon className="w-4 h-4" />
          </div>
          <span className="text-xs text-zinc-500 uppercase tracking-wider">{title}</span>
        </div>
        {status && (
          <div className={`w-2 h-2 rounded-full ${
            status === 'good' ? 'bg-emerald-400' :
            status === 'warn' ? 'bg-amber-400' :
            status === 'bad' ? 'bg-red-400' : 'bg-orange-400'
          }`} />
        )}
      </div>
      <p className="text-xl font-bold text-white font-mono">{value}</p>
      {subtitle && <p className="text-xs text-zinc-500 mt-1">{subtitle}</p>}
    </CardContent>
  </Card>
);

const LatencyBar = ({ group, data }) => {
  const avg = data?.avg_ms || 0;
  const barColor = avg < 50 ? 'bg-emerald-500' : avg < 200 ? 'bg-amber-500' : 'bg-red-500';
  const maxWidth = Math.min(avg / 5, 100);

  return (
    <div className="flex items-center gap-3 py-1.5" data-testid={`latency-${group}`}>
      <span className="text-xs text-zinc-400 w-16 font-mono">{group}</span>
      <div className="flex-1 h-2 bg-[#1a1a1a] rounded-full overflow-hidden">
        <div className={`h-full ${barColor} rounded-full transition-all duration-500`} style={{ width: `${maxWidth}%` }} />
      </div>
      <span className="text-xs font-mono text-zinc-300 w-16 text-right">
        {avg > 0 ? `${avg.toFixed(0)}ms` : '--'}
      </span>
      <span className="text-xs text-zinc-600 w-12 text-right">
        {data?.samples || 0}req
      </span>
    </div>
  );
};

const ServiceBadge = ({ name, status }) => (
  <div className="flex items-center justify-between py-1.5 px-3 rounded-lg bg-[#0d0d0d]/50" data-testid={`service-${name}`}>
    <span className="text-sm text-zinc-300 capitalize">{name.replace(/_/g, ' ')}</span>
    {status === 'configured' ? (
      <Badge variant="outline" className="border-emerald-500/30 text-emerald-400 text-xs">
        <CheckCircle2 className="w-3 h-3 mr-1" /> Active
      </Badge>
    ) : (
      <Badge variant="outline" className="border-white/[0.08] text-zinc-500 text-xs">
        <XCircle className="w-3 h-3 mr-1" /> Off
      </Badge>
    )}
  </div>
);

const CollectionRow = ({ name, count }) => (
  <div className="flex items-center justify-between py-1 px-2">
    <span className="text-xs text-zinc-400 font-mono">{name}</span>
    <span className="text-xs font-mono text-white">{(count || 0).toLocaleString()}</span>
  </div>
);

export default function SystemHealthPage() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [showCollections, setShowCollections] = useState(false);

  const fetchHealth = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    try {
      const res = await api.get('/admin/system-health');
      setHealth(res.data);
    } catch (err) {
      console.error('Failed to fetch system health:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchHealth();
  }, [fetchHealth]);

  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => fetchHealth(true), 10000);
    return () => clearInterval(interval);
  }, [autoRefresh, fetchHealth]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64" data-testid="health-loading">
        <RefreshCw className="w-8 h-8 animate-spin text-orange-400" />
      </div>
    );
  }

  if (!health) {
    return (
      <div className="text-center py-16 text-zinc-500" data-testid="health-error">
        <AlertTriangle className="w-12 h-12 mx-auto mb-4 text-red-400" />
        <p>Failed to load system health data</p>
        <Button className="mt-4" onClick={() => fetchHealth()}>Retry</Button>
      </div>
    );
  }

  const sys = health.system || {};
  const db = health.database || {};
  const ws = health.websockets || {};
  const users = health.users || {};
  const mem = sys.memory || {};
  const disk = sys.disk || {};
  const proc = sys.process || {};

  return (
    <div className="space-y-6 max-w-7xl mx-auto" data-testid="system-health-dashboard">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Gauge className="w-6 h-6 text-orange-400" />
            System Health
          </h1>
          <p className="text-sm text-zinc-500 mt-1">
            Build {health.build?.version?.slice(0, 8)} &middot; Up {health.uptime?.formatted}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            className={`border-white/[0.08] text-xs ${autoRefresh ? 'text-emerald-400 border-emerald-500/30' : 'text-zinc-400'}`}
            onClick={() => setAutoRefresh(!autoRefresh)}
            data-testid="auto-refresh-toggle"
          >
            <Activity className={`w-3.5 h-3.5 mr-1 ${autoRefresh ? 'animate-pulse' : ''}`} />
            {autoRefresh ? 'Live' : 'Auto'}
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="border-white/[0.08] text-zinc-400 text-xs"
            onClick={() => fetchHealth(true)}
            disabled={refreshing}
            data-testid="refresh-button"
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-1 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Top Metrics Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <MetricCard
          icon={Clock}
          title="Uptime"
          value={health.uptime?.formatted || '--'}
          subtitle={`Since ${new Date(health.uptime?.started_at).toLocaleDateString()}`}
          status="good"
        />
        <MetricCard
          icon={Database}
          title="DB Ping"
          value={`${db.ping_ms || '--'}ms`}
          subtitle={`${db.collections_count || 0} collections`}
          status={db.ping_ms < 10 ? 'good' : db.ping_ms < 50 ? 'warn' : 'bad'}
        />
        <MetricCard
          icon={Wifi}
          title="WebSocket"
          value={ws.total_connections || 0}
          subtitle={`${ws.unique_users || 0} users, ${ws.admin_connections || 0} admins`}
          status="good"
        />
        <MetricCard
          icon={Users}
          title="Active Users"
          value={users.active_24h || 0}
          subtitle={`${users.total || 0} total, ${users.active_members || 0} members`}
          status="good"
        />
      </div>

      {/* System Resources */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
        <Card className="glass-card border-white/[0.06]/50" data-testid="cpu-card">
          <CardHeader className="pb-2 px-4 pt-4">
            <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
              <Cpu className="w-4 h-4 text-orange-400" /> CPU
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4">
            <div className="text-3xl font-bold font-mono text-white">{sys.cpu_percent || 0}%</div>
            <Progress value={sys.cpu_percent || 0} className="mt-2 h-1.5" />
            <p className="text-xs text-zinc-500 mt-1">{proc.threads || 0} threads</p>
          </CardContent>
        </Card>

        <Card className="glass-card border-white/[0.06]/50" data-testid="memory-card">
          <CardHeader className="pb-2 px-4 pt-4">
            <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
              <MemoryStick className="w-4 h-4 text-purple-400" /> Memory
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4">
            <div className="text-3xl font-bold font-mono text-white">{mem.percent || 0}%</div>
            <Progress value={mem.percent || 0} className="mt-2 h-1.5" />
            <p className="text-xs text-zinc-500 mt-1">
              {mem.used_gb || 0}GB / {mem.total_gb || 0}GB &middot; Process: {proc.rss_mb || 0}MB
            </p>
          </CardContent>
        </Card>

        <Card className="glass-card border-white/[0.06]/50" data-testid="disk-card">
          <CardHeader className="pb-2 px-4 pt-4">
            <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
              <HardDrive className="w-4 h-4 text-emerald-400" /> Disk
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4">
            <div className="text-3xl font-bold font-mono text-white">{disk.percent || 0}%</div>
            <Progress value={disk.percent || 0} className="mt-2 h-1.5" />
            <p className="text-xs text-zinc-500 mt-1">
              {disk.used_gb || 0}GB / {disk.total_gb || 0}GB
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Route Latencies & DB Details */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <Card className="glass-card border-white/[0.06]/50" data-testid="latency-card">
          <CardHeader className="pb-2 px-4 pt-4">
            <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
              <Zap className="w-4 h-4 text-amber-400" /> Route Latencies
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4">
            {health.route_latencies && Object.entries(health.route_latencies).map(([group, data]) => (
              <LatencyBar key={group} group={group} data={data} />
            ))}
          </CardContent>
        </Card>

        <Card className="glass-card border-white/[0.06]/50" data-testid="database-card">
          <CardHeader className="pb-2 px-4 pt-4">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                <Database className="w-4 h-4 text-orange-400" /> Database
              </CardTitle>
              <Badge variant="outline" className={`text-xs ${
                db.status === 'healthy' ? 'border-emerald-500/30 text-emerald-400' : 'border-red-500/30 text-red-400'
              }`}>
                {db.status || 'unknown'}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="px-4 pb-4 space-y-3">
            <div className="grid grid-cols-3 gap-2 text-center">
              <div className="p-2 rounded-lg bg-[#0d0d0d]/50">
                <p className="text-lg font-mono font-bold text-white">{db.connections?.current || 0}</p>
                <p className="text-[10px] text-zinc-500">Current</p>
              </div>
              <div className="p-2 rounded-lg bg-[#0d0d0d]/50">
                <p className="text-lg font-mono font-bold text-white">{db.connections?.available || 0}</p>
                <p className="text-[10px] text-zinc-500">Available</p>
              </div>
              <div className="p-2 rounded-lg bg-[#0d0d0d]/50">
                <p className="text-lg font-mono font-bold text-emerald-400">{db.ping_ms || '--'}ms</p>
                <p className="text-[10px] text-zinc-500">Ping</p>
              </div>
            </div>

            <button
              onClick={() => setShowCollections(!showCollections)}
              className="w-full flex items-center justify-between py-1.5 px-2 text-xs text-zinc-400 hover:text-zinc-300 transition-colors"
              data-testid="toggle-collections"
            >
              <span>Document Counts ({Object.keys(db.document_counts || {}).length} collections)</span>
              {showCollections ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>
            {showCollections && db.document_counts && (
              <div className="border border-white/[0.06] rounded-lg p-1 space-y-0.5">
                {Object.entries(db.document_counts)
                  .sort((a, b) => b[1] - a[1])
                  .map(([name, count]) => (
                    <CollectionRow key={name} name={name} count={count} />
                  ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* External Services */}
      <Card className="glass-card border-white/[0.06]/50" data-testid="services-card">
        <CardHeader className="pb-2 px-4 pt-4">
          <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
            <Globe className="w-4 h-4 text-cyan-400" /> External Services
          </CardTitle>
        </CardHeader>
        <CardContent className="px-4 pb-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
            {health.external_services && Object.entries(health.external_services).map(([name, status]) => (
              <ServiceBadge key={name} name={name} status={status} />
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Recent Errors */}
      {health.recent_errors?.count > 0 && (
        <Card className="glass-card border-red-900/30" data-testid="errors-card">
          <CardHeader className="pb-2 px-4 pt-4">
            <CardTitle className="text-sm text-red-400 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4" /> Recent Errors ({health.recent_errors.count})
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4">
            <div className="space-y-2">
              {health.recent_errors.errors.map((err, i) => (
                <div key={i} className="p-2 rounded bg-red-500/5 border border-red-500/10 text-xs">
                  <p className="text-red-400 font-mono">{err.message || JSON.stringify(err)}</p>
                  {err.timestamp && <p className="text-zinc-600 mt-0.5">{new Date(err.timestamp).toLocaleString()}</p>}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
