import React, { useState, useEffect } from 'react';
import { adminAPI } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import { Users, ShieldCheck, ShieldAlert, Search, UserCog } from 'lucide-react';

export const AdminMembersPage = () => {
  const { user: currentUser, isSuperAdmin } = useAuth();
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [upgradeDialogOpen, setUpgradeDialogOpen] = useState(false);
  const [selectedMember, setSelectedMember] = useState(null);
  const [newRole, setNewRole] = useState('admin');
  const [secretCode, setSecretCode] = useState('');

  useEffect(() => {
    loadMembers();
  }, []);

  const loadMembers = async () => {
    try {
      const res = await adminAPI.getMembers();
      setMembers(res.data.members);
    } catch (error) {
      console.error('Failed to load members:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpgradeRole = async () => {
    try {
      await adminAPI.upgradeRole({
        user_id: selectedMember.id,
        new_role: newRole,
        secret_code: newRole === 'super_admin' ? secretCode : undefined,
      });
      toast.success(`User upgraded to ${newRole}!`);
      setUpgradeDialogOpen(false);
      setSelectedMember(null);
      setSecretCode('');
      loadMembers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to upgrade role');
    }
  };

  const handleDowngradeRole = async (userId) => {
    if (!window.confirm('Are you sure you want to downgrade this user to regular user?')) return;
    
    try {
      await adminAPI.downgradeRole(userId);
      toast.success('User downgraded to regular user');
      loadMembers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to downgrade role');
    }
  };

  const filteredMembers = members.filter(m => 
    m.full_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    m.email?.toLowerCase().includes(searchQuery.toLowerCase())
  );

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

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="w-8 h-8 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" /></div>;
  }

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
                <p className="text-3xl font-bold font-mono text-white mt-2">{members.length}</p>
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

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
        <Input
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search members by name or email..."
          className="pl-10 input-dark"
          data-testid="member-search-input"
        />
      </div>

      {/* Members Table */}
      <Card className="glass-card">
        <CardHeader>
          <CardTitle className="text-white">All Members</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full data-table">
              <thead>
                <tr>
                  <th>Member</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Joined</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredMembers.map((member) => (
                  <tr key={member.id}>
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
                    <td className="font-mono text-zinc-400">
                      {new Date(member.created_at).toLocaleDateString()}
                    </td>
                    <td>
                      {member.id !== currentUser?.id && (
                        <div className="flex gap-2">
                          {member.role === 'user' && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => { setSelectedMember(member); setUpgradeDialogOpen(true); }}
                              className="text-blue-400 hover:text-blue-300"
                              data-testid={`upgrade-${member.id}`}
                            >
                              <UserCog className="w-4 h-4 mr-1" /> Upgrade
                            </Button>
                          )}
                          {member.role !== 'user' && isSuperAdmin && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDowngradeRole(member.id)}
                              className="text-red-400 hover:text-red-300"
                              data-testid={`downgrade-${member.id}`}
                            >
                              Downgrade
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
        </CardContent>
      </Card>

      {/* Upgrade Dialog */}
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
    </div>
  );
};
