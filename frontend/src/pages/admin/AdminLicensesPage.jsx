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
import { 
  Award, Plus, Copy, Mail, RefreshCw, Trash2, Ban, Eye, 
  Clock, Users, CheckCircle2, XCircle, Calendar, DollarSign,
  FileText, Send, RotateCcw, Link2, Upload, ArrowUpCircle,
  ArrowDownCircle, MessageSquare, Image, Loader2
} from 'lucide-react';
import { adminAPI } from '@/lib/api';

export const AdminLicensesPage = () => {
  const { isMasterAdmin } = useAuth();
  const [invites, setInvites] = useState([]);
  const [licenses, setLicenses] = useState([]);
  const [licenseeTransactions, setLicenseeTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [emailDialogOpen, setEmailDialogOpen] = useState(false);
  const [transactionDialogOpen, setTransactionDialogOpen] = useState(false);
  const [feedbackDialogOpen, setFeedbackDialogOpen] = useState(false);
  const [selectedInvite, setSelectedInvite] = useState(null);
  const [selectedTransaction, setSelectedTransaction] = useState(null);
  const [activeTab, setActiveTab] = useState('invites');
  
  // Email dialog state
  const [emailTo, setEmailTo] = useState('');
  const [sendingEmail, setSendingEmail] = useState(false);
  
  // Create form state
  const [createForm, setCreateForm] = useState({
    license_type: 'extended',
    starting_amount: '',
    valid_duration: '3_months',
    max_uses: '1',
    invitee_name: '',
    notes: ''
  });
  const [creating, setCreating] = useState(false);
  
  // Feedback form state
  const [feedbackForm, setFeedbackForm] = useState({
    message: '',
    status: '',
    final_amount: '',
    screenshot: null
  });
  const [sendingFeedback, setSendingFeedback] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [invitesRes, licensesRes, txRes] = await Promise.all([
        adminAPI.getLicenseInvites(),
        adminAPI.getLicenses(),
        adminAPI.getLicenseeTransactions()
      ]);
      setInvites(invitesRes.data.invites || []);
      setLicenses(licensesRes.data.licenses || []);
      setLicenseeTransactions(txRes.data.transactions || []);
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
        invitee_email: null, // Email is no longer attached to invite
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

  const handleOpenEmailDialog = (invite) => {
    setSelectedInvite(invite);
    setEmailTo(invite.invitee_email || '');
    setEmailDialogOpen(true);
  };

  const handleSendEmail = async () => {
    if (!emailTo || !emailTo.includes('@')) {
      toast.error('Please enter a valid email address');
      return;
    }

    setSendingEmail(true);
    try {
      // First update the invite with the email
      await adminAPI.updateLicenseInvite(selectedInvite.id, { invitee_email: emailTo });
      // Then send the email
      const res = await adminAPI.resendLicenseInvite(selectedInvite.id);
      toast.success(res.data.message || 'Email sent successfully!');
      setEmailDialogOpen(false);
      setEmailTo('');
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to send email');
    } finally {
      setSendingEmail(false);
    }
  };

  const handleRevoke = async (invite) => {
    if (!window.confirm(`Revoke invite ${invite.code}?`)) return;

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

  const handleViewTransaction = (tx) => {
    setSelectedTransaction(tx);
    setTransactionDialogOpen(true);
  };

  const handleOpenFeedbackDialog = (tx) => {
    setSelectedTransaction(tx);
    setFeedbackForm({
      message: '',
      status: tx.status === 'pending' ? 'processing' : tx.status === 'processing' ? 'awaiting_confirmation' : '',
      final_amount: '',
      screenshot: null
    });
    setFeedbackDialogOpen(true);
  };

  const handleSendFeedback = async () => {
    if (!feedbackForm.message.trim()) {
      toast.error('Please enter a message');
      return;
    }

    setSendingFeedback(true);
    try {
      const formData = new FormData();
      formData.append('message', feedbackForm.message);
      if (feedbackForm.status) formData.append('status', feedbackForm.status);
      if (feedbackForm.final_amount) formData.append('final_amount', feedbackForm.final_amount);
      if (feedbackForm.screenshot) formData.append('screenshot', feedbackForm.screenshot);

      await adminAPI.addTransactionFeedback(selectedTransaction.id, formData);
      toast.success('Feedback sent successfully');
      setFeedbackDialogOpen(false);
      loadData();
    } catch (error) {
      toast.error('Failed to send feedback');
    } finally {
      setSendingFeedback(false);
    }
  };

  const handleApproveTransaction = async (tx) => {
    try {
      await adminAPI.approveTransaction(tx.id);
      toast.success('Transaction approved');
      loadData();
    } catch (error) {
      toast.error('Failed to approve transaction');
    }
  };

  const handleCompleteTransaction = async (tx) => {
    try {
      const formData = new FormData();
      await adminAPI.completeTransaction(tx.id, formData);
      toast.success('Transaction completed');
      loadData();
    } catch (error) {
      toast.error('Failed to complete transaction');
    }
  };

  const getStatusBadge = (status) => {
    const badges = {
      active: <span className="px-2 py-1 rounded text-xs bg-emerald-500/20 text-emerald-400">Active</span>,
      pending: <span className="px-2 py-1 rounded text-xs bg-amber-500/20 text-amber-400">Pending</span>,
      processing: <span className="px-2 py-1 rounded text-xs bg-blue-500/20 text-blue-400">Processing</span>,
      awaiting_confirmation: <span className="px-2 py-1 rounded text-xs bg-purple-500/20 text-purple-400">Awaiting Confirmation</span>,
      completed: <span className="px-2 py-1 rounded text-xs bg-emerald-500/20 text-emerald-400">Completed</span>,
      rejected: <span className="px-2 py-1 rounded text-xs bg-red-500/20 text-red-400">Rejected</span>,
    };
    return badges[status] || <span className="px-2 py-1 rounded text-xs bg-zinc-500/20 text-zinc-400">{status}</span>;
  };

  const getInviteStatusBadge = (invite) => {
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

  const pendingTransactions = licenseeTransactions.filter(tx => tx.status === 'pending' || tx.status === 'processing');

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

      {/* Pending Transactions Alert */}
      {pendingTransactions.length > 0 && (
        <Card className="glass-card border-amber-500/30">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-amber-500/20 flex items-center justify-center">
                <Clock className="w-5 h-5 text-amber-400" />
              </div>
              <div className="flex-1">
                <p className="text-amber-400 font-medium">
                  {pendingTransactions.length} Pending Transaction{pendingTransactions.length > 1 ? 's' : ''}
                </p>
                <p className="text-sm text-zinc-400">Licensee deposit/withdrawal requests need your attention</p>
              </div>
              <Button 
                variant="outline" 
                onClick={() => setActiveTab('transactions')}
                className="border-amber-500/30 text-amber-400 hover:bg-amber-500/10"
              >
                View Requests
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
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
                <p className="text-sm text-zinc-400">Extended</p>
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
                <p className="text-sm text-zinc-400">Honorary</p>
                <p className="text-2xl font-bold text-amber-400">
                  {licenses.filter(l => l.license_type === 'honorary' && l.is_active).length}
                </p>
              </div>
              <Award className="w-8 h-8 text-amber-400" />
            </div>
          </CardContent>
        </Card>
        <Card className="glass-card">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-400">Pending Requests</p>
                <p className="text-2xl font-bold text-cyan-400">{pendingTransactions.length}</p>
              </div>
              <Clock className="w-8 h-8 text-cyan-400" />
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
          <TabsTrigger value="transactions" className="data-[state=active]:bg-blue-500">
            Transactions ({licenseeTransactions.length})
            {pendingTransactions.length > 0 && (
              <span className="ml-2 px-1.5 py-0.5 rounded-full text-xs bg-amber-500 text-white">
                {pendingTransactions.length}
              </span>
            )}
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
                          <td className="text-white text-sm">{invite.invitee_name || '-'}</td>
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
                          <td>{getInviteStatusBadge(invite)}</td>
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
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => handleOpenEmailDialog(invite)}
                                className="text-zinc-400 hover:text-emerald-400"
                                title="Send Email"
                              >
                                <Mail className="w-4 h-4" />
                              </Button>
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

        {/* Licensee Transactions Tab */}
        <TabsContent value="transactions" className="mt-4">
          <Card className="glass-card">
            <CardHeader>
              <CardTitle className="text-white">Licensee Transactions</CardTitle>
            </CardHeader>
            <CardContent>
              {licenseeTransactions.length === 0 ? (
                <div className="text-center py-12">
                  <DollarSign className="w-12 h-12 text-zinc-600 mx-auto mb-4" />
                  <p className="text-zinc-500">No licensee transactions yet</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full data-table">
                    <thead>
                      <tr>
                        <th>Type</th>
                        <th>User</th>
                        <th>Amount</th>
                        <th>Status</th>
                        <th>Date</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {licenseeTransactions.map((tx) => (
                        <tr key={tx.id}>
                          <td>
                            <div className="flex items-center gap-2">
                              {tx.type === 'deposit' ? (
                                <ArrowDownCircle className="w-4 h-4 text-emerald-400" />
                              ) : (
                                <ArrowUpCircle className="w-4 h-4 text-red-400" />
                              )}
                              <span className="capitalize text-white">{tx.type}</span>
                            </div>
                          </td>
                          <td>
                            <div>
                              <p className="text-white">{tx.user_name}</p>
                              <p className="text-zinc-500 text-xs">{tx.user_email}</p>
                            </div>
                          </td>
                          <td className={`font-mono ${tx.type === 'deposit' ? 'text-emerald-400' : 'text-red-400'}`}>
                            {tx.type === 'deposit' ? '+' : '-'}${tx.amount?.toLocaleString()}
                          </td>
                          <td>{getStatusBadge(tx.status)}</td>
                          <td className="text-zinc-400 text-sm">
                            {new Date(tx.created_at).toLocaleDateString()}
                          </td>
                          <td>
                            <div className="flex gap-1">
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => handleViewTransaction(tx)}
                                className="text-zinc-400 hover:text-white"
                                title="View Details"
                              >
                                <Eye className="w-4 h-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => handleOpenFeedbackDialog(tx)}
                                className="text-zinc-400 hover:text-blue-400"
                                title="Send Feedback"
                              >
                                <MessageSquare className="w-4 h-4" />
                              </Button>
                              {tx.status === 'pending' && (
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  onClick={() => handleApproveTransaction(tx)}
                                  className="text-zinc-400 hover:text-emerald-400"
                                  title="Approve"
                                >
                                  <CheckCircle2 className="w-4 h-4" />
                                </Button>
                              )}
                              {tx.status === 'processing' && (
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  onClick={() => handleCompleteTransaction(tx)}
                                  className="text-zinc-400 hover:text-emerald-400"
                                  title="Complete"
                                >
                                  <CheckCircle2 className="w-4 h-4" />
                                </Button>
                              )}
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
                <SelectTrigger className="input-dark mt-1">
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
            </div>

            <div>
              <Label className="text-zinc-300">Invitee Name (optional)</Label>
              <Input
                value={createForm.invitee_name}
                onChange={(e) => setCreateForm({ ...createForm, invitee_name: e.target.value })}
                placeholder="For your reference"
                className="input-dark mt-1"
              />
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
            >
              {creating ? (
                <><RefreshCw className="w-4 h-4 mr-2 animate-spin" /> Generating...</>
              ) : (
                <><Link2 className="w-4 h-4 mr-2" /> Generate Invite Link</>
              )}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Email Dialog */}
      <Dialog open={emailDialogOpen} onOpenChange={setEmailDialogOpen}>
        <DialogContent className="glass-card border-zinc-800 max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Mail className="w-5 h-5 text-emerald-400" /> Send License Invite Email
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 mt-4">
            <div>
              <Label className="text-zinc-300">Recipient Email</Label>
              <Input
                type="email"
                value={emailTo}
                onChange={(e) => setEmailTo(e.target.value)}
                placeholder="invitee@example.com"
                className="input-dark mt-1"
              />
            </div>

            {selectedInvite && (
              <div className="p-4 rounded-lg bg-zinc-900/50 border border-zinc-800">
                <p className="text-xs text-zinc-500 mb-2">Invite Details</p>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <p className="text-zinc-500">Code</p>
                    <code className="text-blue-400">{selectedInvite.code}</code>
                  </div>
                  <div>
                    <p className="text-zinc-500">Type</p>
                    <p className={selectedInvite.license_type === 'extended' ? 'text-purple-400' : 'text-amber-400'}>
                      {selectedInvite.license_type}
                    </p>
                  </div>
                  <div>
                    <p className="text-zinc-500">Amount</p>
                    <p className="text-emerald-400">${selectedInvite.starting_amount?.toLocaleString()}</p>
                  </div>
                </div>
              </div>
            )}

            <Button 
              onClick={handleSendEmail}
              className="w-full btn-primary"
              disabled={sendingEmail}
            >
              {sendingEmail ? (
                <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Sending...</>
              ) : (
                <><Send className="w-4 h-4 mr-2" /> Send Email</>
              )}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* View Invite Dialog */}
      <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
        <DialogContent className="glass-card border-zinc-800 max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Eye className="w-5 h-5" /> Invite Details
            </DialogTitle>
          </DialogHeader>
          
          {selectedInvite && (
            <div className="space-y-4 mt-4">
              <div className="p-4 rounded-lg bg-zinc-900/50 border border-zinc-800">
                <div className="flex items-center justify-between mb-3">
                  <code className="text-base font-mono text-blue-400">{selectedInvite.code}</code>
                  {getInviteStatusBadge(selectedInvite)}
                </div>
                
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <p className="text-zinc-500 text-xs">License Type</p>
                    <p className={`text-sm ${selectedInvite.license_type === 'extended' ? 'text-purple-400' : 'text-amber-400'}`}>
                      {selectedInvite.license_type?.charAt(0).toUpperCase() + selectedInvite.license_type?.slice(1)}
                    </p>
                  </div>
                  <div>
                    <p className="text-zinc-500 text-xs">Starting Amount</p>
                    <p className="text-emerald-400 font-mono text-sm">${selectedInvite.starting_amount?.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-zinc-500 text-xs">Valid Duration</p>
                    <p className="text-white text-sm">{getDurationLabel(selectedInvite.valid_duration)}</p>
                  </div>
                  <div>
                    <p className="text-zinc-500 text-xs">Uses</p>
                    <p className="text-white text-sm">{selectedInvite.uses_count || 0} / {selectedInvite.max_uses}</p>
                  </div>
                </div>
                
                {selectedInvite.invitee_name && (
                  <div className="mt-3 pt-3 border-t border-zinc-700">
                    <p className="text-zinc-500 text-xs">Invitee</p>
                    <p className="text-white text-sm">{selectedInvite.invitee_name}</p>
                  </div>
                )}
              </div>

              {/* Registration Link - Compact */}
              <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20">
                <p className="text-xs text-zinc-400 mb-2">Registration Link</p>
                <div className="flex items-center gap-2">
                  <code className="text-xs text-blue-400 bg-zinc-900/50 px-2 py-1 rounded truncate max-w-[200px]">
                    .../register/license/{selectedInvite.code?.slice(0, 8)}...
                  </code>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleCopyLink(selectedInvite)}
                    className="text-blue-400 hover:text-blue-300 shrink-0"
                  >
                    <Copy className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={() => handleCopyLink(selectedInvite)}
                  className="flex-1 btn-secondary text-sm"
                >
                  <Copy className="w-4 h-4 mr-1" /> Copy Link
                </Button>
                <Button
                  onClick={() => {
                    setViewDialogOpen(false);
                    handleOpenEmailDialog(selectedInvite);
                  }}
                  className="flex-1 btn-primary text-sm"
                >
                  <Send className="w-4 h-4 mr-1" /> Email
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* View Transaction Dialog */}
      <Dialog open={transactionDialogOpen} onOpenChange={setTransactionDialogOpen}>
        <DialogContent className="glass-card border-zinc-800 max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              {selectedTransaction?.type === 'deposit' ? (
                <ArrowDownCircle className="w-5 h-5 text-emerald-400" />
              ) : (
                <ArrowUpCircle className="w-5 h-5 text-red-400" />
              )}
              {selectedTransaction?.type?.charAt(0).toUpperCase() + selectedTransaction?.type?.slice(1)} Request
            </DialogTitle>
          </DialogHeader>
          
          {selectedTransaction && (
            <div className="space-y-4 mt-4">
              <div className="p-4 rounded-lg bg-zinc-900/50 border border-zinc-800">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-zinc-500">User</p>
                    <p className="text-white">{selectedTransaction.user_name}</p>
                    <p className="text-zinc-500 text-xs">{selectedTransaction.user_email}</p>
                  </div>
                  <div>
                    <p className="text-zinc-500">Amount</p>
                    <p className={`text-xl font-mono ${selectedTransaction.type === 'deposit' ? 'text-emerald-400' : 'text-red-400'}`}>
                      ${selectedTransaction.amount?.toLocaleString()}
                    </p>
                  </div>
                  <div>
                    <p className="text-zinc-500">Status</p>
                    {getStatusBadge(selectedTransaction.status)}
                  </div>
                  <div>
                    <p className="text-zinc-500">Date</p>
                    <p className="text-white">{new Date(selectedTransaction.created_at).toLocaleString()}</p>
                  </div>
                  {selectedTransaction.deposit_date && (
                    <div>
                      <p className="text-zinc-500">Deposit Date</p>
                      <p className="text-white">{selectedTransaction.deposit_date}</p>
                    </div>
                  )}
                  {selectedTransaction.processing_days && (
                    <div>
                      <p className="text-zinc-500">Processing Time</p>
                      <p className="text-white">{selectedTransaction.processing_days} business days</p>
                    </div>
                  )}
                </div>
                
                {selectedTransaction.notes && (
                  <div className="mt-4 pt-4 border-t border-zinc-800">
                    <p className="text-zinc-500 text-sm">Notes</p>
                    <p className="text-zinc-300">{selectedTransaction.notes}</p>
                  </div>
                )}
              </div>

              {/* Screenshot */}
              {selectedTransaction.screenshot_url && (
                <div>
                  <p className="text-sm text-zinc-400 mb-2">Submitted Screenshot</p>
                  <a href={selectedTransaction.screenshot_url} target="_blank" rel="noopener noreferrer">
                    <img 
                      src={selectedTransaction.screenshot_url} 
                      alt="Transaction screenshot" 
                      className="rounded-lg border border-zinc-800 max-h-60 object-contain"
                    />
                  </a>
                </div>
              )}

              {/* Feedback History */}
              {selectedTransaction.feedback?.length > 0 && (
                <div>
                  <p className="text-sm text-zinc-400 mb-2">Communication History</p>
                  <div className="space-y-3">
                    {selectedTransaction.feedback.map((fb, idx) => (
                      <div key={fb.id || idx} className={`p-3 rounded-lg ${fb.from_admin ? 'bg-blue-500/10 border border-blue-500/20' : 'bg-zinc-900/50 border border-zinc-800'}`}>
                        <div className="flex items-center justify-between mb-2">
                          <span className={`text-xs ${fb.from_admin ? 'text-blue-400' : 'text-zinc-400'}`}>
                            {fb.from_admin ? fb.created_by_name || 'Admin' : 'Licensee'}
                          </span>
                          <span className="text-xs text-zinc-500">
                            {new Date(fb.created_at).toLocaleString()}
                          </span>
                        </div>
                        <p className="text-zinc-300 text-sm">{fb.message}</p>
                        {fb.final_amount && (
                          <p className="text-emerald-400 font-mono mt-2">Final Amount: ${fb.final_amount.toLocaleString()}</p>
                        )}
                        {fb.screenshot_url && (
                          <a href={fb.screenshot_url} target="_blank" rel="noopener noreferrer" className="block mt-2">
                            <img src={fb.screenshot_url} alt="Feedback screenshot" className="rounded-lg border border-zinc-800 max-h-40 object-contain" />
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-2 pt-4 border-t border-zinc-800">
                <Button
                  onClick={() => {
                    setTransactionDialogOpen(false);
                    handleOpenFeedbackDialog(selectedTransaction);
                  }}
                  className="flex-1 btn-secondary"
                >
                  <MessageSquare className="w-4 h-4 mr-2" /> Send Feedback
                </Button>
                {selectedTransaction.status === 'pending' && (
                  <Button
                    onClick={() => {
                      handleApproveTransaction(selectedTransaction);
                      setTransactionDialogOpen(false);
                    }}
                    className="flex-1 btn-primary"
                  >
                    <CheckCircle2 className="w-4 h-4 mr-2" /> Approve
                  </Button>
                )}
                {selectedTransaction.status === 'processing' && (
                  <Button
                    onClick={() => {
                      handleCompleteTransaction(selectedTransaction);
                      setTransactionDialogOpen(false);
                    }}
                    className="flex-1 bg-emerald-600 hover:bg-emerald-700"
                  >
                    <CheckCircle2 className="w-4 h-4 mr-2" /> Complete
                  </Button>
                )}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Feedback Dialog */}
      <Dialog open={feedbackDialogOpen} onOpenChange={setFeedbackDialogOpen}>
        <DialogContent className="glass-card border-zinc-800 max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <MessageSquare className="w-5 h-5 text-blue-400" /> Send Feedback
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 mt-4">
            <div>
              <Label className="text-zinc-300">Message</Label>
              <Textarea
                value={feedbackForm.message}
                onChange={(e) => setFeedbackForm({ ...feedbackForm, message: e.target.value })}
                placeholder="Enter your feedback message..."
                className="input-dark mt-1 min-h-[100px]"
              />
            </div>

            <div>
              <Label className="text-zinc-300">Update Status (optional)</Label>
              <Select 
                value={feedbackForm.status} 
                onValueChange={(v) => setFeedbackForm({ ...feedbackForm, status: v })}
              >
                <SelectTrigger className="input-dark mt-1">
                  <SelectValue placeholder="Keep current status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="processing">Processing</SelectItem>
                  <SelectItem value="awaiting_confirmation">Awaiting Confirmation</SelectItem>
                  <SelectItem value="completed">Completed</SelectItem>
                  <SelectItem value="rejected">Rejected</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {selectedTransaction?.type === 'withdrawal' && (
              <div>
                <Label className="text-zinc-300">Final Amount After Fees (optional)</Label>
                <div className="relative mt-1">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500">$</span>
                  <Input
                    type="number"
                    value={feedbackForm.final_amount}
                    onChange={(e) => setFeedbackForm({ ...feedbackForm, final_amount: e.target.value })}
                    placeholder="Amount after fees"
                    className="input-dark pl-7"
                  />
                </div>
              </div>
            )}

            <div>
              <Label className="text-zinc-300">Attach Screenshot (optional)</Label>
              <div className="mt-1">
                <input
                  type="file"
                  accept="image/*"
                  onChange={(e) => setFeedbackForm({ ...feedbackForm, screenshot: e.target.files?.[0] || null })}
                  className="hidden"
                  id="feedback-screenshot"
                />
                <label htmlFor="feedback-screenshot">
                  <div className="flex items-center gap-2 px-4 py-2 rounded-lg border border-dashed border-zinc-700 cursor-pointer hover:border-zinc-500 transition-colors">
                    <Upload className="w-4 h-4 text-zinc-500" />
                    <span className="text-sm text-zinc-400">
                      {feedbackForm.screenshot ? feedbackForm.screenshot.name : 'Click to upload'}
                    </span>
                  </div>
                </label>
              </div>
            </div>

            <Button 
              onClick={handleSendFeedback}
              className="w-full btn-primary"
              disabled={sendingFeedback}
            >
              {sendingFeedback ? (
                <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Sending...</>
              ) : (
                <><Send className="w-4 h-4 mr-2" /> Send Feedback</>
              )}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};
