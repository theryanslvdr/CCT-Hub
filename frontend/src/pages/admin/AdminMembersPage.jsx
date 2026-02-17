import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from 'sonner';
import { MobileNotice } from '@/components/MobileNotice';
import { 
  Users, ShieldCheck, ShieldAlert, Search, UserCog, Eye, Ban, 
  Trash2, Key, Mail, ChevronLeft, ChevronRight, MoreVertical,
  Activity, DollarSign, TrendingUp, Calendar, Crown, Play,
  Award, FileCheck, AlertTriangle, RefreshCw, Loader2, AlertCircle,
  UserX, UserCheck, ArrowUpDown, ArrowUp, ArrowDown, Download, Radio
} from 'lucide-react';
import api, { adminAPI } from '@/lib/api';

export const AdminMembersPage = () => {
  const { user, isSuperAdmin, isMasterAdmin, simulateMemberView } = useAuth();
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortByAccountValue, setSortByAccountValue] = useState('none'); // 'none', 'asc', 'desc'
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
  const [licenseDialogOpen, setLicenseDialogOpen] = useState(false);
  const [selectedMember, setSelectedMember] = useState(null);
  const [memberDetails, setMemberDetails] = useState(null);
  const [simulationData, setSimulationData] = useState(null);
  
  // View dialog editing states
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [viewEditForm, setViewEditForm] = useState({
    full_name: '',
    timezone: ''
  });
  
  // License state
  const [licenses, setLicenses] = useState([]);
  const [memberLicense, setMemberLicense] = useState(null);
  const [licenseForm, setLicenseForm] = useState({
    license_type: 'extended',
    starting_amount: '',
    start_date: new Date().toISOString().split('T')[0],
    notes: ''
  });
  const [licenseLoading, setLicenseLoading] = useState(false);
  
  // Change License Type state
  const [changeLicenseDialogOpen, setChangeLicenseDialogOpen] = useState(false);
  const [changeLicenseForm, setChangeLicenseForm] = useState({
    new_license_type: 'extended',
    new_starting_amount: '',
    notes: ''
  });
  const [changingLicense, setChangingLicense] = useState(false);
  
  // Diagnostic state
  const [diagnosticDialogOpen, setDiagnosticDialogOpen] = useState(false);
  const [diagnosticData, setDiagnosticData] = useState(null);
  const [diagnosticLoading, setDiagnosticLoading] = useState(false);
  const [editingTradingStart, setEditingTradingStart] = useState(false);
  const [newTradingStartDate, setNewTradingStartDate] = useState('');
  
  // Form states
  const [newRole, setNewRole] = useState('basic_admin');
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
      if (sortByAccountValue !== 'none') params.append('sort_account_value', sortByAccountValue);

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
  }, [currentPage, searchQuery, roleFilter, statusFilter, sortByAccountValue]);

  const loadLicenses = useCallback(async () => {
    if (!isMasterAdmin()) return;
    try {
      const res = await adminAPI.getLicenses();
      setLicenses(res.data.licenses || []);
    } catch (error) {
      console.error('Failed to load licenses:', error);
    }
  }, [isMasterAdmin]);

  useEffect(() => {
    loadMembers();
    loadLicenses();
  }, [loadMembers, loadLicenses]);

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      setCurrentPage(1);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Get license for a member
  const getMemberLicense = (memberId) => {
    return licenses.find(l => l.user_id === memberId && l.is_active);
  };

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
    setIsEditingProfile(false);
    setViewEditForm({
      full_name: member.full_name || '',
      timezone: member.timezone || 'UTC'
    });
    try {
      const res = await api.get(`/admin/members/${member.id}`);
      setMemberDetails(res.data);
      // Also load license info
      const memberLic = licenses.find(l => l.user_id === member.id && l.is_active);
      setMemberLicense(memberLic || null);
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

  const handleSaveViewEdit = async () => {
    try {
      await api.put(`/admin/members/${selectedMember.id}`, {
        full_name: viewEditForm.full_name,
        timezone: viewEditForm.timezone,
      });
      toast.success('Profile updated successfully');
      setIsEditingProfile(false);
      // Update local state
      setMemberDetails(prev => ({
        ...prev,
        user: {
          ...prev.user,
          full_name: viewEditForm.full_name,
          timezone: viewEditForm.timezone
        }
      }));
      loadMembers();
    } catch (error) {
      toast.error('Failed to update profile');
    }
  };

  const handleUpgradeRole = async () => {
    try {
      // Master Admin doesn't need secret code
      const needsSecretCode = newRole === 'super_admin' && !isMasterAdmin();
      await api.post('/admin/upgrade-role', {
        user_id: selectedMember.id,
        new_role: newRole,
        secret_code: needsSecretCode ? secretCode : undefined,
      });
      toast.success(`User promoted to ${newRole.replace('_', ' ')}!`);
      setUpgradeDialogOpen(false);
      setSecretCode('');
      loadMembers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to promote user');
    }
  };

  const handleDowngradeRole = async (userId) => {
    if (!window.confirm('Are you sure you want to downgrade this user to member?')) return;
    try {
      await api.post(`/admin/downgrade-role/${userId}`);
      toast.success('User downgraded to member');
      loadMembers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to downgrade role');
    }
  };

  const handleDeactivateUser = async (userId) => {
    if (!window.confirm('Are you sure you want to deactivate this user? They will not be able to login until reactivated.')) return;
    try {
      await api.post(`/admin/deactivate/${userId}`);
      toast.success('User has been deactivated');
      loadMembers();
      // Refresh member details if viewing
      if (selectedMember?.id === userId) {
        const res = await api.get(`/admin/members/${userId}`);
        setMemberDetails(res.data);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to deactivate user');
    }
  };

  const handleReactivateUser = async (userId) => {
    try {
      await api.post(`/admin/reactivate/${userId}`);
      toast.success('User has been reactivated');
      loadMembers();
      // Refresh member details if viewing
      if (selectedMember?.id === userId) {
        const res = await api.get(`/admin/members/${userId}`);
        setMemberDetails(res.data);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to reactivate user');
    }
  };

  const handleOpenChangeLicense = () => {
    if (!memberLicense) return;
    setChangeLicenseForm({
      new_license_type: memberLicense.license_type === 'extended' ? 'honorary' : 'extended',
      new_starting_amount: memberLicense.current_amount?.toString() || memberLicense.starting_amount?.toString() || '',
      notes: ''
    });
    setChangeLicenseDialogOpen(true);
  };

  const handleChangeLicenseType = async () => {
    if (!changeLicenseForm.new_starting_amount || parseFloat(changeLicenseForm.new_starting_amount) <= 0) {
      toast.error('Please enter a valid starting amount');
      return;
    }

    setChangingLicense(true);
    try {
      await adminAPI.changeLicenseType(memberLicense.id, {
        new_license_type: changeLicenseForm.new_license_type,
        new_starting_amount: parseFloat(changeLicenseForm.new_starting_amount),
        notes: changeLicenseForm.notes
      });
      toast.success(`License changed to ${changeLicenseForm.new_license_type}`);
      setChangeLicenseDialogOpen(false);
      // Reload license info
      const licRes = await adminAPI.getLicenses();
      setLicenses(licRes.data.licenses || []);
      const updatedLicense = licRes.data.licenses.find(l => l.user_id === selectedMember?.id && l.is_active);
      setMemberLicense(updatedLicense || null);
      loadMembers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to change license type');
    } finally {
      setChangingLicense(false);
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

  // License management
  const handleOpenLicenseDialog = (member) => {
    setSelectedMember(member);
    const existingLicense = getMemberLicense(member.id);
    setMemberLicense(existingLicense);
    if (!existingLicense) {
      setLicenseForm({
        license_type: 'extended',
        starting_amount: member.account_value?.toString() || '',
        start_date: new Date().toISOString().split('T')[0],
        notes: ''
      });
    }
    setLicenseDialogOpen(true);
  };

  const handleCreateLicense = async () => {
    if (!licenseForm.starting_amount || parseFloat(licenseForm.starting_amount) <= 0) {
      toast.error('Please enter a valid starting amount');
      return;
    }
    setLicenseLoading(true);
    try {
      await adminAPI.createLicense({
        user_id: selectedMember.id,
        license_type: licenseForm.license_type,
        starting_amount: parseFloat(licenseForm.starting_amount),
        start_date: licenseForm.start_date,
        notes: licenseForm.notes
      });
      toast.success(`${licenseForm.license_type === 'extended' ? 'Extended' : 'Honorary'} License assigned to ${selectedMember.full_name}`);
      setLicenseDialogOpen(false);
      loadLicenses();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create license');
    } finally {
      setLicenseLoading(false);
    }
  };

  const handleRemoveLicense = async () => {
    if (!memberLicense) return;
    if (!window.confirm(`Remove ${memberLicense.license_type} license from ${selectedMember.full_name}? This will revert them to standard calculations.`)) return;
    
    setLicenseLoading(true);
    try {
      await adminAPI.deleteLicense(memberLicense.id);
      toast.success('License removed successfully');
      setLicenseDialogOpen(false);
      setMemberLicense(null);
      loadLicenses();
    } catch (error) {
      toast.error('Failed to remove license');
    } finally {
      setLicenseLoading(false);
    }
  };

  // Run diagnostic for a member's account
  const handleRunDiagnostic = async (userId) => {
    setDiagnosticLoading(true);
    setDiagnosticData(null);
    setDiagnosticDialogOpen(true);
    try {
      // Use POST to avoid any potential caching issues with GET
      const response = await api.post(`/admin/run-diagnostic/${userId}`);
      setDiagnosticData(response.data);
    } catch (error) {
      console.error('Failed to run diagnostic:', error);
      toast.error('Failed to run diagnostic: ' + (error.response?.data?.detail || error.message));
      setDiagnosticDialogOpen(false);
    } finally {
      setDiagnosticLoading(false);
    }
  };

  // Copy text to clipboard
  const copyToClipboard = (text, label) => {
    navigator.clipboard.writeText(text);
    toast.success(`${label} copied to clipboard`);
  };

  // Export debug data as downloadable JSON
  const handleExportDebugData = async (userId, userName) => {
    try {
      toast.info('Exporting debug data...');
      const response = await api.get(`/admin/export-debug-data/${userId}`);
      const blob = new Blob([JSON.stringify(response.data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `debug-export-${(userName || userId).replace(/\s+/g, '_')}-${new Date().toISOString().slice(0,10)}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success('Debug data exported successfully');
    } catch (error) {
      console.error('Failed to export debug data:', error);
      toast.error('Failed to export: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Auto-fix trading start date based on first trade
  const handleAutoFixTradingStart = async (userId) => {
    try {
      const response = await api.post(`/admin/members/${userId}/fix-trading-start`);
      toast.success(response.data.message);
      // Refresh diagnostic data
      handleRunDiagnostic(userId);
    } catch (error) {
      console.error('Failed to fix trading start date:', error);
      toast.error(error.response?.data?.detail || 'Failed to fix trading start date');
    }
  };

  // Manually update trading start date
  const handleUpdateTradingStartDate = async (userId, newDate) => {
    try {
      await api.put(`/admin/members/${userId}`, { trading_start_date: newDate });
      toast.success(`Trading start date updated to ${newDate}`);
      // Refresh diagnostic data
      handleRunDiagnostic(userId);
    } catch (error) {
      console.error('Failed to update trading start date:', error);
      toast.error(error.response?.data?.detail || 'Failed to update trading start date');
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

  const getLicenseBadge = (memberId) => {
    const license = getMemberLicense(memberId);
    if (!license) return null;
    
    if (license.license_type === 'extended') {
      return (
        <span className="ml-2 px-1.5 py-0.5 rounded text-[10px] font-medium bg-purple-500/20 text-purple-400 border border-purple-500/30">
          EXT
        </span>
      );
    }
    if (license.license_type === 'honorary') {
      return (
        <span className="ml-2 px-1.5 py-0.5 rounded text-[10px] font-medium bg-amber-500/20 text-amber-400 border border-amber-500/30">
          HON
        </span>
      );
    }
    if (license.license_type === 'honorary_fa') {
      return (
        <span className="ml-2 px-1.5 py-0.5 rounded text-[10px] font-medium bg-blue-500/20 text-blue-400 border border-blue-500/30">
          FA
        </span>
      );
    }
    return null;
  };

  // Count members (merged "user" into "member")
  const memberCount = members.filter(m => m.role === 'member').length;
  const adminCount = members.filter(m => m.role === 'admin').length;
  const superAdminCount = members.filter(m => m.role === 'super_admin').length;

  return (
    <MobileNotice featureName="Member Management" showOnMobile={true}>
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
                <p className="text-sm text-zinc-400">Members</p>
                <p className="text-3xl font-bold font-mono text-white mt-2">{memberCount}</p>
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
                <p className="text-sm text-zinc-400">Licensed Users</p>
                <p className="text-3xl font-bold font-mono text-purple-400 mt-2">
                  {licenses.filter(l => l.is_active).length}
                </p>
              </div>
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                <Award className="w-6 h-6 text-white" />
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
            <SelectItem value="member">Members</SelectItem>
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
            <SelectItem value="deactivated">Deactivated</SelectItem>
          </SelectContent>
        </Select>
        {canSeeAccountValue && (
          <Select value={sortByAccountValue} onValueChange={(v) => { setSortByAccountValue(v); setCurrentPage(1); }}>
            <SelectTrigger className="w-48 input-dark" data-testid="sort-account-value">
              <SelectValue placeholder="Sort by Account" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">
                <div className="flex items-center gap-2">
                  <ArrowUpDown className="w-4 h-4" /> Default Order
                </div>
              </SelectItem>
              <SelectItem value="asc">
                <div className="flex items-center gap-2">
                  <ArrowUp className="w-4 h-4" /> Account Value: Low → High
                </div>
              </SelectItem>
              <SelectItem value="desc">
                <div className="flex items-center gap-2">
                  <ArrowDown className="w-4 h-4" /> Account Value: High → Low
                </div>
              </SelectItem>
            </SelectContent>
          </Select>
        )}
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
                      {canSeeAccountValue && <th>Account Value</th>}
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
                            <span className="font-medium text-white">
                              {member.full_name}
                              {getLicenseBadge(member.id)}
                            </span>
                          </div>
                        </td>
                        <td className="text-zinc-400">{member.email}</td>
                        <td>
                          <span className={`status-badge flex items-center gap-1 ${getRoleBadgeClass(member.role)}`}>
                            {getRoleIcon(member.role)}
                            {member.role?.replace('_', ' ')}
                          </span>
                        </td>
                        {canSeeAccountValue && (
                          <td className="font-mono text-emerald-400">
                            ${member.account_value?.toFixed(2) || '0.00'}
                          </td>
                        )}
                        <td>
                          <span className={`status-badge ${
                            member.is_deactivated 
                              ? 'bg-zinc-500/20 text-zinc-400' 
                              : member.is_suspended 
                                ? 'bg-red-500/20 text-red-400' 
                                : 'bg-emerald-500/20 text-emerald-400'
                          }`}>
                            {member.is_deactivated ? 'Deactivated' : member.is_suspended ? 'Suspended' : 'Active'}
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
                              {isSuperAdmin() && (
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

      {/* View Member Dialog - Enhanced with Edit, License, Simulate, Upgrade */}
      <Dialog open={viewDialogOpen} onOpenChange={(open) => { setViewDialogOpen(open); if (!open) setIsEditingProfile(false); }}>
        <DialogContent className="glass-card border-zinc-800 max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Eye className="w-5 h-5" /> Member Details - {selectedMember?.full_name}
              {getLicenseBadge(selectedMember?.id)}
            </DialogTitle>
          </DialogHeader>
          {memberDetails ? (
            <Tabs defaultValue="profile" className="mt-4">
              <TabsList className="grid w-full grid-cols-4 bg-zinc-900">
                <TabsTrigger value="profile">Profile</TabsTrigger>
                <TabsTrigger value="stats">Statistics</TabsTrigger>
                <TabsTrigger value="activity">Activity</TabsTrigger>
                <TabsTrigger value="actions">Actions</TabsTrigger>
              </TabsList>
              
              {/* Profile Tab - Editable */}
              <TabsContent value="profile" className="space-y-4 mt-4">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm font-medium text-zinc-400">Profile Information</h4>
                  {!isEditingProfile ? (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setViewEditForm({
                          full_name: memberDetails.user.full_name || '',
                          timezone: memberDetails.user.timezone || 'UTC'
                        });
                        setIsEditingProfile(true);
                      }}
                      className="text-blue-400 hover:text-blue-300"
                    >
                      <UserCog className="w-4 h-4 mr-1" /> Edit
                    </Button>
                  ) : (
                    <div className="flex gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setIsEditingProfile(false)}
                        className="text-zinc-400 hover:text-white"
                      >
                        Cancel
                      </Button>
                      <Button
                        size="sm"
                        onClick={handleSaveViewEdit}
                        className="btn-primary"
                      >
                        Save
                      </Button>
                    </div>
                  )}
                </div>
                
                {isEditingProfile ? (
                  <div className="space-y-4">
                    <div>
                      <Label className="text-zinc-300">Full Name</Label>
                      <Input
                        value={viewEditForm.full_name}
                        onChange={(e) => setViewEditForm({ ...viewEditForm, full_name: e.target.value })}
                        className="input-dark mt-1"
                      />
                    </div>
                    <div>
                      <Label className="text-zinc-300">Email</Label>
                      <Input
                        value={memberDetails.user.email}
                        disabled
                        className="input-dark mt-1 opacity-50"
                      />
                    </div>
                    <div>
                      <Label className="text-zinc-300">Timezone</Label>
                      <Select value={viewEditForm.timezone} onValueChange={(v) => setViewEditForm({ ...viewEditForm, timezone: v })}>
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
                    <div className="grid grid-cols-2 gap-4">
                      <div className="p-4 rounded-lg bg-zinc-900/50">
                        <p className="text-xs text-zinc-500">Role</p>
                        <p className="text-white font-medium capitalize">{memberDetails.user.role?.replace('_', ' ')}</p>
                      </div>
                      <div className="p-4 rounded-lg bg-zinc-900/50">
                        <p className="text-xs text-zinc-500">LOT Size</p>
                        <p className="text-white font-medium">
                          {((memberDetails.stats?.account_value || 0) / 980).toFixed(2)}
                        </p>
                        <p className="text-xs text-zinc-500 mt-1">Based on ${(memberDetails.stats?.account_value || 0).toLocaleString()}</p>
                      </div>
                    </div>
                  </div>
                ) : (
                  <>
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
                      <p className="text-white font-medium">
                        {((memberDetails.stats?.account_value || 0) / 980).toFixed(2)}
                      </p>
                      <p className="text-xs text-zinc-500 mt-1">Based on ${(memberDetails.stats?.account_value || 0).toLocaleString()}</p>
                    </div>
                    <div className="p-4 rounded-lg bg-zinc-900/50">
                      <p className="text-xs text-zinc-500">Joined</p>
                      <p className="text-white font-medium">{new Date(memberDetails.user.created_at).toLocaleDateString()}</p>
                    </div>
                    <div className="p-4 rounded-lg bg-zinc-900/50 col-span-2">
                      <p className="text-xs text-zinc-500">User ID</p>
                      <div className="flex items-center gap-2 mt-1">
                        <code className="text-white font-mono text-sm bg-zinc-800 px-2 py-1 rounded flex-1 truncate">
                          {memberDetails.user.id}
                        </code>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => copyToClipboard(memberDetails.user.id, 'User ID')}
                          className="text-zinc-400 hover:text-white shrink-0"
                        >
                          Copy
                        </Button>
                      </div>
                    </div>
                  </div>
                  
                  {/* Run Diagnostic Button */}
                  {isMasterAdmin() && (
                    <div className="mt-4 space-y-2">
                      <Button
                        onClick={() => handleRunDiagnostic(memberDetails.user.id)}
                        className="w-full bg-blue-600 hover:bg-blue-700 text-white"
                        data-testid="run-diagnostic-button"
                      >
                        <Activity className="w-4 h-4 mr-2" />
                        Run Account Diagnostic
                      </Button>
                      <Button
                        onClick={() => handleExportDebugData(memberDetails.user.id, memberDetails.user.full_name)}
                        variant="outline"
                        className="w-full border-zinc-700 text-zinc-300 hover:bg-zinc-800"
                        data-testid="export-debug-data-button"
                      >
                        <Download className="w-4 h-4 mr-2" />
                        Export Debug Data
                      </Button>
                      <p className="text-xs text-zinc-500 mt-1 text-center">
                        Diagnostic: view live summary. Export: download full JSON for offline analysis.
                      </p>
                    </div>
                  )}
                  </>
                )}

                {/* License Info in Profile */}
                {memberLicense && (
                  <div className="mt-4 p-4 rounded-lg bg-purple-500/10 border border-purple-500/30">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <Award className="w-5 h-5 text-purple-400" />
                        <span className="text-purple-400 font-medium">
                          {memberLicense.license_type === 'extended' ? 'Extended Licensee' : 'Honorary Licensee'}
                        </span>
                      </div>
                      {isMasterAdmin() && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setViewDialogOpen(false);
                            handleOpenLicenseDialog(selectedMember);
                          }}
                          className="text-purple-400 hover:text-purple-300"
                        >
                          Manage
                        </Button>
                      )}
                    </div>
                    <div className="grid grid-cols-2 gap-3 text-sm">
                      <div>
                        <p className="text-zinc-500">Starting Amount</p>
                        <p className="text-white font-mono">${memberLicense.starting_amount?.toLocaleString()}</p>
                      </div>
                      <div>
                        <p className="text-zinc-500">Current Amount</p>
                        <p className="text-emerald-400 font-mono">${memberLicense.current_amount?.toLocaleString()}</p>
                      </div>
                    </div>
                  </div>
                )}
              </TabsContent>
              
              {/* Stats Tab */}
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
              
              {/* Actions Tab */}
              <TabsContent value="actions" className="mt-4">
                <div className="space-y-4">
                  <h4 className="text-sm font-medium text-zinc-400">Member Actions</h4>
                  
                  {/* Simulate Member View - for regular members */}
                  {selectedMember?.role === 'member' && (
                    <div className="p-4 rounded-lg bg-zinc-900/50">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center">
                            <Play className="w-5 h-5 text-purple-400" />
                          </div>
                          <div>
                            <p className="text-white font-medium">Simulate Member View</p>
                            <p className="text-xs text-zinc-500">See the platform from this member&apos;s perspective</p>
                          </div>
                        </div>
                        <Button
                          onClick={() => {
                            setViewDialogOpen(false);
                            handleSimulateMember(selectedMember);
                          }}
                          className="btn-secondary"
                        >
                          <Play className="w-4 h-4 mr-1" /> Simulate
                        </Button>
                      </div>
                    </div>
                  )}

                  {/* Manage License - Master Admin only, for regular members */}
                  {isMasterAdmin() && selectedMember?.role === 'member' && (
                    <div className="p-4 rounded-lg bg-zinc-900/50">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${memberLicense ? 'bg-purple-500/20' : 'bg-zinc-800'}`}>
                            <Award className={`w-5 h-5 ${memberLicense ? 'text-purple-400' : 'text-zinc-500'}`} />
                          </div>
                          <div>
                            <p className="text-white font-medium">
                              {memberLicense ? `${memberLicense.license_type === 'extended' ? 'Extended' : 'Honorary'} License` : 'No License'}
                            </p>
                            <p className="text-xs text-zinc-500">
                              {memberLicense ? `Since ${memberLicense.start_date}` : 'Assign a license to this member'}
                            </p>
                          </div>
                        </div>
                        <div className="flex gap-2">
                          {memberLicense && (
                            <Button
                              onClick={handleOpenChangeLicense}
                              variant="outline"
                              size="sm"
                              className="border-purple-500/30 text-purple-400 hover:bg-purple-500/10"
                            >
                              <RefreshCw className="w-4 h-4 mr-1" /> Change Type
                            </Button>
                          )}
                          <Button
                            onClick={() => {
                              setViewDialogOpen(false);
                              handleOpenLicenseDialog(selectedMember);
                            }}
                            className={memberLicense ? 'btn-secondary' : 'btn-primary'}
                            size="sm"
                          >
                            <Award className="w-4 h-4 mr-1" /> {memberLicense ? 'Manage' : 'Assign'}
                          </Button>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Upgrade Role - for regular members */}
                  {selectedMember?.role === 'member' && (
                    <div className="p-4 rounded-lg bg-zinc-900/50">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-lg bg-emerald-500/20 flex items-center justify-center">
                            <ShieldCheck className="w-5 h-5 text-emerald-400" />
                          </div>
                          <div>
                            <p className="text-white font-medium">Upgrade Role</p>
                            <p className="text-xs text-zinc-500">Promote to Basic Admin, Super Admin, or Master Admin</p>
                          </div>
                        </div>
                        <Button
                          onClick={() => {
                            setViewDialogOpen(false);
                            setUpgradeDialogOpen(true);
                          }}
                          className="btn-secondary"
                        >
                          <ShieldCheck className="w-4 h-4 mr-1" /> Upgrade
                        </Button>
                      </div>
                    </div>
                  )}

                  {/* Downgrade Role - For admins */}
                  {selectedMember?.role !== 'member' && isSuperAdmin && selectedMember?.id !== user?.id && (
                    <div className="p-4 rounded-lg bg-zinc-900/50">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-lg bg-amber-500/20 flex items-center justify-center">
                            <Users className="w-5 h-5 text-amber-400" />
                          </div>
                          <div>
                            <p className="text-white font-medium">Downgrade Role</p>
                            <p className="text-xs text-zinc-500">Demote to regular member</p>
                          </div>
                        </div>
                        <Button
                          onClick={() => {
                            setViewDialogOpen(false);
                            handleDowngradeRole(selectedMember.id);
                          }}
                          variant="outline"
                          className="border-amber-500/30 text-amber-400 hover:bg-amber-500/10"
                        >
                          <Users className="w-4 h-4 mr-1" /> Downgrade
                        </Button>
                      </div>
                    </div>
                  )}

                  {/* Unblock Trading Signal - Admin only */}
                  {selectedMember?.id !== user?.id && selectedMember?.role === 'member' && (
                    <div className="p-4 rounded-lg bg-zinc-900/50">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-lg flex items-center justify-center bg-orange-500/20">
                            <AlertTriangle className="w-5 h-5 text-orange-400" />
                          </div>
                          <div>
                            <p className="text-white font-medium">Unblock Signal</p>
                            <p className="text-xs text-zinc-500">Manually unblock this member's trading signal for 7 days</p>
                          </div>
                        </div>
                        <Button
                          onClick={async () => {
                            try {
                              const res = await adminAPI.unblockSignal(selectedMember.id, 7);
                              toast.success(res.data.message);
                            } catch (e) {
                              toast.error(e.response?.data?.detail || 'Failed to unblock');
                            }
                          }}
                          variant="outline"
                          className="border-orange-500/30 text-orange-400 hover:bg-orange-500/10"
                          data-testid="unblock-signal-btn"
                        >
                          <Radio className="w-4 h-4 mr-1" /> Unblock
                        </Button>
                      </div>
                    </div>
                  )}

                  {/* Deactivate/Reactivate User - Admin only */}
                  {selectedMember?.id !== user?.id && (
                    <div className="p-4 rounded-lg bg-zinc-900/50">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${memberDetails?.user?.is_deactivated ? 'bg-emerald-500/20' : 'bg-red-500/20'}`}>
                            {memberDetails?.user?.is_deactivated ? (
                              <UserCheck className="w-5 h-5 text-emerald-400" />
                            ) : (
                              <UserX className="w-5 h-5 text-red-400" />
                            )}
                          </div>
                          <div>
                            <p className="text-white font-medium">
                              {memberDetails?.user?.is_deactivated ? 'Reactivate User' : 'Deactivate User'}
                            </p>
                            <p className="text-xs text-zinc-500">
                              {memberDetails?.user?.is_deactivated 
                                ? 'Allow this user to login again' 
                                : 'Prevent this user from logging in'}
                            </p>
                          </div>
                        </div>
                        {memberDetails?.user?.is_deactivated ? (
                          <Button
                            onClick={() => handleReactivateUser(selectedMember.id)}
                            className="bg-emerald-600 hover:bg-emerald-700 text-white"
                            data-testid="reactivate-user-btn"
                          >
                            <UserCheck className="w-4 h-4 mr-1" /> Reactivate
                          </Button>
                        ) : (
                          <Button
                            onClick={() => handleDeactivateUser(selectedMember.id)}
                            variant="outline"
                            className="border-red-500/30 text-red-400 hover:bg-red-500/10"
                            data-testid="deactivate-user-btn"
                          >
                            <UserX className="w-4 h-4 mr-1" /> Deactivate
                          </Button>
                        )}
                      </div>
                    </div>
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
            <DialogTitle className="text-white">Promote {selectedMember?.full_name}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div>
              <Label className="text-zinc-300">New Role</Label>
              <Select value={newRole} onValueChange={setNewRole}>
                <SelectTrigger className="input-dark mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="basic_admin">Basic Admin</SelectItem>
                  {(isSuperAdmin() || isMasterAdmin()) && <SelectItem value="super_admin">Super Admin</SelectItem>}
                  {isMasterAdmin() && <SelectItem value="master_admin">Master Admin</SelectItem>}
                </SelectContent>
              </Select>
            </div>
            {newRole === 'super_admin' && !isMasterAdmin() && (
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
            {isMasterAdmin() && (
              <p className="text-xs text-emerald-400 flex items-center gap-1">
                <Crown className="w-3 h-3" /> As Master Admin, you can promote directly without secret code
              </p>
            )}
            <Button onClick={handleUpgradeRole} className="w-full btn-primary" data-testid="confirm-upgrade">
              Promote to {newRole?.replace('_', ' ')}
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

      {/* License Management Dialog */}
      <Dialog open={licenseDialogOpen} onOpenChange={setLicenseDialogOpen}>
        <DialogContent className="glass-card border-zinc-800 max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Award className="w-5 h-5 text-purple-400" /> 
              {memberLicense ? 'Manage License' : 'Assign License'} - {selectedMember?.full_name}
            </DialogTitle>
          </DialogHeader>
          
          {memberLicense ? (
            // View/Remove existing license
            <div className="space-y-4 mt-4">
              <div className="p-4 rounded-lg bg-purple-500/10 border border-purple-500/30">
                <div className="flex items-center gap-2 mb-3">
                  <FileCheck className="w-5 h-5 text-purple-400" />
                  <span className="text-purple-400 font-medium">
                    {memberLicense.license_type === 'extended' ? 'Extended Licensee' : 'Honorary Licensee'}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <p className="text-zinc-500">Starting Amount</p>
                    <p className="text-white font-mono">${memberLicense.starting_amount?.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-zinc-500">Current Amount</p>
                    <p className="text-emerald-400 font-mono">${memberLicense.current_amount?.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-zinc-500">Start Date</p>
                    <p className="text-white">{memberLicense.start_date}</p>
                  </div>
                  <div>
                    <p className="text-zinc-500">Status</p>
                    <p className="text-emerald-400">Active</p>
                  </div>
                </div>
                {memberLicense.notes && (
                  <div className="mt-3 pt-3 border-t border-purple-500/20">
                    <p className="text-zinc-500 text-xs">Notes</p>
                    <p className="text-zinc-300 text-sm">{memberLicense.notes}</p>
                  </div>
                )}
              </div>

              {memberLicense.license_type === 'extended' && (
                <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20 text-sm">
                  <p className="text-blue-400 font-medium mb-1">Extended License Calculation</p>
                  <p className="text-zinc-400">
                    Daily profit is fixed per quarter: <span className="text-white font-mono">(Balance ÷ 980) × 15</span>
                  </p>
                  <p className="text-zinc-400 mt-1">
                    Recalculated at the start of each new quarter based on ending balance.
                  </p>
                </div>
              )}

              {memberLicense.license_type === 'honorary' && (
                <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-sm">
                  <p className="text-amber-400 font-medium mb-1">Honorary License</p>
                  <p className="text-zinc-400">
                    Standard profit calculations apply. Funds are <strong>excluded</strong> from team analytics totals.
                  </p>
                </div>
              )}

              {memberLicense.license_type === 'honorary_fa' && (
                <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20 text-sm">
                  <p className="text-blue-400 font-medium mb-1">Honorary FA (Family Account)</p>
                  <p className="text-zinc-400">
                    Family Account license. Licensee can add up to 5 family members with independent profit tracking.
                  </p>
                </div>
              )}

              <Button 
                onClick={handleRemoveLicense}
                variant="outline"
                className="w-full border-red-500/30 text-red-400 hover:bg-red-500/10"
                disabled={licenseLoading}
              >
                {licenseLoading ? 'Removing...' : 'Remove License'}
              </Button>
            </div>
          ) : (
            // Create new license
            <div className="space-y-4 mt-4">
              <div>
                <Label className="text-zinc-300">License Type</Label>
                <Select 
                  value={licenseForm.license_type} 
                  onValueChange={(v) => setLicenseForm({ ...licenseForm, license_type: v })}
                >
                  <SelectTrigger className="input-dark mt-1" data-testid="license-type-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="extended">
                      <div className="flex items-center gap-2">
                        <span className="text-purple-400">Extended Licensee</span>
                      </div>
                    </SelectItem>
                    <SelectItem value="honorary">
                      <div className="flex items-center gap-2">
                        <span className="text-amber-400">Honorary Licensee</span>
                      </div>
                    </SelectItem>
                    <SelectItem value="honorary_fa">
                      <div className="flex items-center gap-2">
                        <span className="text-blue-400">Honorary FA (Family Account)</span>
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {licenseForm.license_type === 'extended' && (
                <div className="p-3 rounded-lg bg-purple-500/10 border border-purple-500/20 text-sm">
                  <p className="text-purple-400 font-medium mb-1">Extended License</p>
                  <p className="text-zinc-400">
                    Daily profit is fixed for entire quarters. Formula: <span className="text-white font-mono">(Balance ÷ 980) × 15</span>
                  </p>
                </div>
              )}

              {licenseForm.license_type === 'honorary' && (
                <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-sm">
                  <p className="text-amber-400 font-medium mb-1">Honorary License</p>
                  <p className="text-zinc-400">
                    Standard calculations, but funds excluded from team totals.
                  </p>
                </div>
              )}

              <div>
                <Label className="text-zinc-300">Starting Amount (USDT)</Label>
                <div className="relative mt-1">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500">$</span>
                  <Input
                    type="number"
                    value={licenseForm.starting_amount}
                    onChange={(e) => setLicenseForm({ ...licenseForm, starting_amount: e.target.value })}
                    placeholder="0.00"
                    className="input-dark pl-7"
                    data-testid="license-starting-amount"
                  />
                </div>
                <p className="text-xs text-zinc-500 mt-1">
                  Current account value: ${selectedMember?.account_value?.toFixed(2) || '0.00'}
                </p>
              </div>

              <div>
                <Label className="text-zinc-300">Start Date</Label>
                <Input
                  type="date"
                  value={licenseForm.start_date}
                  onChange={(e) => setLicenseForm({ ...licenseForm, start_date: e.target.value })}
                  className="input-dark mt-1"
                  data-testid="license-start-date"
                />
              </div>

              <div>
                <Label className="text-zinc-300">Notes (optional)</Label>
                <Input
                  value={licenseForm.notes}
                  onChange={(e) => setLicenseForm({ ...licenseForm, notes: e.target.value })}
                  placeholder="Any additional notes..."
                  className="input-dark mt-1"
                  data-testid="license-notes"
                />
              </div>

              <Button 
                onClick={handleCreateLicense}
                className="w-full btn-primary"
                disabled={licenseLoading}
                data-testid="assign-license-button"
              >
                {licenseLoading ? 'Assigning...' : `Assign ${licenseForm.license_type === 'extended' ? 'Extended' : 'Honorary'} License`}
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Simulate Member Dialog */}
      <Dialog open={simulateDialogOpen} onOpenChange={setSimulateDialogOpen}>
        <DialogContent className="glass-card border-zinc-800 max-w-4xl">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Play className="w-5 h-5" /> Simulate Member View - {selectedMember?.full_name}
            </DialogTitle>
          </DialogHeader>
          {simulationData ? (
            <div className="space-y-6 mt-4">
              {/* Account Overview */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="p-4 rounded-lg bg-zinc-900/50">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-emerald-500/20 flex items-center justify-center">
                      <DollarSign className="w-5 h-5 text-emerald-400" />
                    </div>
                    <div>
                      <p className="text-xs text-zinc-500">Account Value</p>
                      <p className="text-xl font-bold text-emerald-400">
                        ${simulationData.account_value?.toFixed(2) || '0.00'}
                      </p>
                    </div>
                  </div>
                </div>
                <div className="p-4 rounded-lg bg-zinc-900/50">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center">
                      <Activity className="w-5 h-5 text-purple-400" />
                    </div>
                    <div>
                      <p className="text-xs text-zinc-500">LOT Size</p>
                      <p className="text-xl font-bold text-purple-400">
                        {simulationData.lot_size?.toFixed(2) || '0.00'}
                      </p>
                    </div>
                  </div>
                </div>
                <div className="p-4 rounded-lg bg-zinc-900/50">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
                      <TrendingUp className="w-5 h-5 text-blue-400" />
                    </div>
                    <div>
                      <p className="text-xs text-zinc-500">Total Profit</p>
                      <p className="text-xl font-bold text-blue-400">
                        ${simulationData.total_profit?.toFixed(2) || '0.00'}
                      </p>
                    </div>
                  </div>
                </div>
                <div className="p-4 rounded-lg bg-zinc-900/50">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-cyan-500/20 flex items-center justify-center">
                      <Activity className="w-5 h-5 text-cyan-400" />
                    </div>
                    <div>
                      <p className="text-xs text-zinc-500">Total Trades</p>
                      <p className="text-xl font-bold text-white">
                        {simulationData.summary?.total_trades || 0}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Recent Activity */}
              <div>
                <h4 className="text-sm font-medium text-zinc-400 mb-3">Recent Trading Activity</h4>
                {simulationData.trades?.length > 0 ? (
                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {simulationData.trades.slice(0, 10).map((trade, index) => (
                      <div key={trade.id || index} className="p-3 rounded-lg bg-zinc-900/50 flex justify-between items-center">
                        <div className="flex items-center gap-3">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            trade.direction === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'
                          }`}>
                            {trade.direction}
                          </span>
                          <span className="text-zinc-400 text-sm">
                            {new Date(trade.created_at).toLocaleString()}
                          </span>
                        </div>
                        <span className={`font-mono ${trade.actual_profit >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                          {trade.actual_profit >= 0 ? '+' : ''}${trade.actual_profit?.toFixed(2) || '0.00'}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-zinc-500 text-center py-8">No recent trading activity</p>
                )}
              </div>

              {/* Action Buttons */}
              <div className="flex gap-3 pt-4 border-t border-zinc-800">
                <Button
                  onClick={() => {
                    simulateMemberView({
                      id: selectedMember.id,
                      full_name: selectedMember.full_name,
                      account_value: simulationData.account_value,
                      lot_size: simulationData.lot_size,
                      total_deposits: simulationData.total_deposits,
                      total_profit: simulationData.total_profit,
                      allowed_dashboards: selectedMember.allowed_dashboards,
                      license_type: selectedMember.license_type || null,
                      // Include trading type and start date for "New Trader" filtering
                      trading_type: simulationData.member?.trading_type || selectedMember.trading_type,
                      trading_start_date: simulationData.member?.trading_start_date || selectedMember.trading_start_date,
                    });
                    setSimulateDialogOpen(false);
                    toast.success(`Now simulating ${selectedMember.full_name}'s view`);
                  }}
                  className="btn-primary flex items-center gap-2"
                >
                  <Play className="w-4 h-4" />
                  Start Simulation
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setSimulateDialogOpen(false)}
                  className="btn-secondary"
                >
                  Close
                </Button>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-32">
              <div className="w-6 h-6 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Change License Type Dialog */}
      <Dialog open={changeLicenseDialogOpen} onOpenChange={setChangeLicenseDialogOpen}>
        <DialogContent className="glass-card border-zinc-800 max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <RefreshCw className="w-5 h-5 text-purple-400" /> Change License Type
            </DialogTitle>
          </DialogHeader>
          
          {memberLicense && (
            <div className="space-y-4 mt-4">
              <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
                <div className="flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 text-amber-400 mt-0.5" />
                  <div className="text-sm">
                    <p className="text-amber-400 font-medium">Important</p>
                    <p className="text-amber-400/80 text-xs mt-1">
                      This will generate a new license and invalidate the current one.
                    </p>
                  </div>
                </div>
              </div>

              <div className="p-4 rounded-lg bg-zinc-900/50 border border-zinc-800">
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <p className="text-zinc-500">Current Type</p>
                    <p className={memberLicense.license_type === 'extended' ? 'text-purple-400' : 'text-amber-400'}>
                      {memberLicense.license_type?.charAt(0).toUpperCase() + memberLicense.license_type?.slice(1)}
                    </p>
                  </div>
                  <div>
                    <p className="text-zinc-500">Current Amount</p>
                    <p className="text-emerald-400 font-mono">${memberLicense.current_amount?.toLocaleString()}</p>
                  </div>
                </div>
              </div>

              <div>
                <Label className="text-zinc-300">New License Type</Label>
                <Select
                  value={changeLicenseForm.new_license_type}
                  onValueChange={(v) => setChangeLicenseForm({ ...changeLicenseForm, new_license_type: v })}
                >
                  <SelectTrigger className="input-dark mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="extended">Extended Licensee</SelectItem>
                    <SelectItem value="honorary">Honorary Licensee</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label className="text-zinc-300">New Starting Amount</Label>
                <div className="relative mt-1">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500">$</span>
                  <Input
                    type="number"
                    value={changeLicenseForm.new_starting_amount}
                    onChange={(e) => setChangeLicenseForm({ ...changeLicenseForm, new_starting_amount: e.target.value })}
                    placeholder="0.00"
                    className="input-dark pl-7"
                    step="0.01"
                    min="0"
                  />
                </div>
              </div>

              <div>
                <Label className="text-zinc-300">Notes (optional)</Label>
                <Textarea
                  value={changeLicenseForm.notes}
                  onChange={(e) => setChangeLicenseForm({ ...changeLicenseForm, notes: e.target.value })}
                  placeholder="Reason for license type change..."
                  className="input-dark mt-1"
                  rows={2}
                />
              </div>

              <Button
                onClick={handleChangeLicenseType}
                disabled={changingLicense}
                className="w-full btn-primary"
              >
                {changingLicense ? (
                  <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Changing...</>
                ) : (
                  <><RefreshCw className="w-4 h-4 mr-2" /> Change License Type</>
                )}
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Diagnostic Dialog */}
      <Dialog open={diagnosticDialogOpen} onOpenChange={setDiagnosticDialogOpen}>
        <DialogContent className="glass-card border-zinc-800 max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Activity className="w-5 h-5 text-blue-400" />
              Account Diagnostic - {diagnosticData?.user?.full_name || 'Loading...'}
            </DialogTitle>
          </DialogHeader>
          
          {diagnosticLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-blue-400" />
              <span className="ml-3 text-zinc-400">Running diagnostic...</span>
            </div>
          ) : diagnosticData && diagnosticData.summary ? (
            <div className="space-y-6 mt-4">
              {/* User Info */}
              <div className="p-4 rounded-lg bg-zinc-900/50 border border-zinc-800">
                <h4 className="text-sm font-medium text-zinc-400 mb-3">User Information</h4>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
                  <div>
                    <p className="text-zinc-500">Email</p>
                    <p className="text-white">{diagnosticData.user.email}</p>
                  </div>
                  <div>
                    <p className="text-zinc-500">Trading Type</p>
                    <p className="text-white capitalize">{diagnosticData.user.trading_type || 'Not set'}</p>
                  </div>
                  <div>
                    <p className="text-zinc-500">Trading Start</p>
                    {editingTradingStart ? (
                      <div className="flex items-center gap-2 mt-1">
                        <Input
                          type="date"
                          value={newTradingStartDate}
                          onChange={(e) => setNewTradingStartDate(e.target.value)}
                          className="input-dark text-sm h-8"
                        />
                        <Button
                          size="sm"
                          onClick={() => {
                            handleUpdateTradingStartDate(diagnosticData.user.id, newTradingStartDate);
                            setEditingTradingStart(false);
                          }}
                          className="h-8 px-2 bg-emerald-600 hover:bg-emerald-700"
                        >
                          Save
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => setEditingTradingStart(false)}
                          className="h-8 px-2"
                        >
                          Cancel
                        </Button>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2">
                        <p className={diagnosticData.user.trading_start_date ? 'text-white' : 'text-amber-400'}>
                          {diagnosticData.user.trading_start_date || 'Not set'}
                        </p>
                        {!diagnosticData.user.trading_start_date && (
                          <span className="text-xs text-amber-400">⚠️</span>
                        )}
                      </div>
                    )}
                  </div>
                  <div>
                    <p className="text-zinc-500">Onboarding</p>
                    <p className={diagnosticData.user.onboarding_completed ? 'text-emerald-400' : 'text-amber-400'}>
                      {diagnosticData.user.onboarding_completed ? 'Completed' : 'Not completed'}
                    </p>
                  </div>
                  <div>
                    <p className="text-zinc-500">Streak Reset Date</p>
                    <p className="text-white">{diagnosticData.user.streak_reset_date || 'Never'}</p>
                  </div>
                </div>
                
                {/* Quick Actions for Trading Start Date */}
                {!diagnosticData.user.trading_start_date && diagnosticData.summary.actual_trades > 0 && (
                  <div className="mt-4 p-3 rounded-lg bg-amber-500/10 border border-amber-500/30">
                    <div className="flex items-center gap-2 mb-2">
                      <AlertTriangle className="w-4 h-4 text-amber-400" />
                      <span className="text-amber-400 font-medium text-sm">Trading Start Date Not Set</span>
                    </div>
                    <p className="text-xs text-zinc-400 mb-3">
                      This user has {diagnosticData.summary.actual_trades} trade(s) but no trading start date. 
                      This can cause incorrect balance calculations in the Daily Projection table.
                    </p>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        onClick={() => handleAutoFixTradingStart(diagnosticData.user.id)}
                        className="bg-emerald-600 hover:bg-emerald-700 text-white"
                      >
                        <RefreshCw className="w-4 h-4 mr-1" />
                        Auto-Fix (Use First Trade Date)
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          setNewTradingStartDate('');
                          setEditingTradingStart(true);
                        }}
                        className="btn-secondary"
                      >
                        <Calendar className="w-4 h-4 mr-1" />
                        Set Manually
                      </Button>
                    </div>
                  </div>
                )}
              </div>

              {/* Summary Stats */}
              <div className="p-4 rounded-lg bg-zinc-900/50 border border-zinc-800">
                <h4 className="text-sm font-medium text-zinc-400 mb-3">Account Summary</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30">
                    <p className="text-2xl font-bold text-emerald-400">${diagnosticData.summary.total_deposits.toLocaleString()}</p>
                    <p className="text-xs text-zinc-400">Total Deposits</p>
                  </div>
                  <div className="text-center p-3 rounded-lg bg-red-500/10 border border-red-500/30">
                    <p className="text-2xl font-bold text-red-400">${diagnosticData.summary.total_withdrawals.toLocaleString()}</p>
                    <p className="text-xs text-zinc-400">Total Withdrawals</p>
                  </div>
                  <div className="text-center p-3 rounded-lg bg-blue-500/10 border border-blue-500/30">
                    <p className="text-2xl font-bold text-blue-400">${diagnosticData.summary.total_profit.toLocaleString()}</p>
                    <p className="text-xs text-zinc-400">Total Profit</p>
                  </div>
                  <div className="text-center p-3 rounded-lg bg-purple-500/10 border border-purple-500/30">
                    <p className="text-2xl font-bold text-purple-400">${diagnosticData.summary.total_commission.toLocaleString()}</p>
                    <p className="text-xs text-zinc-400">Total Commission</p>
                  </div>
                </div>
                <div className="mt-4 p-3 rounded-lg bg-amber-500/10 border border-amber-500/30">
                  <div className="flex justify-between items-center">
                    <span className="text-zinc-400">Calculated Balance:</span>
                    <span className="text-xl font-bold text-amber-400">${diagnosticData.summary.calculated_balance.toLocaleString()}</span>
                  </div>
                  <p className="text-xs text-zinc-500 mt-1">
                    (Deposits - Withdrawals + Profit + Commission)
                  </p>
                </div>
                <div className="mt-3 grid grid-cols-3 gap-3 text-sm">
                  <div className="text-center">
                    <p className="text-white font-bold">{diagnosticData.summary.total_trades}</p>
                    <p className="text-zinc-500">Total Entries</p>
                  </div>
                  <div className="text-center">
                    <p className="text-emerald-400 font-bold">{diagnosticData.summary.actual_trades}</p>
                    <p className="text-zinc-500">Actual Trades</p>
                  </div>
                  <div className="text-center">
                    <p className="text-amber-400 font-bold">{diagnosticData.summary.did_not_trade_entries}</p>
                    <p className="text-zinc-500">Did Not Trade</p>
                  </div>
                </div>
                {diagnosticData.summary.reset_trades_count > 0 && (
                  <div className="mt-3 p-2 rounded bg-red-500/20 border border-red-500/30">
                    <p className="text-red-400 text-sm font-medium">
                      ⚠️ {diagnosticData.summary.reset_trades_count} trade(s) were deleted/reset
                    </p>
                  </div>
                )}
              </div>

              {/* Recent Trades */}
              <div className="p-4 rounded-lg bg-zinc-900/50 border border-zinc-800">
                <h4 className="text-sm font-medium text-zinc-400 mb-3">Recent Trades (Last 20)</h4>
                {diagnosticData.trades.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="text-zinc-500 border-b border-zinc-800">
                          <th className="text-left py-2 px-2">Date</th>
                          <th className="text-right py-2 px-2">Profit</th>
                          <th className="text-right py-2 px-2">Commission</th>
                          <th className="text-center py-2 px-2">Type</th>
                          <th className="text-left py-2 px-2">Notes</th>
                        </tr>
                      </thead>
                      <tbody>
                        {diagnosticData.trades.map((trade, idx) => (
                          <tr key={idx} className="border-b border-zinc-800/50 hover:bg-zinc-800/30">
                            <td className="py-2 px-2 text-white">{trade.date}</td>
                            <td className={`py-2 px-2 text-right font-mono ${trade.profit >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                              ${trade.profit.toFixed(2)}
                            </td>
                            <td className="py-2 px-2 text-right font-mono text-purple-400">
                              ${trade.commission.toFixed(2)}
                            </td>
                            <td className="py-2 px-2 text-center">
                              {trade.did_not_trade ? (
                                <span className="px-2 py-0.5 rounded text-xs bg-amber-500/20 text-amber-400">DNT</span>
                              ) : (
                                <span className="px-2 py-0.5 rounded text-xs bg-emerald-500/20 text-emerald-400">Trade</span>
                              )}
                            </td>
                            <td className="py-2 px-2 text-zinc-400 truncate max-w-[150px]">{trade.notes}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="text-zinc-500 text-center py-4">No trades found</p>
                )}
              </div>

              {/* Deposits */}
              <div className="p-4 rounded-lg bg-zinc-900/50 border border-zinc-800">
                <h4 className="text-sm font-medium text-zinc-400 mb-3">Recent Deposits/Withdrawals (Last 20)</h4>
                {diagnosticData.deposits.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="text-zinc-500 border-b border-zinc-800">
                          <th className="text-left py-2 px-2">Date</th>
                          <th className="text-right py-2 px-2">Amount</th>
                          <th className="text-center py-2 px-2">Type</th>
                          <th className="text-left py-2 px-2">Notes</th>
                        </tr>
                      </thead>
                      <tbody>
                        {diagnosticData.deposits.map((dep, idx) => (
                          <tr key={idx} className="border-b border-zinc-800/50 hover:bg-zinc-800/30">
                            <td className="py-2 px-2 text-white">{dep.date}</td>
                            <td className={`py-2 px-2 text-right font-mono ${dep.amount >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                              {dep.amount >= 0 ? '+' : ''}${dep.amount.toFixed(2)}
                            </td>
                            <td className="py-2 px-2 text-center">
                              <span className={`px-2 py-0.5 rounded text-xs ${
                                dep.type === 'initial' ? 'bg-blue-500/20 text-blue-400' :
                                dep.amount >= 0 ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'
                              }`}>
                                {dep.type || (dep.amount >= 0 ? 'Deposit' : 'Withdrawal')}
                              </span>
                            </td>
                            <td className="py-2 px-2 text-zinc-400 truncate max-w-[200px]">{dep.notes}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="text-zinc-500 text-center py-4">No deposits found</p>
                )}
              </div>

              {/* Reset/Deleted Trades */}
              {diagnosticData.reset_trades.length > 0 && (
                <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/30">
                  <h4 className="text-sm font-medium text-red-400 mb-3 flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4" />
                    Deleted/Reset Trades
                  </h4>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="text-zinc-500 border-b border-red-500/30">
                          <th className="text-left py-2 px-2">Reset At</th>
                          <th className="text-left py-2 px-2">Original Date</th>
                          <th className="text-right py-2 px-2">Original Profit</th>
                          <th className="text-left py-2 px-2">Reset By</th>
                        </tr>
                      </thead>
                      <tbody>
                        {diagnosticData.reset_trades.map((rt, idx) => (
                          <tr key={idx} className="border-b border-red-500/20">
                            <td className="py-2 px-2 text-white">{rt.reset_at}</td>
                            <td className="py-2 px-2 text-white">{rt.original_date}</td>
                            <td className="py-2 px-2 text-right font-mono text-red-400">${rt.original_profit.toFixed(2)}</td>
                            <td className="py-2 px-2 text-zinc-400">{rt.reset_by}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          ) : diagnosticData && !diagnosticData.summary ? (
            <div className="p-6 text-center">
              <AlertTriangle className="w-12 h-12 text-amber-400 mx-auto mb-4" />
              <h4 className="text-lg font-medium text-white mb-2">Invalid Diagnostic Response</h4>
              <p className="text-zinc-400 mb-4">
                The server returned an unexpected response format. Please ensure the backend is updated to version 2026.02.11.v4 or later.
              </p>
              <p className="text-xs text-zinc-500">
                Check /api/health endpoint for current version.
              </p>
            </div>
          ) : null}
          
          <div className="flex justify-end mt-4">
            <Button variant="outline" onClick={() => setDiagnosticDialogOpen(false)} className="btn-secondary">
              Close
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
    </MobileNotice>
  );
};
