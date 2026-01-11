import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from 'sonner';
import { 
  Users, ShieldCheck, ShieldAlert, Search, UserCog, Eye, Ban, 
  Trash2, Key, Mail, ChevronLeft, ChevronRight, MoreVertical,
  Activity, DollarSign, TrendingUp, Calendar, Crown, Play
} from 'lucide-react';
import api, { adminAPI } from '@/lib/api';

export const AdminMembersPage = () => {
  const { user, isSuperAdmin, isMasterAdmin, simulateMemberView } = useAuth();
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalMembers, setTotalMembers] = useState(0);
  const pageSize = 10;

  // Dialog states
  const [upgradeDialogOpen, setUpgradeDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [tempPasswordDialogOpen, setTempPasswordDialogOpen] = useState(false);
  const [simulateDialogOpen, setSimulateDialogOpen] = useState(false);
  const [selectedMember, setSelectedMember] = useState(null);
  const [memberDetails, setMemberDetails] = useState(null);
  const [simulationData, setSimulationData] = useState(null);
  
  // Form states
  const [newRole, setNewRole] = useState('admin');
  const [secretCode, setSecretCode] = useState('');
  const [editForm, setEditForm] = useState({ full_name: '', timezone: '' });
  const [tempPassword, setTempPassword] = useState('');

  // Check if can see account value (super_admin or master_admin only)
  const canSeeAccountValue = isSuperAdmin() || isMasterAdmin();

  const loadMembers = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: currentPage,
        limit: pageSize,
      });
      if (searchQuery) params.append('search', searchQuery);
      if (roleFilter !== 'all') params.append('role', roleFilter);
      if (statusFilter !== 'all') params.append('status', statusFilter);

      const res = await api.get(`/admin/members?${params}`);
      setMembers(res.data.members);
      setTotalPages(res.data.pages);
      setTotalMembers(res.data.total);
    } catch (error) {
      console.error('Failed to load members:', error);
      toast.error('Failed to load members');
    } finally {
      setLoading(false);
    }
  }, [currentPage, searchQuery, roleFilter, statusFilter]);

  useEffect(() => {
    loadMembers();
  }, [loadMembers]);

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      setCurrentPage(1);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Simulate member view
  const handleSimulateMember = async (member) => {
    try {
      const res = await adminAPI.getMemberSimulation(member.id);
      setSimulationData(res.data);
      setSelectedMember(member);
      setSimulateDialogOpen(true);
    } catch (error) {
      toast.error('Failed to load member simulation data');
    }
  };

  const handleViewMember = async (member) => {
    setSelectedMember(member);
    setViewDialogOpen(true);
    try {
      const res = await api.get(`/admin/members/${member.id}`);
      setMemberDetails(res.data);
    } catch (error) {
      toast.error('Failed to load member details');
    }
  };

  const handleEditMember = (member) => {
    setSelectedMember(member);
    setEditForm({
      full_name: member.full_name || '',
      timezone: member.timezone || 'UTC',
    });
    setEditDialogOpen(true);
  };

  const handleSaveEdit = async () => {
    try {
      await api.put(`/admin/members/${selectedMember.id}`, {
        full_name: editForm.full_name,
        timezone: editForm.timezone,
      });
      toast.success('Member updated successfully');
      setEditDialogOpen(false);
      loadMembers();
    } catch (error) {
      toast.error('Failed to update member');
    }
  };

  const handleUpgradeRole = async () => {
    try {
      await api.post('/admin/upgrade-role', {
        user_id: selectedMember.id,
        new_role: newRole,
        secret_code: newRole === 'super_admin' ? secretCode : undefined,
      });
      toast.success(`User upgraded to ${newRole}!`);
      setUpgradeDialogOpen(false);
      setSecretCode('');
      loadMembers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to upgrade role');
    }
  };

  const handleDowngradeRole = async (userId) => {
    if (!window.confirm('Are you sure you want to downgrade this user to regular user?')) return;
    try {
      await api.post(`/admin/downgrade-role/${userId}`);
      toast.success('User downgraded to regular user');
      loadMembers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to downgrade role');
    }
  };

  const handleSuspendMember = async (member) => {
    const action = member.is_suspended ? 'unsuspend' : 'suspend';
    if (!window.confirm(`Are you sure you want to ${action} this user?`)) return;
    try {
      await api.post(`/admin/members/${member.id}/${action}`);
      toast.success(`User ${action}ed successfully`);
      loadMembers();
    } catch (error) {
      toast.error(`Failed to ${action} user`);
    }
  };

  const handleDeleteMember = async (member) => {
    if (!window.confirm(`Are you sure you want to DELETE ${member.full_name}? This will remove all their data and cannot be undone.`)) return;
    try {
      await api.delete(`/admin/members/${member.id}`);
      toast.success('User deleted');
      loadMembers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete user');
    }
  };

  const handleSetTempPassword = async () => {
    if (!tempPassword || tempPassword.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }
    try {
      await api.post(`/admin/members/${selectedMember.id}/set-temp-password`, {
        temp_password: tempPassword,
      });
      toast.success('Temporary password set. User will need to change it on next login.');
      setTempPasswordDialogOpen(false);
      setTempPassword('');
    } catch (error) {
      toast.error('Failed to set temporary password');
    }
  };

  const getRoleIcon = (role) => {
    switch (role) {
      case 'super_admin': return <ShieldAlert className="w-4 h-4 text-amber-400" />;
      case 'admin': return <ShieldCheck className="w-4 h-4 text-blue-400" />;
      default: return <Users className="w-4 h-4 text-zinc-400" />;
    }
  };

  const getRoleBadgeClass = (role) => {
    switch (role) {
      case 'super_admin': return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
      case 'admin': return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
      default: return 'bg-zinc-500/20 text-zinc-400 border-zinc-500/30';
    }
  };

  const userCount = members.filter(m => m.role === 'user').length;
  const adminCount = members.filter(m => m.role === 'admin').length;
  const superAdminCount = members.filter(m => m.role === 'super_admin').length;

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="glass-card">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-400">Total Members</p>
                <p className="text-3xl font-bold font-mono text-white mt-2">{totalMembers}</p>
              </div>
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center">
                <Users className="w-6 h-6 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="glass-card">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-400">Users</p>
                <p className="text-3xl font-bold font-mono text-white mt-2">{userCount}</p>
              </div>
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-zinc-600 to-zinc-700 flex items-center justify-center">
                <Users className="w-6 h-6 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="glass-card">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-400">Admins</p>
                <p className="text-3xl font-bold font-mono text-blue-400 mt-2">{adminCount}</p>
              </div>
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
                <ShieldCheck className="w-6 h-6 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="glass-card">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-400">Super Admins</p>
                <p className="text-3xl font-bold font-mono text-amber-400 mt-2">{superAdminCount}</p>
              </div>
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center">
                <ShieldAlert className="w-6 h-6 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex flex-col md:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search members by name or email..."
            className="pl-10 input-dark"
            data-testid="member-search-input"
          />
        </div>
        <Select value={roleFilter} onValueChange={(v) => { setRoleFilter(v); setCurrentPage(1); }}>
          <SelectTrigger className="w-40 input-dark" data-testid="role-filter">
            <SelectValue placeholder="All Roles" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Roles</SelectItem>
            <SelectItem value="user">Users</SelectItem>
            <SelectItem value="admin">Admins</SelectItem>
            <SelectItem value="super_admin">Super Admins</SelectItem>
          </SelectContent>
        </Select>
        <Select value={statusFilter} onValueChange={(v) => { setStatusFilter(v); setCurrentPage(1); }}>
          <SelectTrigger className="w-40 input-dark" data-testid="status-filter">
            <SelectValue placeholder="All Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="suspended">Suspended</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Members Table */}
      <Card className="glass-card">
        <CardHeader>
          <CardTitle className="text-white">All Members</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="w-8 h-8 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full data-table">
                  <thead>
                    <tr>
                      <th>Member</th>
                      <th>Email</th>
                      <th>Role</th>
                      <th>Status</th>
                      <th>Joined</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {members.map((member) => (
                      <tr key={member.id} className={member.is_suspended ? 'opacity-50' : ''}>
                        <td>
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center text-white font-medium">
                              {member.full_name?.charAt(0) || 'U'}
                            </div>
                            <span className="font-medium text-white">{member.full_name}</span>
                          </div>
                        </td>
                        <td className="text-zinc-400">{member.email}</td>
                        <td>
                          <span className={`status-badge flex items-center gap-1 ${getRoleBadgeClass(member.role)}`}>
                            {getRoleIcon(member.role)}
                            {member.role?.replace('_', ' ')}
                          </span>
                        </td>
                        <td>
                          <span className={`status-badge ${member.is_suspended ? 'bg-red-500/20 text-red-400' : 'bg-emerald-500/20 text-emerald-400'}`}>
                            {member.is_suspended ? 'Suspended' : 'Active'}
                          </span>
                        </td>
                        <td className="font-mono text-zinc-400">
                          {new Date(member.created_at).toLocaleDateString()}
                        </td>
                        <td>
                          {member.id !== user?.id && (
                            <div className="flex gap-1">
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => handleViewMember(member)}
                                className="text-zinc-400 hover:text-white"
                                data-testid={`view-${member.id}`}
                                title="View Details"
                              >
                                <Eye className="w-4 h-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => handleEditMember(member)}
                                className="text-zinc-400 hover:text-blue-400"
                                data-testid={`edit-${member.id}`}
                                title="Edit"
                              >
                                <UserCog className="w-4 h-4" />
                              </Button>
                              {member.role === 'user' && (
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  onClick={() => { setSelectedMember(member); setUpgradeDialogOpen(true); }}
                                  className="text-zinc-400 hover:text-emerald-400"
                                  data-testid={`upgrade-${member.id}`}
                                  title="Upgrade Role"
                                >
                                  <ShieldCheck className="w-4 h-4" />
                                </Button>
                              )}
                              {member.role !== 'user' && isSuperAdmin && (
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  onClick={() => handleDowngradeRole(member.id)}
                                  className="text-zinc-400 hover:text-amber-400"
                                  data-testid={`downgrade-${member.id}`}
                                  title="Downgrade"
                                >
                                  <Users className="w-4 h-4" />
                                </Button>
                              )}
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => { setSelectedMember(member); setTempPasswordDialogOpen(true); }}
                                className="text-zinc-400 hover:text-cyan-400"
                                title="Set Temp Password"
                              >
                                <Key className="w-4 h-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => handleSuspendMember(member)}
                                className={member.is_suspended ? 'text-emerald-400 hover:text-emerald-300' : 'text-zinc-400 hover:text-amber-400'}
                                title={member.is_suspended ? 'Unsuspend' : 'Suspend'}
                              >
                                <Ban className="w-4 h-4" />
                              </Button>
                              {isSuperAdmin && (
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  onClick={() => handleDeleteMember(member)}
                                  className="text-zinc-400 hover:text-red-400"
                                  data-testid={`delete-${member.id}`}
                                  title="Delete"
                                >
                                  <Trash2 className="w-4 h-4" />
                                </Button>
                              )}
                            </div>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between mt-4 pt-4 border-t border-zinc-800">
                  <p className="text-sm text-zinc-500">
                    Showing {((currentPage - 1) * pageSize) + 1} - {Math.min(currentPage * pageSize, totalMembers)} of {totalMembers}
                  </p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                      disabled={currentPage === 1}
                      className="btn-secondary"
                    >
                      <ChevronLeft className="w-4 h-4" />
                    </Button>
                    <span className="px-3 py-1 text-sm text-zinc-400">
                      Page {currentPage} of {totalPages}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                      disabled={currentPage === totalPages}
                      className="btn-secondary"
                    >
                      <ChevronRight className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* View Member Dialog */}
      <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
        <DialogContent className="glass-card border-zinc-800 max-w-2xl">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Eye className="w-5 h-5" /> Member Details
            </DialogTitle>
          </DialogHeader>
          {memberDetails ? (
            <Tabs defaultValue="profile" className="mt-4">
              <TabsList className="grid w-full grid-cols-3 bg-zinc-900">
                <TabsTrigger value="profile">Profile</TabsTrigger>
                <TabsTrigger value="stats">Statistics</TabsTrigger>
                <TabsTrigger value="activity">Activity</TabsTrigger>
              </TabsList>
              <TabsContent value="profile" className="space-y-4 mt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 rounded-lg bg-zinc-900/50">
                    <p className="text-xs text-zinc-500">Full Name</p>
                    <p className="text-white font-medium">{memberDetails.user.full_name}</p>
                  </div>
                  <div className="p-4 rounded-lg bg-zinc-900/50">
                    <p className="text-xs text-zinc-500">Email</p>
                    <p className="text-white font-medium">{memberDetails.user.email}</p>
                  </div>
                  <div className="p-4 rounded-lg bg-zinc-900/50">
                    <p className="text-xs text-zinc-500">Role</p>
                    <p className="text-white font-medium capitalize">{memberDetails.user.role?.replace('_', ' ')}</p>
                  </div>
                  <div className="p-4 rounded-lg bg-zinc-900/50">
                    <p className="text-xs text-zinc-500">Timezone</p>
                    <p className="text-white font-medium">{memberDetails.user.timezone || 'UTC'}</p>
                  </div>
                  <div className="p-4 rounded-lg bg-zinc-900/50">
                    <p className="text-xs text-zinc-500">LOT Size</p>
                    <p className="text-white font-medium">{memberDetails.user.lot_size || 0.01}</p>
                  </div>
                  <div className="p-4 rounded-lg bg-zinc-900/50">
                    <p className="text-xs text-zinc-500">Joined</p>
                    <p className="text-white font-medium">{new Date(memberDetails.user.created_at).toLocaleDateString()}</p>
                  </div>
                </div>
              </TabsContent>
              <TabsContent value="stats" className="mt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 rounded-lg bg-zinc-900/50 flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
                      <Activity className="w-5 h-5 text-blue-400" />
                    </div>
                    <div>
                      <p className="text-xs text-zinc-500">Total Trades</p>
                      <p className="text-xl font-bold text-white">{memberDetails.stats.total_trades}</p>
                    </div>
                  </div>
                  <div className="p-4 rounded-lg bg-zinc-900/50 flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-emerald-500/20 flex items-center justify-center">
                      <TrendingUp className="w-5 h-5 text-emerald-400" />
                    </div>
                    <div>
                      <p className="text-xs text-zinc-500">Total Profit</p>
                      <p className="text-xl font-bold text-emerald-400">${memberDetails.stats.total_profit.toFixed(2)}</p>
                    </div>
                  </div>
                  <div className="p-4 rounded-lg bg-zinc-900/50 flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-cyan-500/20 flex items-center justify-center">
                      <DollarSign className="w-5 h-5 text-cyan-400" />
                    </div>
                    <div>
                      <p className="text-xs text-zinc-500">Total Deposits</p>
                      <p className="text-xl font-bold text-white">${memberDetails.stats.total_deposits.toFixed(2)}</p>
                    </div>
                  </div>
                  <div className="p-4 rounded-lg bg-zinc-900/50 flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center">
                      <DollarSign className="w-5 h-5 text-purple-400" />
                    </div>
                    <div>
                      <p className="text-xs text-zinc-500">Account Value</p>
                      <p className="text-xl font-bold text-white">${memberDetails.stats.account_value.toFixed(2)}</p>
                    </div>
                  </div>
                </div>
              </TabsContent>
              <TabsContent value="activity" className="mt-4">
                <div className="space-y-4">
                  <h4 className="text-sm font-medium text-zinc-400">Recent Trades</h4>
                  {memberDetails.recent_trades.length > 0 ? (
                    <div className="space-y-2">
                      {memberDetails.recent_trades.slice(0, 5).map((trade) => (
                        <div key={trade.id} className="p-3 rounded-lg bg-zinc-900/50 flex justify-between items-center">
                          <div className="flex items-center gap-3">
                            <span className={`px-2 py-1 rounded text-xs font-medium ${trade.direction === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
                              {trade.direction}
                            </span>
                            <span className="text-zinc-400 text-sm">{new Date(trade.created_at).toLocaleString()}</span>
                          </div>
                          <span className={`font-mono ${trade.actual_profit >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                            {trade.actual_profit >= 0 ? '+' : ''}${trade.actual_profit.toFixed(2)}
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-zinc-500 text-center py-4">No recent trades</p>
                  )}
                </div>
              </TabsContent>
            </Tabs>
          ) : (
            <div className="flex items-center justify-center h-32">
              <div className="w-6 h-6 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Edit Member Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent className="glass-card border-zinc-800">
          <DialogHeader>
            <DialogTitle className="text-white">Edit {selectedMember?.full_name}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div>
              <Label className="text-zinc-300">Full Name</Label>
              <Input
                value={editForm.full_name}
                onChange={(e) => setEditForm({ ...editForm, full_name: e.target.value })}
                className="input-dark mt-1"
                data-testid="edit-name-input"
              />
            </div>
            <div>
              <Label className="text-zinc-300">Timezone</Label>
              <Select value={editForm.timezone} onValueChange={(v) => setEditForm({ ...editForm, timezone: v })}>
                <SelectTrigger className="input-dark mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Asia/Manila">Philippines (GMT+8)</SelectItem>
                  <SelectItem value="Asia/Singapore">Singapore (GMT+8)</SelectItem>
                  <SelectItem value="Asia/Taipei">Taiwan (GMT+8)</SelectItem>
                  <SelectItem value="UTC">UTC</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button onClick={handleSaveEdit} className="w-full btn-primary" data-testid="save-edit-button">
              Save Changes
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Upgrade Role Dialog */}
      <Dialog open={upgradeDialogOpen} onOpenChange={setUpgradeDialogOpen}>
        <DialogContent className="glass-card border-zinc-800">
          <DialogHeader>
            <DialogTitle className="text-white">Upgrade {selectedMember?.full_name}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div>
              <Label className="text-zinc-300">New Role</Label>
              <Select value={newRole} onValueChange={setNewRole}>
                <SelectTrigger className="input-dark mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="admin">Admin</SelectItem>
                  {isSuperAdmin && <SelectItem value="super_admin">Super Admin</SelectItem>}
                </SelectContent>
              </Select>
            </div>
            {newRole === 'super_admin' && (
              <div>
                <Label className="text-zinc-300">Super Admin Secret Code</Label>
                <Input
                  type="password"
                  value={secretCode}
                  onChange={(e) => setSecretCode(e.target.value)}
                  placeholder="Enter secret code"
                  className="input-dark mt-1"
                  data-testid="secret-code-input"
                />
              </div>
            )}
            <Button onClick={handleUpgradeRole} className="w-full btn-primary" data-testid="confirm-upgrade">
              Upgrade to {newRole?.replace('_', ' ')}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Temp Password Dialog */}
      <Dialog open={tempPasswordDialogOpen} onOpenChange={setTempPasswordDialogOpen}>
        <DialogContent className="glass-card border-zinc-800">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Key className="w-5 h-5" /> Set Temporary Password
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <p className="text-sm text-zinc-400">
              Set a temporary password for <strong className="text-white">{selectedMember?.full_name}</strong>. 
              They will be required to change it on their next login.
            </p>
            <div>
              <Label className="text-zinc-300">Temporary Password</Label>
              <Input
                type="password"
                value={tempPassword}
                onChange={(e) => setTempPassword(e.target.value)}
                placeholder="Enter temporary password (min 6 characters)"
                className="input-dark mt-1"
                data-testid="temp-password-input"
              />
            </div>
            <Button onClick={handleSetTempPassword} className="w-full btn-primary" data-testid="confirm-temp-password">
              Set Temporary Password
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};
