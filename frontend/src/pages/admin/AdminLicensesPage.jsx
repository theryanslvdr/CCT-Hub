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
  Award, Plus, Copy, Mail, RefreshCw, Trash2, Ban, Eye, 
  Clock, Users, CheckCircle2, XCircle, Calendar, DollarSign,
  FileText, Send, RotateCcw, Link2
} from 'lucide-react';
import { adminAPI } from '@/lib/api';

export const AdminLicensesPage = () => {
  const { isMasterAdmin } = useAuth();
  const [invites, setInvites] = useState([]);
  const [licenses, setLicenses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [selectedInvite, setSelectedInvite] = useState(null);
  const [activeTab, setActiveTab] = useState('invites');
  
  // Create form state
  const [createForm, setCreateForm] = useState({
    license_type: 'extended',
    starting_amount: '',
    valid_duration: '3_months',
    max_uses: '1',
    invitee_name: '',
    invitee_email: '',
    notes: ''
  });
  const [creating, setCreating] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [invitesRes, licensesRes] = await Promise.all([
        adminAPI.getLicenseInvites(),
        adminAPI.getLicenses()
      ]);
      setInvites(invitesRes.data.invites || []);
      setLicenses(licensesRes.data.licenses || []);
    } catch (error) {
      console.error('Failed to load licenses data:', error);
      toast.error('Failed to load licenses data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleCreateInvite = async () => {
    if (!createForm.starting_amount || parseFloat(createForm.starting_amount) <= 0) {
      toast.error('Please enter a valid starting amount');
      return;
    }

    setCreating(true);
    try {
      const res = await adminAPI.createLicenseInvite({
        license_type: createForm.license_type,
        starting_amount: parseFloat(createForm.starting_amount),
        valid_duration: createForm.valid_duration,
        max_uses: parseInt(createForm.max_uses),
        invitee_name: createForm.invitee_name || null,
        invitee_email: createForm.invitee_email || null,
        notes: createForm.notes || null
      });

      toast.success('License invite created!');
      
      // Copy the link to clipboard
      if (res.data.registration_url) {
        navigator.clipboard.writeText(res.data.registration_url);
        toast.success('Registration link copied to clipboard!');
      }

      setCreateDialogOpen(false);
      setCreateForm({
        license_type: 'extended',
        starting_amount: '',
        valid_duration: '3_months',
        max_uses: '1',
        invitee_name: '',
        invitee_email: '',
        notes: ''
      });
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create invite');
    } finally {
      setCreating(false);
    }
  };

  const handleCopyLink = (invite) => {
    const url = `${window.location.origin}/register/license/${invite.code}`;
    navigator.clipboard.writeText(url);
    toast.success('Registration link copied!');
  };

  const handleSendEmail = async (invite) => {
    if (!invite.invitee_email) {
      toast.error('No email address for this invite');
      return;
    }

    try {
      const res = await adminAPI.resendLicenseInvite(invite.id);
      toast.success(res.data.message);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to send email');
    }
  };

  const handleRevoke = async (invite) => {
    if (!window.confirm(`Revoke invite for ${invite.invitee_name || invite.code}?`)) return;

    try {
      await adminAPI.revokeLicenseInvite(invite.id);
      toast.success('Invite revoked');
      loadData();
    } catch (error) {
      toast.error('Failed to revoke invite');
    }
  };

  const handleRenew = async (invite, duration = '3_months') => {
    try {
      await adminAPI.renewLicenseInvite(invite.id, duration);
      toast.success('Invite renewed');
      loadData();
    } catch (error) {
      toast.error('Failed to renew invite');
    }
  };

  const handleDelete = async (invite) => {
    if (!window.confirm(`Delete invite ${invite.code}? This cannot be undone.`)) return;

    try {
      await adminAPI.deleteLicenseInvite(invite.id);
      toast.success('Invite deleted');
      loadData();
    } catch (error) {
      toast.error('Failed to delete invite');
    }
  };

  const handleViewDetails = (invite) => {
    setSelectedInvite(invite);
    setViewDialogOpen(true);
  };

  const getStatusBadge = (invite) => {
    if (invite.is_revoked) {
      return <span className="px-2 py-1 rounded text-xs bg-red-500/20 text-red-400">Revoked</span>;
    }
    if (invite.is_expired) {
      return <span className="px-2 py-1 rounded text-xs bg-amber-500/20 text-amber-400">Expired</span>;
    }
    if (invite.is_fully_used) {
      return <span className="px-2 py-1 rounded text-xs bg-blue-500/20 text-blue-400">Used</span>;
    }
    return <span className="px-2 py-1 rounded text-xs bg-emerald-500/20 text-emerald-400">Active</span>;
  };

  const getDurationLabel = (duration) => {
    const labels = {
      '3_months': '3 Months',
      '6_months': '6 Months',
      '1_year': '1 Year',
      'indefinite': 'Indefinite'
    };
    return labels[duration] || duration;
  };

  if (!isMasterAdmin()) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-zinc-500">Only Master Admin can access this page</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Award className="w-6 h-6 text-purple-400" /> License Management
        </h1>
        <Button onClick={() => setCreateDialogOpen(true)} className="btn-primary gap-2" data-testid="create-invite-btn">
          <Plus className="w-4 h-4" /> Generate License Invite
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="glass-card">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-400">Total Invites</p>
                <p className="text-2xl font-bold text-white">{invites.length}</p>
              </div>
              <FileText className="w-8 h-8 text-blue-400" />
            </div>
          </CardContent>
        </Card>
        <Card className="glass-card">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-400">Active Invites</p>
                <p className="text-2xl font-bold text-emerald-400">
                  {invites.filter(i => !i.is_revoked && !i.is_expired && !i.is_fully_used).length}
                </p>
              </div>
              <CheckCircle2 className="w-8 h-8 text-emerald-400" />
            </div>
          </CardContent>
        </Card>
        <Card className="glass-card">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-400">Extended Licenses</p>
                <p className="text-2xl font-bold text-purple-400">
                  {licenses.filter(l => l.license_type === 'extended' && l.is_active).length}
                </p>
              </div>
              <Award className="w-8 h-8 text-purple-400" />
            </div>
          </CardContent>
        </Card>
        <Card className="glass-card">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-400">Honorary Licenses</p>
                <p className="text-2xl font-bold text-amber-400">
                  {licenses.filter(l => l.license_type === 'honorary' && l.is_active).length}
                </p>
              </div>
              <Award className="w-8 h-8 text-amber-400" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-zinc-900/50 border border-zinc-800">
          <TabsTrigger value="invites" className="data-[state=active]:bg-blue-500">
            License Invites ({invites.length})
          </TabsTrigger>
          <TabsTrigger value="active" className="data-[state=active]:bg-blue-500">
            Active Licenses ({licenses.filter(l => l.is_active).length})
          </TabsTrigger>
        </TabsList>

        {/* Invites Tab */}
        <TabsContent value="invites" className="mt-4">
          <Card className="glass-card">
            <CardHeader>
              <CardTitle className="text-white">License Invites</CardTitle>
            </CardHeader>
            <CardContent>
              {invites.length === 0 ? (
                <div className="text-center py-12">
                  <FileText className="w-12 h-12 text-zinc-600 mx-auto mb-4" />
                  <p className="text-zinc-500">No license invites yet</p>
                  <Button onClick={() => setCreateDialogOpen(true)} className="mt-4 btn-secondary">
                    Create First Invite
                  </Button>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full data-table">
                    <thead>
                      <tr>
                        <th>Code</th>
                        <th>Type</th>
                        <th>Invitee</th>
                        <th>Amount</th>
                        <th>Valid For</th>
                        <th>Uses</th>
                        <th>Status</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {invites.map((invite) => (
                        <tr key={invite.id}>
                          <td>
                            <code className="text-xs bg-zinc-800 px-2 py-1 rounded">{invite.code}</code>
                          </td>
                          <td>
                            <span className={`px-2 py-1 rounded text-xs ${
                              invite.license_type === 'extended' 
                                ? 'bg-purple-500/20 text-purple-400' 
                                : 'bg-amber-500/20 text-amber-400'
                            }`}>
                              {invite.license_type}
                            </span>
                          </td>
                          <td>
                            <div>
                              <p className="text-white text-sm">{invite.invitee_name || '-'}</p>
                              <p className="text-zinc-500 text-xs">{invite.invitee_email || '-'}</p>
                            </div>
                          </td>
                          <td className="font-mono text-emerald-400">
                            ${invite.starting_amount?.toLocaleString()}
                          </td>
                          <td className="text-zinc-400 text-sm">
                            {getDurationLabel(invite.valid_duration)}
                          </td>
                          <td>
                            <span className="text-zinc-400">
                              {invite.uses_count || 0} / {invite.max_uses}
                            </span>
                          </td>
                          <td>{getStatusBadge(invite)}</td>
                          <td>
                            <div className="flex gap-1">
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => handleViewDetails(invite)}
                                className="text-zinc-400 hover:text-white"
                                title="View Details"
                              >
                                <Eye className="w-4 h-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => handleCopyLink(invite)}
                                className="text-zinc-400 hover:text-blue-400"
                                title="Copy Link"
                              >
                                <Copy className="w-4 h-4" />
                              </Button>
                              {invite.invitee_email && (
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  onClick={() => handleSendEmail(invite)}
                                  className="text-zinc-400 hover:text-emerald-400"
                                  title="Send Email"
                                >
                                  <Mail className="w-4 h-4" />
                                </Button>
                              )}
                              {(invite.is_expired || invite.is_revoked) && (
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  onClick={() => handleRenew(invite)}
                                  className="text-zinc-400 hover:text-cyan-400"
                                  title="Renew"
                                >
                                  <RotateCcw className="w-4 h-4" />
                                </Button>
                              )}
                              {!invite.is_revoked && !invite.is_expired && (
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  onClick={() => handleRevoke(invite)}
                                  className="text-zinc-400 hover:text-amber-400"
                                  title="Revoke"
                                >
                                  <Ban className="w-4 h-4" />
                                </Button>
                              )}
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => handleDelete(invite)}
                                className="text-zinc-400 hover:text-red-400"
                                title="Delete"
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
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Active Licenses Tab */}
        <TabsContent value="active" className="mt-4">
          <Card className="glass-card">
            <CardHeader>
              <CardTitle className="text-white">Active Licenses</CardTitle>
            </CardHeader>
            <CardContent>
              {licenses.filter(l => l.is_active).length === 0 ? (
                <div className="text-center py-12">
                  <Award className="w-12 h-12 text-zinc-600 mx-auto mb-4" />
                  <p className="text-zinc-500">No active licenses</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full data-table">
                    <thead>
                      <tr>
                        <th>User</th>
                        <th>Type</th>
                        <th>Starting Amount</th>
                        <th>Current Amount</th>
                        <th>Start Date</th>
                        <th>Created</th>
                      </tr>
                    </thead>
                    <tbody>
                      {licenses.filter(l => l.is_active).map((license) => (
                        <tr key={license.id}>
                          <td>
                            <div>
                              <p className="text-white">{license.user_name}</p>
                              <p className="text-zinc-500 text-xs">{license.user_email}</p>
                            </div>
                          </td>
                          <td>
                            <span className={`px-2 py-1 rounded text-xs ${
                              license.license_type === 'extended' 
                                ? 'bg-purple-500/20 text-purple-400' 
                                : 'bg-amber-500/20 text-amber-400'
                            }`}>
                              {license.license_type}
                            </span>
                          </td>
                          <td className="font-mono text-zinc-400">
                            ${license.starting_amount?.toLocaleString()}
                          </td>
                          <td className="font-mono text-emerald-400">
                            ${license.current_amount?.toLocaleString()}
                          </td>
                          <td className="text-zinc-400">
                            {license.start_date?.split('T')[0]}
                          </td>
                          <td className="text-zinc-500 text-sm">
                            {new Date(license.created_at).toLocaleDateString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Create Invite Dialog */}
      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <DialogContent className="glass-card border-zinc-800 max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Plus className="w-5 h-5 text-blue-400" /> Generate License Invite
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 mt-4">
            <div>
              <Label className="text-zinc-300">License Type</Label>
              <Select 
                value={createForm.license_type} 
                onValueChange={(v) => setCreateForm({ ...createForm, license_type: v })}
              >
                <SelectTrigger className="input-dark mt-1" data-testid="invite-type-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="extended">
                    <span className="text-purple-400">Extended Licensee</span>
                  </SelectItem>
                  <SelectItem value="honorary">
                    <span className="text-amber-400">Honorary Licensee</span>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label className="text-zinc-300">Starting Amount (USDT)</Label>
              <div className="relative mt-1">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500">$</span>
                <Input
                  type="number"
                  value={createForm.starting_amount}
                  onChange={(e) => setCreateForm({ ...createForm, starting_amount: e.target.value })}
                  placeholder="10000"
                  className="input-dark pl-7"
                  data-testid="invite-amount-input"
                />
              </div>
            </div>

            <div>
              <Label className="text-zinc-300">Valid For</Label>
              <Select 
                value={createForm.valid_duration} 
                onValueChange={(v) => setCreateForm({ ...createForm, valid_duration: v })}
              >
                <SelectTrigger className="input-dark mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="3_months">3 Months</SelectItem>
                  <SelectItem value="6_months">6 Months</SelectItem>
                  <SelectItem value="1_year">1 Year</SelectItem>
                  <SelectItem value="indefinite">Indefinite</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label className="text-zinc-300">Maximum Uses</Label>
              <Input
                type="number"
                min="1"
                value={createForm.max_uses}
                onChange={(e) => setCreateForm({ ...createForm, max_uses: e.target.value })}
                className="input-dark mt-1"
              />
              <p className="text-xs text-zinc-500 mt-1">How many users can register with this invite</p>
            </div>

            <div className="border-t border-zinc-800 pt-4">
              <p className="text-sm text-zinc-400 mb-3">Optional: Pre-fill invitee details</p>
              
              <div className="space-y-3">
                <div>
                  <Label className="text-zinc-300">Invitee Name</Label>
                  <Input
                    value={createForm.invitee_name}
                    onChange={(e) => setCreateForm({ ...createForm, invitee_name: e.target.value })}
                    placeholder="John Doe"
                    className="input-dark mt-1"
                  />
                </div>
                
                <div>
                  <Label className="text-zinc-300">Invitee Email</Label>
                  <Input
                    type="email"
                    value={createForm.invitee_email}
                    onChange={(e) => setCreateForm({ ...createForm, invitee_email: e.target.value })}
                    placeholder="john@example.com"
                    className="input-dark mt-1"
                  />
                  <p className="text-xs text-zinc-500 mt-1">If provided, you can send the invite via email</p>
                </div>
              </div>
            </div>

            <div>
              <Label className="text-zinc-300">Notes (optional)</Label>
              <Input
                value={createForm.notes}
                onChange={(e) => setCreateForm({ ...createForm, notes: e.target.value })}
                placeholder="Special arrangement, referral source, etc."
                className="input-dark mt-1"
              />
            </div>

            <Button 
              onClick={handleCreateInvite}
              className="w-full btn-primary"
              disabled={creating}
              data-testid="generate-invite-btn"
            >
              {creating ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> Generating...
                </>
              ) : (
                <>
                  <Link2 className="w-4 h-4 mr-2" /> Generate Invite Link
                </>
              )}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* View Details Dialog */}
      <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
        <DialogContent className="glass-card border-zinc-800 max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Eye className="w-5 h-5" /> Invite Details
            </DialogTitle>
          </DialogHeader>
          
          {selectedInvite && (
            <div className="space-y-4 mt-4">
              <div className="p-4 rounded-lg bg-zinc-900/50 border border-zinc-800">
                <div className="flex items-center justify-between mb-3">
                  <code className="text-lg font-mono text-blue-400">{selectedInvite.code}</code>
                  {getStatusBadge(selectedInvite)}
                </div>
                
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-zinc-500">License Type</p>
                    <p className={`${selectedInvite.license_type === 'extended' ? 'text-purple-400' : 'text-amber-400'}`}>
                      {selectedInvite.license_type?.charAt(0).toUpperCase() + selectedInvite.license_type?.slice(1)} Licensee
                    </p>
                  </div>
                  <div>
                    <p className="text-zinc-500">Starting Amount</p>
                    <p className="text-emerald-400 font-mono">${selectedInvite.starting_amount?.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-zinc-500">Valid Duration</p>
                    <p className="text-white">{getDurationLabel(selectedInvite.valid_duration)}</p>
                  </div>
                  <div>
                    <p className="text-zinc-500">Uses</p>
                    <p className="text-white">{selectedInvite.uses_count || 0} / {selectedInvite.max_uses}</p>
                  </div>
                  {selectedInvite.valid_until && (
                    <div>
                      <p className="text-zinc-500">Expires</p>
                      <p className="text-white">{selectedInvite.valid_until?.split('T')[0]}</p>
                    </div>
                  )}
                  <div>
                    <p className="text-zinc-500">Created</p>
                    <p className="text-white">{new Date(selectedInvite.created_at).toLocaleDateString()}</p>
                  </div>
                </div>

                {selectedInvite.invitee_name && (
                  <div className="mt-4 pt-4 border-t border-zinc-800">
                    <p className="text-zinc-500 text-sm">Invitee</p>
                    <p className="text-white">{selectedInvite.invitee_name}</p>
                    {selectedInvite.invitee_email && (
                      <p className="text-zinc-400 text-sm">{selectedInvite.invitee_email}</p>
                    )}
                  </div>
                )}

                {selectedInvite.notes && (
                  <div className="mt-4 pt-4 border-t border-zinc-800">
                    <p className="text-zinc-500 text-sm">Notes</p>
                    <p className="text-zinc-300">{selectedInvite.notes}</p>
                  </div>
                )}
              </div>

              {/* Registered Users */}
              {selectedInvite.registered_users?.length > 0 && (
                <div>
                  <p className="text-sm text-zinc-400 mb-2">Registered Users ({selectedInvite.registered_users.length})</p>
                  <div className="space-y-2">
                    {selectedInvite.registered_users.map((user) => (
                      <div key={user.id} className="p-3 rounded-lg bg-zinc-900/50 flex items-center justify-between">
                        <div>
                          <p className="text-white text-sm">{user.full_name}</p>
                          <p className="text-zinc-500 text-xs">{user.email}</p>
                        </div>
                        <p className="text-zinc-500 text-xs">
                          {new Date(user.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Registration Link */}
              <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20">
                <p className="text-xs text-zinc-400 mb-1">Registration Link</p>
                <div className="flex items-center gap-2">
                  <code className="text-xs text-blue-400 flex-1 truncate">
                    {window.location.origin}/register/license/{selectedInvite.code}
                  </code>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleCopyLink(selectedInvite)}
                    className="text-blue-400 hover:text-blue-300"
                  >
                    <Copy className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-2 pt-2">
                <Button
                  variant="outline"
                  onClick={() => handleCopyLink(selectedInvite)}
                  className="flex-1 btn-secondary"
                >
                  <Copy className="w-4 h-4 mr-2" /> Copy Link
                </Button>
                {selectedInvite.invitee_email && (
                  <Button
                    onClick={() => handleSendEmail(selectedInvite)}
                    className="flex-1 btn-primary"
                  >
                    <Send className="w-4 h-4 mr-2" /> Send Email
                  </Button>
                )}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};
