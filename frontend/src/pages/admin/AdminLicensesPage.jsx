import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from 'sonner';
import { MobileNotice } from '@/components/MobileNotice';
import { 
  Award, Plus, Copy, Mail, RefreshCw, Trash2, Ban, Eye, Edit2,
  Clock, Users, CheckCircle2, XCircle, Calendar, DollarSign,
  FileText, Send, RotateCcw, Link2, Upload, ArrowUpCircle,
  ArrowDownCircle, MessageSquare, Image, Loader2, AlertCircle, UserCog
} from 'lucide-react';
import { adminAPI, familyAPI } from '@/lib/api';

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
  const [changeLicenseDialogOpen, setChangeLicenseDialogOpen] = useState(false);
  const [selectedInvite, setSelectedInvite] = useState(null);
  const [selectedTransaction, setSelectedTransaction] = useState(null);
  const [selectedLicense, setSelectedLicense] = useState(null);
  const [activeTab, setActiveTab] = useState('invites');
  
  // Family member dialog state (admin adds on behalf of licensee)
  const [addFamilyDialogOpen, setAddFamilyDialogOpen] = useState(false);
  const [familyForm, setFamilyForm] = useState({ name: '', relationship: '', starting_amount: '' });
  const [addingFamilyMember, setAddingFamilyMember] = useState(false);
  
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
    notes: '',
    effective_start_date: '' // YYYY-MM-DD format
  });
  const [creating, setCreating] = useState(false);
  
  // Change license form state
  const [changeLicenseForm, setChangeLicenseForm] = useState({
    new_license_type: 'extended',
    new_starting_amount: '',
    notes: ''
  });
  const [changingLicense, setChangingLicense] = useState(false);
  
  // Edit effective start date state
  const [editEffectiveDateDialogOpen, setEditEffectiveDateDialogOpen] = useState(false);
  const [editEffectiveDateForm, setEditEffectiveDateForm] = useState({
    effective_start_date: ''
  });
  const [savingEffectiveDate, setSavingEffectiveDate] = useState(false);
  
  // Reset balance dialog state
  const [resetBalanceDialogOpen, setResetBalanceDialogOpen] = useState(false);
  const [resetBalanceForm, setResetBalanceForm] = useState({
    new_amount: '',
    notes: '',
    record_as_deposit: true
  });
  const [resettingBalance, setResettingBalance] = useState(false);
  
  // Edit profile dialog state
  const [editProfileDialogOpen, setEditProfileDialogOpen] = useState(false);
  const [editProfileForm, setEditProfileForm] = useState({
    full_name: '',
    timezone: 'Asia/Manila'
  });
  const [savingProfile, setSavingProfile] = useState(false);
  
  // Delete license dialog state
  const [deleteLicenseDialogOpen, setDeleteLicenseDialogOpen] = useState(false);
  const [deletingLicense, setDeletingLicense] = useState(false);
  
  // Feedback form state
  const [feedbackForm, setFeedbackForm] = useState({
    message: '',
    status: '',
    final_amount: '',
    screenshot: null
  });
  const [sendingFeedback, setSendingFeedback] = useState(false);
  
  // Edit/Delete Transaction state
  const [editTxDialogOpen, setEditTxDialogOpen] = useState(false);
  const [selectedTx, setSelectedTx] = useState(null);
  const [editTxForm, setEditTxForm] = useState({
    amount: '',
    notes: ''
  });
  const [savingTx, setSavingTx] = useState(false);
  const [deleteTxDialogOpen, setDeleteTxDialogOpen] = useState(false);
  const [deletingTx, setDeletingTx] = useState(false);
  
  // Diagnostic/Sync Tool state
  const [diagnosticDialogOpen, setDiagnosticDialogOpen] = useState(false);
  const [diagnosticEmail, setDiagnosticEmail] = useState('');
  const [diagnosticResult, setDiagnosticResult] = useState(null);
  const [runningDiagnostic, setRunningDiagnostic] = useState(false);
  const [syncingUser, setSyncingUser] = useState(false);

  // Run diagnostic for a licensee
  const runDiagnostic = async (email) => {
    if (!email) {
      toast.error('Please enter an email address');
      return;
    }
    setRunningDiagnostic(true);
    setDiagnosticResult(null);
    try {
      // Call the public diagnostic endpoint
      const response = await fetch(`/api/diagnostic/licensee/${encodeURIComponent(email)}`);
      const data = await response.json();
      setDiagnosticResult(data);
      
      if (data.errors && data.errors.length > 0) {
        toast.error(`Diagnostic found ${data.errors.length} issue(s)`);
      } else if (data.calculated_value) {
        toast.success(`Diagnostic complete: Account value should be $${data.calculated_value.toLocaleString()}`);
      }
    } catch (error) {
      console.error('Diagnostic failed:', error);
      toast.error('Failed to run diagnostic: ' + error.message);
      setDiagnosticResult({ error: error.message });
    } finally {
      setRunningDiagnostic(false);
    }
  };

  // Force sync/recalculate for a user
  const forceSync = async (userId) => {
    if (!userId) {
      toast.error('No user ID provided');
      return;
    }
    setSyncingUser(true);
    try {
      // Call the sync endpoint (we'll need to create this if it doesn't exist)
      const response = await adminAPI.forceSyncLicensee(userId);
      toast.success('User data synced successfully!');
      setDiagnosticResult(prev => ({
        ...prev,
        sync_result: response.data,
        synced_at: new Date().toISOString()
      }));
      // Reload the licenses list
      loadData();
    } catch (error) {
      console.error('Sync failed:', error);
      toast.error('Failed to sync: ' + (error.response?.data?.detail || error.message));
    } finally {
      setSyncingUser(false);
    }
  };

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
    // Validate starting amount for extended licensees (required)
    if (createForm.license_type === 'extended') {
      if (!createForm.starting_amount || parseFloat(createForm.starting_amount) <= 0) {
        toast.error('Please enter a valid starting amount for Extended Licensee');
        return;
      }
    }
    
    // For honorary, starting amount is optional but validate if provided
    const startingAmount = createForm.license_type === 'extended' 
      ? parseFloat(createForm.starting_amount)
      : createForm.starting_amount ? parseFloat(createForm.starting_amount) : 0;

    setCreating(true);
    try {
      const res = await adminAPI.createLicenseInvite({
        license_type: createForm.license_type,
        starting_amount: startingAmount,
        valid_duration: createForm.valid_duration,
        max_uses: parseInt(createForm.max_uses),
        invitee_name: createForm.invitee_name || null,
        invitee_email: null, // Email is no longer attached to invite
        notes: createForm.notes || null,
        effective_start_date: createForm.effective_start_date || null
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
        notes: '',
        effective_start_date: ''
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

  const handleOpenChangeLicense = (license) => {
    setSelectedLicense(license);
    setChangeLicenseForm({
      new_license_type: license.license_type === 'extended' ? 'honorary' : 'extended',
      new_starting_amount: license.current_amount?.toString() || license.starting_amount?.toString() || '',
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
      await adminAPI.changeLicenseType(selectedLicense.id, {
        new_license_type: changeLicenseForm.new_license_type,
        new_starting_amount: parseFloat(changeLicenseForm.new_starting_amount),
        notes: changeLicenseForm.notes
      });
      toast.success(`License changed to ${changeLicenseForm.new_license_type}`);
      setChangeLicenseDialogOpen(false);
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to change license type');
    } finally {
      setChangingLicense(false);
    }
  };

  const handleOpenResetBalance = (license) => {
    setSelectedLicense(license);
    setResetBalanceForm({
      new_amount: license.current_amount?.toString() || license.starting_amount?.toString() || '',
      notes: '',
      record_as_deposit: true
    });
    setResetBalanceDialogOpen(true);
  };

  const handleResetBalance = async () => {
    if (!resetBalanceForm.new_amount || parseFloat(resetBalanceForm.new_amount) < 0) {
      toast.error('Please enter a valid amount');
      return;
    }

    setResettingBalance(true);
    try {
      await adminAPI.resetLicenseBalance(selectedLicense.id, {
        new_amount: parseFloat(resetBalanceForm.new_amount),
        notes: resetBalanceForm.notes,
        record_as_deposit: resetBalanceForm.record_as_deposit
      });
      toast.success('License balance reset successfully');
      setResetBalanceDialogOpen(false);
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to reset balance');
    } finally {
      setResettingBalance(false);
    }
  };

  const handleOpenEditProfile = (license) => {
    setSelectedLicense(license);
    setEditProfileForm({
      full_name: license.user_name || '',
      timezone: license.user_timezone || 'Asia/Manila'
    });
    setEditProfileDialogOpen(true);
  };

  const handleSaveProfile = async () => {
    if (!editProfileForm.full_name.trim()) {
      toast.error('Please enter a name');
      return;
    }

    setSavingProfile(true);
    try {
      await adminAPI.updateMember(selectedLicense.user_id, {
        full_name: editProfileForm.full_name,
        timezone: editProfileForm.timezone
      });
      toast.success('Profile updated successfully');
      setEditProfileDialogOpen(false);
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update profile');
    } finally {
      setSavingProfile(false);
    }
  };

  const handleOpenDeleteLicense = (license) => {
    setSelectedLicense(license);
    setDeleteLicenseDialogOpen(true);
  };

  const handleDeleteLicense = async () => {
    if (!selectedLicense) return;
    
    setDeletingLicense(true);
    try {
      await adminAPI.deleteLicense(selectedLicense.id);
      toast.success('License deleted successfully');
      setDeleteLicenseDialogOpen(false);
      setSelectedLicense(null);
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete license');
    } finally {
      setDeletingLicense(false);
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

  // Edit transaction handler
  const handleOpenEditTx = (tx) => {
    setSelectedTx(tx);
    setEditTxForm({
      amount: tx.amount?.toString() || '',
      notes: ''
    });
    setEditTxDialogOpen(true);
  };

  const handleSaveEditTx = async () => {
    if (!editTxForm.amount || parseFloat(editTxForm.amount) <= 0) {
      toast.error('Please enter a valid amount');
      return;
    }

    setSavingTx(true);
    try {
      await adminAPI.updateLicenseeTransaction(selectedTx.id, {
        amount: parseFloat(editTxForm.amount),
        notes: editTxForm.notes || `Amount corrected by admin from $${selectedTx.amount} to $${editTxForm.amount}`
      });
      toast.success('Transaction updated successfully');
      setEditTxDialogOpen(false);
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update transaction');
    } finally {
      setSavingTx(false);
    }
  };

  // Delete transaction handler
  const handleOpenDeleteTx = (tx) => {
    setSelectedTx(tx);
    setDeleteTxDialogOpen(true);
  };

  const handleDeleteTx = async () => {
    setDeletingTx(true);
    try {
      await adminAPI.deleteLicenseeTransaction(selectedTx.id);
      toast.success('Transaction deleted successfully');
      setDeleteTxDialogOpen(false);
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete transaction');
    } finally {
      setDeletingTx(false);
    }
  };

  // Edit effective start date handler
  const handleOpenEditEffectiveDate = (license) => {
    setSelectedLicense(license);
    setEditEffectiveDateForm({
      effective_start_date: license.effective_start_date || license.start_date || ''
    });
    setEditEffectiveDateDialogOpen(true);
  };

  // Add family member on behalf of licensee handler
  const handleOpenAddFamily = (license) => {
    setSelectedLicense(license);
    setFamilyForm({ name: '', relationship: '', starting_amount: '' });
    setAddFamilyDialogOpen(true);
  };

  const handleAddFamilyMember = async () => {
    if (!familyForm.name || !familyForm.starting_amount) {
      toast.error('Name and starting amount are required');
      return;
    }
    setAddingFamilyMember(true);
    try {
      await familyAPI.adminAddMember(selectedLicense.user_id, {
        name: familyForm.name,
        relationship: familyForm.relationship || 'Family',
        starting_amount: parseFloat(familyForm.starting_amount),
      });
      toast.success(`Family member "${familyForm.name}" added for ${selectedLicense.user_name}`);
      setAddFamilyDialogOpen(false);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to add family member');
    } finally {
      setAddingFamilyMember(false);
    }
  };

  const handleSaveEffectiveDate = async () => {
    if (!editEffectiveDateForm.effective_start_date) {
      toast.error('Please select a date');
      return;
    }

    setSavingEffectiveDate(true);
    try {
      await adminAPI.updateLicenseEffectiveStartDate(
        selectedLicense.id, 
        editEffectiveDateForm.effective_start_date
      );
      toast.success('Effective start date updated successfully');
      setEditEffectiveDateDialogOpen(false);
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update effective start date');
    } finally {
      setSavingEffectiveDate(false);
    }
  };

  const getStatusBadge = (status) => {
    const badges = {
      active: <span className="px-2 py-1 rounded text-xs bg-emerald-500/20 text-emerald-400">Active</span>,
      pending: <span className="px-2 py-1 rounded text-xs bg-amber-500/20 text-amber-400">Pending</span>,
      processing: <span className="px-2 py-1 rounded text-xs bg-orange-500/10 text-orange-400">Processing</span>,
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
      return <span className="px-2 py-1 rounded text-xs bg-orange-500/10 text-orange-400">Used</span>;
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
        <div className="w-8 h-8 border-4 border-orange-500/20 border-t-orange-500 rounded-full animate-spin" />
      </div>
    );
  }

  const pendingTransactions = licenseeTransactions.filter(tx => tx.status === 'pending' || tx.status === 'processing');

  return (
    <MobileNotice featureName="License Management" showOnMobile={true}>
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
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
              <FileText className="w-8 h-8 text-orange-400" />
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
                  {licenses.filter(l => (l.license_type === 'honorary' || l.license_type === 'honorary_fa') && l.is_active).length}
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
        <TabsList className="bg-[#0d0d0d]/50 border border-white/[0.06]">
          <TabsTrigger value="invites" className="data-[state=active]:bg-orange-500">
            License Invites ({invites.length})
          </TabsTrigger>
          <TabsTrigger value="active" className="data-[state=active]:bg-orange-500">
            Active Licenses ({licenses.filter(l => l.is_active).length})
          </TabsTrigger>
          <TabsTrigger value="transactions" className="data-[state=active]:bg-orange-500">
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
                            <code className="text-xs bg-[#1a1a1a] px-2 py-1 rounded">{invite.code}</code>
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
                                className="text-zinc-400 hover:text-orange-400"
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
                        <th>Effective Start</th>
                        <th>Actions</th>
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
                          <td className="text-orange-400">
                            <div className="flex items-center gap-1">
                              <span>{license.effective_start_date || license.start_date?.split('T')[0]}</span>
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => handleOpenEditEffectiveDate(license)}
                                className="w-6 h-6 text-zinc-400 hover:text-orange-400"
                                title="Edit Effective Start Date"
                              >
                                <Edit2 className="w-3 h-3" />
                              </Button>
                            </div>
                          </td>
                          <td>
                            <div className="flex gap-1">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleOpenEditProfile(license)}
                                className="text-zinc-400 hover:text-orange-400"
                                title="Edit Profile"
                                data-testid={`edit-profile-${license.id}`}
                              >
                                <UserCog className="w-4 h-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleOpenChangeLicense(license)}
                                className="text-zinc-400 hover:text-purple-400"
                                title="Change License Type"
                              >
                                <RefreshCw className="w-4 h-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleOpenResetBalance(license)}
                                className="text-zinc-400 hover:text-emerald-400"
                                title="Reset Balance"
                              >
                                <RotateCcw className="w-4 h-4" />
                              </Button>
                              {license.license_type === 'honorary_fa' && (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleOpenAddFamily(license)}
                                  className="text-zinc-400 hover:text-orange-400"
                                  title="Add Family Member"
                                  data-testid={`add-family-${license.id}`}
                                >
                                  <Users className="w-4 h-4" />
                                </Button>
                              )}
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleOpenDeleteLicense(license)}
                                className="text-zinc-400 hover:text-red-400"
                                title="Delete License"
                                data-testid={`delete-license-${license.id}`}
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
                                onClick={() => handleOpenEditTx(tx)}
                                className="text-zinc-400 hover:text-orange-400"
                                title="Edit Transaction"
                              >
                                <Edit2 className="w-4 h-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => handleOpenDeleteTx(tx)}
                                className="text-zinc-400 hover:text-red-400"
                                title="Delete Transaction"
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => handleOpenFeedbackDialog(tx)}
                                className="text-zinc-400 hover:text-orange-400"
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
        <DialogContent className="glass-card border-white/[0.06] max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Plus className="w-5 h-5 text-orange-400" /> Generate License Invite
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
                  <SelectItem value="honorary_fa">
                    <span className="text-orange-400">Honorary FA (Family Account)</span>
                  </SelectItem>
                </SelectContent>
              </Select>
              {createForm.license_type === 'honorary' && (
                <p className="text-xs text-zinc-500 mt-1">
                  Honorary licensees use standard profit calculations (deposits + profits - withdrawals)
                </p>
              )}
              {createForm.license_type === 'honorary_fa' && (
                <p className="text-xs text-zinc-500 mt-1">
                  Family Account: Licensee can add up to 5 family members, each with their own profit tracking
                </p>
              )}
            </div>

            {/* Starting Amount - Required for Extended, Optional for Honorary */}
            <div>
              <Label className="text-zinc-300">
                Starting Amount (USDT)
                {createForm.license_type === 'honorary' && (
                  <span className="text-zinc-500 font-normal ml-1">(optional)</span>
                )}
              </Label>
              <div className="relative mt-1">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500">$</span>
                <Input
                  type="number"
                  value={createForm.starting_amount}
                  onChange={(e) => setCreateForm({ ...createForm, starting_amount: e.target.value })}
                  placeholder={createForm.license_type === 'extended' ? '10000' : '0 (optional)'}
                  className="input-dark pl-7"
                />
              </div>
              {createForm.license_type === 'honorary' && (
                <p className="text-xs text-zinc-500 mt-1">
                  Set an initial balance for this honorary licensee. Leave empty or 0 for no starting balance.
                </p>
              )}
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
              <Label className="text-zinc-300">
                Effective Start Trade Date
                <span className="text-zinc-500 font-normal ml-1">(optional)</span>
              </Label>
              <Input
                type="date"
                value={createForm.effective_start_date}
                onChange={(e) => setCreateForm({ ...createForm, effective_start_date: e.target.value })}
                className="input-dark mt-1"
              />
              <p className="text-xs text-zinc-500 mt-1">
                When the licensee&apos;s trading projections start. Defaults to registration date if empty.
              </p>
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
        <DialogContent className="glass-card border-white/[0.06] max-w-md">
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
              <div className="p-4 rounded-lg bg-[#0d0d0d]/50 border border-white/[0.06]">
                <p className="text-xs text-zinc-500 mb-2">Invite Details</p>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <p className="text-zinc-500">Code</p>
                    <code className="text-orange-400">{selectedInvite.code}</code>
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
        <DialogContent className="glass-card border-white/[0.06] max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Eye className="w-5 h-5" /> Invite Details
            </DialogTitle>
          </DialogHeader>
          
          {selectedInvite && (
            <div className="space-y-4 mt-4">
              <div className="p-4 rounded-lg bg-[#0d0d0d]/50 border border-white/[0.06]">
                <div className="flex items-center justify-between mb-3">
                  <code className="text-base font-mono text-orange-400">{selectedInvite.code}</code>
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
                  <div className="mt-3 pt-3 border-t border-white/[0.08]">
                    <p className="text-zinc-500 text-xs">Invitee</p>
                    <p className="text-white text-sm">{selectedInvite.invitee_name}</p>
                  </div>
                )}
              </div>

              {/* Registration Link - Compact */}
              <div className="p-3 rounded-lg bg-orange-500/10 border border-orange-500/15">
                <p className="text-xs text-zinc-400 mb-2">Registration Link</p>
                <div className="flex items-center gap-2">
                  <code className="text-xs text-orange-400 bg-[#0d0d0d]/50 px-2 py-1 rounded truncate max-w-[200px]">
                    .../register/license/{selectedInvite.code?.slice(0, 8)}...
                  </code>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleCopyLink(selectedInvite)}
                    className="text-orange-400 hover:text-orange-300 shrink-0"
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
        <DialogContent className="glass-card border-white/[0.06] max-w-2xl max-h-[80vh] overflow-y-auto">
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
              <div className="p-4 rounded-lg bg-[#0d0d0d]/50 border border-white/[0.06]">
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
                  <div className="mt-4 pt-4 border-t border-white/[0.06]">
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
                      className="rounded-lg border border-white/[0.06] max-h-60 object-contain"
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
                      <div key={fb.id || idx} className={`p-3 rounded-lg ${fb.from_admin ? 'bg-orange-500/10 border border-orange-500/15' : 'bg-[#0d0d0d]/50 border border-white/[0.06]'}`}>
                        <div className="flex items-center justify-between mb-2">
                          <span className={`text-xs ${fb.from_admin ? 'text-orange-400' : 'text-zinc-400'}`}>
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
                            <img src={fb.screenshot_url} alt="Feedback screenshot" className="rounded-lg border border-white/[0.06] max-h-40 object-contain" />
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-2 pt-4 border-t border-white/[0.06]">
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
        <DialogContent className="glass-card border-white/[0.06] max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <MessageSquare className="w-5 h-5 text-orange-400" /> Send Feedback
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
                  <div className="flex items-center gap-2 px-4 py-2 rounded-lg border border-dashed border-white/[0.08] cursor-pointer hover:border-zinc-500 transition-colors">
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

      {/* Change License Type Dialog */}
      <Dialog open={changeLicenseDialogOpen} onOpenChange={setChangeLicenseDialogOpen}>
        <DialogContent className="glass-card border-white/[0.06] max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <RefreshCw className="w-5 h-5 text-purple-400" /> Change License Type
            </DialogTitle>
          </DialogHeader>
          
          {selectedLicense && (
            <div className="space-y-4 mt-4">
              <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
                <div className="flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 text-amber-400 mt-0.5" />
                  <div className="text-sm">
                    <p className="text-amber-400 font-medium">Important</p>
                    <p className="text-amber-400/80 text-xs mt-1">
                      This will generate a new license and invalidate the current one. The change will be applied immediately.
                    </p>
                  </div>
                </div>
              </div>

              <div className="p-4 rounded-lg bg-[#0d0d0d]/50 border border-white/[0.06]">
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <p className="text-zinc-500">Current User</p>
                    <p className="text-white">{selectedLicense.user_name}</p>
                  </div>
                  <div>
                    <p className="text-zinc-500">Current Type</p>
                    <p className={selectedLicense.license_type === 'extended' ? 'text-purple-400' : 'text-amber-400'}>
                      {selectedLicense.license_type?.charAt(0).toUpperCase() + selectedLicense.license_type?.slice(1)}
                    </p>
                  </div>
                  <div>
                    <p className="text-zinc-500">Current Amount</p>
                    <p className="text-emerald-400 font-mono">${selectedLicense.current_amount?.toLocaleString()}</p>
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
                    <SelectItem value="honorary_fa">Honorary FA (Family Account)</SelectItem>
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
                <p className="text-xs text-zinc-500 mt-1">
                  Suggested: ${selectedLicense.current_amount?.toLocaleString()} (current amount)
                </p>
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

      {/* Reset Balance Dialog */}
      <Dialog open={resetBalanceDialogOpen} onOpenChange={setResetBalanceDialogOpen}>
        <DialogContent className="bg-[#0d0d0d] border-white/[0.08] max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <RotateCcw className="w-5 h-5 text-emerald-400" />
              Reset Starting Balance
            </DialogTitle>
          </DialogHeader>
          {selectedLicense && (
            <div className="space-y-4 py-4">
              <div className="p-3 rounded-lg bg-white/[0.04] border border-white/[0.08]">
                <p className="text-zinc-500 text-xs">Current Balance</p>
                <p className="text-emerald-400 font-mono text-lg">
                  ${selectedLicense.current_amount?.toLocaleString() || selectedLicense.starting_amount?.toLocaleString()}
                </p>
              </div>

              <div>
                <Label className="text-zinc-300">New Balance (USDT)</Label>
                <div className="relative mt-1">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500">$</span>
                  <Input
                    type="number"
                    value={resetBalanceForm.new_amount}
                    onChange={(e) => setResetBalanceForm({ ...resetBalanceForm, new_amount: e.target.value })}
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
                  value={resetBalanceForm.notes}
                  onChange={(e) => setResetBalanceForm({ ...resetBalanceForm, notes: e.target.value })}
                  placeholder="Reason for balance reset..."
                  className="input-dark mt-1"
                  rows={2}
                />
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="record_as_deposit"
                  checked={resetBalanceForm.record_as_deposit}
                  onChange={(e) => setResetBalanceForm({ ...resetBalanceForm, record_as_deposit: e.target.checked })}
                  className="rounded border-white/[0.08] bg-[#1a1a1a]"
                />
                <Label htmlFor="record_as_deposit" className="text-zinc-400 text-sm cursor-pointer">
                  Record adjustment as deposit/withdrawal transaction
                </Label>
              </div>

              <Button
                onClick={handleResetBalance}
                disabled={resettingBalance}
                className="w-full bg-emerald-600 hover:bg-emerald-700 text-white"
              >
                {resettingBalance ? (
                  <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Resetting...</>
                ) : (
                  <><RotateCcw className="w-4 h-4 mr-2" /> Reset Balance</>
                )}
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Edit Profile Dialog */}
      <Dialog open={editProfileDialogOpen} onOpenChange={setEditProfileDialogOpen}>
        <DialogContent className="glass-card border-white/[0.06]">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <UserCog className="w-5 h-5 text-orange-400" /> Edit Licensee Profile
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            {selectedLicense && (
              <div className="p-3 rounded-lg bg-[#0d0d0d]/50 text-sm mb-4">
                <p className="text-zinc-400">Email: <span className="text-white">{selectedLicense.user_email}</span></p>
                <p className="text-zinc-400 mt-1">License: <span className={selectedLicense.license_type === 'extended' ? 'text-purple-400' : selectedLicense.license_type === 'honorary_fa' ? 'text-orange-400' : 'text-amber-400'}>{selectedLicense.license_type === 'honorary_fa' ? 'Honorary FA' : selectedLicense.license_type}</span></p>
              </div>
            )}
            
            <div>
              <Label className="text-zinc-300">Full Name</Label>
              <Input
                value={editProfileForm.full_name}
                onChange={(e) => setEditProfileForm({ ...editProfileForm, full_name: e.target.value })}
                className="input-dark mt-1"
                placeholder="Enter full name"
                data-testid="edit-licensee-name"
              />
            </div>

            <div>
              <Label className="text-zinc-300">Timezone</Label>
              <Select 
                value={editProfileForm.timezone} 
                onValueChange={(v) => setEditProfileForm({ ...editProfileForm, timezone: v })}
              >
                <SelectTrigger className="input-dark mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Asia/Manila">Philippines (GMT+8)</SelectItem>
                  <SelectItem value="Asia/Singapore">Singapore (GMT+8)</SelectItem>
                  <SelectItem value="Asia/Taipei">Taiwan (GMT+8)</SelectItem>
                  <SelectItem value="Asia/Hong_Kong">Hong Kong (GMT+8)</SelectItem>
                  <SelectItem value="Asia/Tokyo">Japan (GMT+9)</SelectItem>
                  <SelectItem value="UTC">UTC</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex gap-3 pt-4">
              <Button
                variant="outline"
                onClick={() => setEditProfileDialogOpen(false)}
                className="flex-1 btn-secondary"
              >
                Cancel
              </Button>
              <Button
                onClick={handleSaveProfile}
                disabled={savingProfile || !editProfileForm.full_name.trim()}
                className="flex-1 btn-primary"
                data-testid="save-licensee-profile"
              >
                {savingProfile ? (
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                ) : (
                  <CheckCircle2 className="w-4 h-4 mr-2" />
                )}
                Save Changes
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Delete License Confirmation Dialog */}
      <Dialog open={deleteLicenseDialogOpen} onOpenChange={setDeleteLicenseDialogOpen}>
        <DialogContent className="glass-card border-white/[0.06]">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Trash2 className="w-5 h-5 text-red-400" /> Delete License
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            {selectedLicense && (
              <>
                <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/30">
                  <p className="text-red-400 font-medium mb-2">⚠️ Warning: This action cannot be undone</p>
                  <p className="text-zinc-400 text-sm">
                    Deleting this license will:
                  </p>
                  <ul className="text-zinc-400 text-sm list-disc list-inside mt-2">
                    <li>Remove the license from the system</li>
                    <li>Prevent the licensee from accessing the platform</li>
                    <li>Preserve the user account (they can be re-licensed later)</li>
                  </ul>
                </div>
                
                <div className="p-3 rounded-lg bg-[#0d0d0d]/50 text-sm">
                  <div className="flex justify-between mb-1">
                    <span className="text-zinc-400">Licensee:</span>
                    <span className="text-white">{selectedLicense.user_name}</span>
                  </div>
                  <div className="flex justify-between mb-1">
                    <span className="text-zinc-400">Email:</span>
                    <span className="text-white">{selectedLicense.user_email}</span>
                  </div>
                  <div className="flex justify-between mb-1">
                    <span className="text-zinc-400">License Type:</span>
                    <span className={selectedLicense.license_type === 'extended' ? 'text-purple-400' : 'text-amber-400'}>
                      {selectedLicense.license_type}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-400">Current Balance:</span>
                    <span className="text-emerald-400">${selectedLicense.current_amount?.toLocaleString()}</span>
                  </div>
                </div>
              </>
            )}

            <div className="flex gap-3 pt-2">
              <Button
                variant="outline"
                onClick={() => setDeleteLicenseDialogOpen(false)}
                className="flex-1 btn-secondary"
              >
                Cancel
              </Button>
              <Button
                onClick={handleDeleteLicense}
                disabled={deletingLicense}
                className="flex-1 bg-red-600 hover:bg-red-700 text-white"
                data-testid="confirm-delete-license"
              >
                {deletingLicense ? (
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                ) : (
                  <Trash2 className="w-4 h-4 mr-2" />
                )}
                Delete License
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Edit Transaction Dialog */}
      <Dialog open={editTxDialogOpen} onOpenChange={setEditTxDialogOpen}>
        <DialogContent className="glass-card border-white/[0.06] max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Edit2 className="w-5 h-5 text-orange-400" /> Edit Transaction
            </DialogTitle>
          </DialogHeader>
          {selectedTx && (
            <div className="space-y-4 py-4">
              <div className="p-3 rounded-lg bg-[#0d0d0d]/50">
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <span className="text-zinc-500">Type:</span>
                    <span className={`ml-2 ${selectedTx.type === 'deposit' ? 'text-emerald-400' : 'text-red-400'}`}>
                      {selectedTx.type}
                    </span>
                  </div>
                  <div>
                    <span className="text-zinc-500">User:</span>
                    <span className="ml-2 text-white">{selectedTx.user_name}</span>
                  </div>
                  <div>
                    <span className="text-zinc-500">Original Amount:</span>
                    <span className="ml-2 text-zinc-400 font-mono">${selectedTx.amount?.toLocaleString()}</span>
                  </div>
                  <div>
                    <span className="text-zinc-500">Status:</span>
                    <span className="ml-2">{getStatusBadge(selectedTx.status)}</span>
                  </div>
                </div>
              </div>

              <div>
                <Label className="text-zinc-300">Corrected Amount (USDT)</Label>
                <div className="relative mt-1">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500">$</span>
                  <Input
                    type="number"
                    value={editTxForm.amount}
                    onChange={(e) => setEditTxForm({ ...editTxForm, amount: e.target.value })}
                    placeholder="0.00"
                    className="input-dark pl-7"
                    step="0.01"
                  />
                </div>
              </div>

              <div>
                <Label className="text-zinc-300">Reason for Correction (optional)</Label>
                <Textarea
                  value={editTxForm.notes}
                  onChange={(e) => setEditTxForm({ ...editTxForm, notes: e.target.value })}
                  placeholder="Reason for amount correction..."
                  className="input-dark mt-1"
                  rows={2}
                />
              </div>

              <DialogFooter className="flex gap-3 pt-2">
                <Button
                  variant="outline"
                  onClick={() => setEditTxDialogOpen(false)}
                  className="flex-1 btn-secondary"
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleSaveEditTx}
                  disabled={savingTx}
                  className="flex-1 btn-primary"
                >
                  {savingTx ? (
                    <><Loader2 className="w-4 h-4 animate-spin mr-2" /> Saving...</>
                  ) : (
                    <><CheckCircle2 className="w-4 h-4 mr-2" /> Save Changes</>
                  )}
                </Button>
              </DialogFooter>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Delete Transaction Dialog */}
      <Dialog open={deleteTxDialogOpen} onOpenChange={setDeleteTxDialogOpen}>
        <DialogContent className="glass-card border-white/[0.06] max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Trash2 className="w-5 h-5 text-red-400" /> Delete Transaction
            </DialogTitle>
          </DialogHeader>
          {selectedTx && (
            <div className="space-y-4 py-4">
              <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/30">
                <p className="text-red-400 font-medium mb-2">⚠️ Warning: This action cannot be undone</p>
                <p className="text-zinc-400 text-sm">
                  Deleting this transaction will permanently remove it from the system and affect the licensee&apos;s balance calculations.
                </p>
              </div>
              
              <div className="p-3 rounded-lg bg-[#0d0d0d]/50 text-sm">
                <div className="flex justify-between mb-1">
                  <span className="text-zinc-400">Type:</span>
                  <span className={selectedTx.type === 'deposit' ? 'text-emerald-400' : 'text-red-400'}>
                    {selectedTx.type}
                  </span>
                </div>
                <div className="flex justify-between mb-1">
                  <span className="text-zinc-400">User:</span>
                  <span className="text-white">{selectedTx.user_name}</span>
                </div>
                <div className="flex justify-between mb-1">
                  <span className="text-zinc-400">Amount:</span>
                  <span className="text-emerald-400 font-mono">${selectedTx.amount?.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-400">Date:</span>
                  <span className="text-white">{new Date(selectedTx.created_at).toLocaleDateString()}</span>
                </div>
              </div>

              <DialogFooter className="flex gap-3 pt-2">
                <Button
                  variant="outline"
                  onClick={() => setDeleteTxDialogOpen(false)}
                  className="flex-1 btn-secondary"
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleDeleteTx}
                  disabled={deletingTx}
                  className="flex-1 bg-red-600 hover:bg-red-700 text-white"
                >
                  {deletingTx ? (
                    <><Loader2 className="w-4 h-4 animate-spin mr-2" /> Deleting...</>
                  ) : (
                    <><Trash2 className="w-4 h-4 mr-2" /> Delete Transaction</>
                  )}
                </Button>
              </DialogFooter>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Edit Effective Start Date Dialog */}
      <Dialog open={editEffectiveDateDialogOpen} onOpenChange={setEditEffectiveDateDialogOpen}>
        <DialogContent className="glass-card border-white/[0.06] max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Calendar className="w-5 h-5 text-orange-400" /> Edit Effective Start Date
            </DialogTitle>
          </DialogHeader>
          {selectedLicense && (
            <div className="space-y-4 py-4">
              <div className="p-3 rounded-lg bg-[#0d0d0d]/50">
                <div className="text-sm">
                  <span className="text-zinc-500">Licensee:</span>
                  <span className="ml-2 text-white">{selectedLicense.user_name}</span>
                </div>
              </div>

              <div>
                <Label className="text-zinc-300">Effective Start Trade Date</Label>
                <Input
                  type="date"
                  value={editEffectiveDateForm.effective_start_date}
                  onChange={(e) => setEditEffectiveDateForm({ ...editEffectiveDateForm, effective_start_date: e.target.value })}
                  className="input-dark mt-1"
                />
                <p className="text-xs text-zinc-500 mt-1">
                  The Daily Projection table will start from this date for the licensee.
                </p>
              </div>

              <DialogFooter className="flex gap-3 pt-2">
                <Button
                  variant="outline"
                  onClick={() => setEditEffectiveDateDialogOpen(false)}
                  className="flex-1 btn-secondary"
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleSaveEffectiveDate}
                  disabled={savingEffectiveDate}
                  className="flex-1 btn-primary"
                >
                  {savingEffectiveDate ? (
                    <><Loader2 className="w-4 h-4 animate-spin mr-2" /> Saving...</>
                  ) : (
                    <><CheckCircle2 className="w-4 h-4 mr-2" /> Save Changes</>
                  )}
                </Button>
              </DialogFooter>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Add Family Member Dialog (Admin on behalf of licensee) */}
      <Dialog open={addFamilyDialogOpen} onOpenChange={setAddFamilyDialogOpen}>
        <DialogContent className="bg-[#0d0d0d] border-white/[0.06] max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Users className="w-5 h-5 text-orange-400" /> Add Family Member
            </DialogTitle>
          </DialogHeader>
          {selectedLicense && (
            <div className="space-y-4">
              <p className="text-sm text-zinc-400">
                Adding family member for <span className="text-white font-medium">{selectedLicense.user_name}</span>
              </p>
              <div>
                <Label className="text-zinc-300">Member Name *</Label>
                <Input
                  value={familyForm.name}
                  onChange={(e) => setFamilyForm({ ...familyForm, name: e.target.value })}
                  placeholder="Full name"
                  className="bg-[#1a1a1a] border-white/[0.08] text-white mt-1"
                  data-testid="admin-family-name-input"
                />
              </div>
              <div>
                <Label className="text-zinc-300">Relationship</Label>
                <Input
                  value={familyForm.relationship}
                  onChange={(e) => setFamilyForm({ ...familyForm, relationship: e.target.value })}
                  placeholder="e.g., Spouse, Child, Parent"
                  className="bg-[#1a1a1a] border-white/[0.08] text-white mt-1"
                  data-testid="admin-family-relationship-input"
                />
              </div>
              <div>
                <Label className="text-zinc-300">Starting Amount (USDT) *</Label>
                <div className="relative mt-1">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500">$</span>
                  <Input
                    type="number"
                    value={familyForm.starting_amount}
                    onChange={(e) => setFamilyForm({ ...familyForm, starting_amount: e.target.value })}
                    placeholder="1000"
                    className="bg-[#1a1a1a] border-white/[0.08] text-white pl-8"
                    data-testid="admin-family-amount-input"
                  />
                </div>
              </div>
              <DialogFooter className="flex gap-3 pt-2">
                <Button variant="outline" onClick={() => setAddFamilyDialogOpen(false)} className="flex-1 btn-secondary">
                  Cancel
                </Button>
                <Button
                  onClick={handleAddFamilyMember}
                  disabled={addingFamilyMember || !familyForm.name || !familyForm.starting_amount}
                  className="flex-1 btn-primary"
                  data-testid="admin-add-family-submit"
                >
                  {addingFamilyMember ? (
                    <><Loader2 className="w-4 h-4 animate-spin mr-2" /> Adding...</>
                  ) : (
                    <><Plus className="w-4 h-4 mr-2" /> Add Member</>
                  )}
                </Button>
              </DialogFooter>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Diagnostic Tool Dialog */}
      <Dialog open={diagnosticDialogOpen} onOpenChange={setDiagnosticDialogOpen}>
        <DialogContent className="glass-card border-white/[0.08] max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <UserCog className="w-5 h-5 text-cyan-400" /> Licensee Diagnostic Tool
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            <p className="text-sm text-zinc-400">
              Enter a licensee's email to diagnose calculation issues. This tool shows exactly what the backend sees and can force a recalculation if needed.
            </p>
            
            <div className="flex gap-2">
              <Input
                placeholder="Enter licensee email (e.g., user@example.com)"
                value={diagnosticEmail}
                onChange={(e) => setDiagnosticEmail(e.target.value)}
                className="flex-1 bg-white/[0.04] border-white/[0.08]"
              />
              <Button 
                onClick={() => runDiagnostic(diagnosticEmail)}
                disabled={runningDiagnostic || !diagnosticEmail}
                className="gap-2"
              >
                {runningDiagnostic ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
                Run Diagnostic
              </Button>
            </div>
            
            {/* Quick select from existing licenses */}
            {licenses.length > 0 && (
              <div>
                <Label className="text-zinc-400 text-xs mb-2 block">Quick Select:</Label>
                <div className="flex flex-wrap gap-2">
                  {licenses.slice(0, 5).map(lic => (
                    <Button
                      key={lic.id}
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setDiagnosticEmail(lic.user_email || '');
                        runDiagnostic(lic.user_email);
                      }}
                      className="text-xs border-white/[0.08] hover:bg-[#1a1a1a]"
                    >
                      {lic.user_name || lic.user_email || 'Unknown'}
                    </Button>
                  ))}
                </div>
              </div>
            )}
            
            {/* Diagnostic Results */}
            {diagnosticResult && (
              <div className="mt-4 space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="font-medium text-white">Diagnostic Results</h4>
                  {diagnosticResult.user_id && (
                    <Button
                      onClick={() => forceSync(diagnosticResult.user_id)}
                      disabled={syncingUser}
                      size="sm"
                      className="gap-2 bg-emerald-600 hover:bg-emerald-700"
                    >
                      {syncingUser ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
                      Force Sync
                    </Button>
                  )}
                </div>
                
                {/* Steps */}
                {diagnosticResult.steps && diagnosticResult.steps.length > 0 && (
                  <div className="bg-[#0d0d0d]/50 rounded-lg p-3 space-y-1">
                    {diagnosticResult.steps.map((step, i) => (
                      <p key={i} className={`text-sm font-mono ${step.startsWith('✓') ? 'text-emerald-400' : 'text-red-400'}`}>
                        {step}
                      </p>
                    ))}
                  </div>
                )}
                
                {/* Errors */}
                {diagnosticResult.errors && diagnosticResult.errors.length > 0 && (
                  <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3">
                    <p className="text-red-400 font-medium flex items-center gap-2">
                      <AlertCircle className="w-4 h-4" /> Issues Found:
                    </p>
                    <ul className="mt-2 space-y-1">
                      {diagnosticResult.errors.map((err, i) => (
                        <li key={i} className="text-sm text-red-300">• {err}</li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {/* Summary */}
                {diagnosticResult.calculated_value && (
                  <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-xs text-zinc-400">Starting Amount</p>
                        <p className="text-lg font-bold text-white">${diagnosticResult.license?.starting_amount?.toLocaleString() || '0'}</p>
                      </div>
                      <div>
                        <p className="text-xs text-zinc-400">Calculated Value</p>
                        <p className="text-lg font-bold text-emerald-400">${diagnosticResult.calculated_value?.toLocaleString()}</p>
                      </div>
                      <div>
                        <p className="text-xs text-zinc-400">Profit</p>
                        <p className="text-lg font-bold text-cyan-400">+${diagnosticResult.calculated_profit?.toLocaleString()}</p>
                      </div>
                      <div>
                        <p className="text-xs text-zinc-400">Trades After Start</p>
                        <p className="text-lg font-bold text-white">{diagnosticResult.trades_after_start || 0}</p>
                      </div>
                    </div>
                  </div>
                )}
                
                {/* Sync Result */}
                {diagnosticResult.sync_result && (
                  <div className="bg-orange-500/10 border border-orange-500/20 rounded-lg p-3">
                    <p className="text-orange-400 font-medium flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4" /> Sync Complete
                    </p>
                    <p className="text-sm text-zinc-300 mt-1">{diagnosticResult.sync_result.message}</p>
                  </div>
                )}
                
                {/* Raw JSON (collapsible) */}
                <details className="text-xs">
                  <summary className="text-zinc-500 cursor-pointer hover:text-zinc-300">Show Raw Response</summary>
                  <pre className="mt-2 bg-[#0d0d0d] p-2 rounded overflow-x-auto text-zinc-400">
                    {JSON.stringify(diagnosticResult, null, 2)}
                  </pre>
                </details>
              </div>
            )}
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setDiagnosticDialogOpen(false)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
    </MobileNotice>
  );
};
