import React, { useState, useEffect, useCallback, useRef } from 'react';
import { referralAPI } from '../../lib/api';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { toast } from 'sonner';
import {
  Users, GitBranch, List, Search, Loader2,
  ChevronDown, ChevronRight, Network, BarChart3, UserCheck, UserPlus
} from 'lucide-react';

// ─── Tree Visualization (Interactive Collapsible) ───

const TreeNode = ({ node, depth = 0 }) => {
  const [expanded, setExpanded] = useState(depth < 2);
  const hasChildren = node.children && node.children.length > 0;

  return (
    <div className="select-none" data-testid={`tree-node-${node.id}`}>
      <div
        className={`flex items-center gap-2 py-2 px-3 rounded-lg cursor-pointer transition-all hover:bg-white/[0.04] ${
          depth === 0 ? 'bg-[#1a1a1a]/40' : ''
        }`}
        style={{ marginLeft: depth * 24 }}
        onClick={() => hasChildren && setExpanded(!expanded)}
      >
        {hasChildren ? (
          expanded ? <ChevronDown className="w-4 h-4 text-zinc-400 shrink-0" /> : <ChevronRight className="w-4 h-4 text-zinc-400 shrink-0" />
        ) : (
          <div className="w-4 h-4 shrink-0" />
        )}

        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
          node.role === 'master_admin' ? 'bg-amber-500/20 text-amber-400 ring-1 ring-amber-500/40' :
          node.role === 'super_admin' ? 'bg-purple-500/20 text-purple-400 ring-1 ring-purple-500/40' :
          node.direct_referrals > 0 ? 'bg-green-500/20 text-green-400 ring-1 ring-green-500/40' :
          'bg-zinc-700 text-zinc-300'
        }`}>
          {node.name?.charAt(0)?.toUpperCase() || '?'}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-white truncate">{node.name}</span>
            {node.referral_code && (
              <span className="text-xs px-1.5 py-0.5 rounded bg-orange-500/10 text-orange-300 font-mono shrink-0">
                {node.referral_code}
              </span>
            )}
          </div>
          <div className="text-xs text-zinc-500 truncate">{node.email}</div>
        </div>

        {hasChildren && (
          <span className="text-xs text-zinc-400 shrink-0 bg-zinc-700/50 px-2 py-0.5 rounded-full">
            {node.direct_referrals} referral{node.direct_referrals !== 1 ? 's' : ''}
          </span>
        )}
      </div>

      {expanded && hasChildren && (
        <div className="border-l border-white/[0.08]/50 ml-6">
          {node.children.map((child) => (
            <TreeNode key={child.id} node={child} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  );
};

// ─── D3 Tree Visualization ───

const D3TreeView = ({ treeData }) => {
  const containerRef = useRef(null);
  const [TreeComponent, setTreeComponent] = useState(null);
  const [translate, setTranslate] = useState({ x: 300, y: 50 });

  useEffect(() => {
    import('react-d3-tree').then(mod => {
      setTreeComponent(() => mod.default);
    });
  }, []);

  useEffect(() => {
    if (containerRef.current) {
      const { width } = containerRef.current.getBoundingClientRect();
      setTranslate({ x: width / 2, y: 50 });
    }
  }, [TreeComponent]);

  if (!TreeComponent) {
    return <div className="flex items-center justify-center h-96 text-zinc-400"><Loader2 className="w-6 h-6 animate-spin mr-2" /> Loading tree...</div>;
  }

  // Convert our data to react-d3-tree format
  const convertToD3 = (nodes) => {
    if (!nodes || nodes.length === 0) return { name: 'No Data', children: [] };

    // If multiple roots, create a virtual root
    if (nodes.length === 1) return convertNode(nodes[0]);

    return {
      name: 'Community',
      attributes: { members: nodes.length },
      children: nodes.filter(n => n.referral_code).map(convertNode),
    };
  };

  const convertNode = (node) => ({
    name: node.name || 'Unknown',
    attributes: {
      code: node.referral_code || 'N/A',
      referrals: node.direct_referrals || 0,
    },
    children: (node.children || []).map(convertNode),
  });

  const d3Data = convertToD3(treeData);

  const renderCustomNode = ({ nodeDatum, toggleNode }) => (
    <g onClick={toggleNode}>
      <circle r={20} fill={nodeDatum.children?.length > 0 ? '#F97316' : '#52525b'} stroke="#71717a" strokeWidth={1} />
      <text fill="white" x={0} y={5} textAnchor="middle" fontSize={10} fontWeight="bold">
        {nodeDatum.name?.charAt(0)?.toUpperCase() || '?'}
      </text>
      <text fill="#d4d4d8" x={30} y={-5} fontSize={11} fontWeight="500">
        {nodeDatum.name}
      </text>
      {nodeDatum.attributes?.code && nodeDatum.attributes.code !== 'N/A' && (
        <text fill="#93c5fd" x={30} y={10} fontSize={9} fontFamily="monospace">
          {nodeDatum.attributes.code}
        </text>
      )}
    </g>
  );

  return (
    <div ref={containerRef} className="w-full h-[500px] bg-[#0d0d0d]/50 rounded-lg border border-white/[0.08]/50 overflow-hidden" data-testid="d3-tree-container">
      <TreeComponent
        data={d3Data}
        translate={translate}
        orientation="vertical"
        pathFunc="step"
        separation={{ siblings: 1.5, nonSiblings: 2 }}
        nodeSize={{ x: 200, y: 80 }}
        renderCustomNodeElement={renderCustomNode}
        collapsible
        zoomable
        draggable
      />
    </div>
  );
};

// ─── Flat Table View ───

const FlatListView = ({ search }) => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await referralAPI.getFlatList({ page, page_size: 20, search: search || undefined });
      setUsers(res.data.users);
      setTotal(res.data.total);
    } catch {
      toast.error('Failed to load referral data');
    } finally {
      setLoading(false);
    }
  }, [page, search]);

  useEffect(() => { load(); }, [load]);

  if (loading) {
    return <div className="flex items-center justify-center py-12 text-zinc-400"><Loader2 className="w-6 h-6 animate-spin mr-2" /> Loading...</div>;
  }

  return (
    <div data-testid="referral-flat-list">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-zinc-400 border-b border-white/[0.08]/50">
              <th className="py-2 px-3">Member</th>
              <th className="py-2 px-3">Referral Code</th>
              <th className="py-2 px-3">Referred By</th>
              <th className="py-2 px-3 text-center">Referrals</th>
              <th className="py-2 px-3">Role</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} className="border-b border-white/[0.06]/50 hover:bg-white/[0.03] transition-colors">
                <td className="py-2.5 px-3">
                  <div className="text-white font-medium">{u.full_name}</div>
                  <div className="text-xs text-zinc-500">{u.email}</div>
                </td>
                <td className="py-2.5 px-3">
                  {u.referral_code ? (
                    <span className="font-mono text-xs px-2 py-0.5 rounded bg-orange-500/10 text-orange-300">{u.referral_code}</span>
                  ) : (
                    <span className="text-zinc-600 text-xs">Not set</span>
                  )}
                </td>
                <td className="py-2.5 px-3">
                  {u.referred_by ? (
                    <span className="font-mono text-xs px-2 py-0.5 rounded bg-green-500/20 text-green-300">{u.referred_by}</span>
                  ) : (
                    <span className="text-zinc-600 text-xs">-</span>
                  )}
                </td>
                <td className="py-2.5 px-3 text-center">
                  <span className={`font-bold ${u.referral_count > 0 ? 'text-green-400' : 'text-zinc-500'}`}>
                    {u.referral_count}
                  </span>
                </td>
                <td className="py-2.5 px-3">
                  <span className={`text-xs px-2 py-0.5 rounded ${
                    u.role === 'master_admin' ? 'bg-amber-500/20 text-amber-300' :
                    u.role === 'super_admin' ? 'bg-purple-500/20 text-purple-300' :
                    u.role?.includes('admin') ? 'bg-orange-500/10 text-orange-300' :
                    'bg-zinc-700 text-zinc-300'
                  }`}>
                    {u.role}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {total > 20 && (
        <div className="flex justify-between items-center mt-4 text-sm text-zinc-400">
          <span>Page {page} of {Math.ceil(total / 20)}</span>
          <div className="flex gap-2">
            <Button size="sm" variant="outline" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>Prev</Button>
            <Button size="sm" variant="outline" onClick={() => setPage(p => p + 1)} disabled={page >= Math.ceil(total / 20)}>Next</Button>
          </div>
        </div>
      )}
    </div>
  );
};

// ─── Main Page ───

const ReferralTreePage = () => {
  const { isAdmin } = useAuth();
  const [view, setView] = useState('tree'); // 'tree' | 'd3' | 'list'
  const [treeData, setTreeData] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    const load = async () => {
      try {
        const res = await referralAPI.getTree();
        setTreeData(res.data.tree);
        setStats(res.data.stats);
      } catch {
        toast.error('Failed to load referral tree');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (!isAdmin()) {
    return <div className="text-center py-12 text-zinc-400">Access denied. Admin only.</div>;
  }

  return (
    <div className="space-y-6" data-testid="referral-tree-page">
      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="glass-card">
            <CardContent className="pt-4 pb-3">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-orange-500/10 flex items-center justify-center">
                  <Users className="w-5 h-5 text-orange-400" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-white">{stats.total_users}</p>
                  <p className="text-xs text-zinc-400">Total Users</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className="glass-card">
            <CardContent className="pt-4 pb-3">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-green-500/20 flex items-center justify-center">
                  <UserCheck className="w-5 h-5 text-green-400" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-white">{stats.users_with_code}</p>
                  <p className="text-xs text-zinc-400">With Code</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className="glass-card">
            <CardContent className="pt-4 pb-3">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center">
                  <UserPlus className="w-5 h-5 text-purple-400" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-white">{stats.users_referred}</p>
                  <p className="text-xs text-zinc-400">Referred</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className="glass-card">
            <CardContent className="pt-4 pb-3">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-amber-500/20 flex items-center justify-center">
                  <BarChart3 className="w-5 h-5 text-amber-400" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-white">{stats.onboarding_completion_rate}%</p>
                  <p className="text-xs text-zinc-400">Onboarded</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* View Toggle + Search */}
      <Card className="glass-card">
        <CardHeader className="pb-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <CardTitle className="text-white flex items-center gap-2 text-lg">
              <GitBranch className="w-5 h-5 text-orange-400" /> Referral Network
            </CardTitle>
            <div className="flex items-center gap-2">
              <div className="flex rounded-lg overflow-hidden border border-white/[0.08]">
                <button
                  data-testid="view-tree-btn"
                  onClick={() => setView('tree')}
                  className={`px-3 py-1.5 text-xs font-medium transition-colors ${
                    view === 'tree' ? 'bg-orange-600 text-white' : 'bg-[#1a1a1a] text-zinc-400 hover:text-white'
                  }`}
                >
                  <Network className="w-3.5 h-3.5 inline mr-1" />Tree
                </button>
                <button
                  data-testid="view-d3-btn"
                  onClick={() => setView('d3')}
                  className={`px-3 py-1.5 text-xs font-medium transition-colors ${
                    view === 'd3' ? 'bg-orange-600 text-white' : 'bg-[#1a1a1a] text-zinc-400 hover:text-white'
                  }`}
                >
                  <GitBranch className="w-3.5 h-3.5 inline mr-1" />Visual
                </button>
                <button
                  data-testid="view-list-btn"
                  onClick={() => setView('list')}
                  className={`px-3 py-1.5 text-xs font-medium transition-colors ${
                    view === 'list' ? 'bg-orange-600 text-white' : 'bg-[#1a1a1a] text-zinc-400 hover:text-white'
                  }`}
                >
                  <List className="w-3.5 h-3.5 inline mr-1" />Table
                </button>
              </div>
            </div>
          </div>
          {view === 'list' && (
            <div className="mt-3 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
              <Input
                data-testid="referral-search-input"
                placeholder="Search by name, email, or code..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9 bg-white/[0.04] border-zinc-600 text-white"
              />
            </div>
          )}
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-16 text-zinc-400">
              <Loader2 className="w-6 h-6 animate-spin mr-2" /> Loading referral data...
            </div>
          ) : (
            <>
              {view === 'tree' && treeData && (
                <div className="space-y-1" data-testid="referral-tree-view">
                  {treeData.filter(n => n.referral_code || n.direct_referrals > 0).length === 0 ? (
                    <div className="text-center py-12 text-zinc-500">
                      <Users className="w-12 h-12 mx-auto mb-3 opacity-30" />
                      <p>No referral codes set yet. Members need to complete onboarding.</p>
                    </div>
                  ) : (
                    treeData.filter(n => n.referral_code || n.direct_referrals > 0).map((node) => (
                      <TreeNode key={node.id} node={node} />
                    ))
                  )}
                </div>
              )}
              {view === 'd3' && treeData && <D3TreeView treeData={treeData} />}
              {view === 'list' && <FlatListView search={search} />}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default ReferralTreePage;
