import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import api from '@/lib/api';
import { toast } from 'sonner';
import { 
  AlertTriangle, Users, Mail, RefreshCw, Loader2, 
  Clock, Calendar, Send, CheckCircle, Bell, Code, 
  FileText, Plus, Trash2, Edit2, Eye, Save, X
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import ReactQuill from 'react-quill-new';
import 'react-quill-new/dist/quill.snow.css';
import { useAuth } from '@/contexts/AuthContext';

// Available shortcodes for email templates
const SHORTCODES = [
  { code: '{user_name}', description: "Recipient's name", example: 'John Doe' },
  { code: '{user_email}', description: "Recipient's email", example: 'john@example.com' },
  { code: '{missed_count}', description: 'Number of missed trades', example: '5' },
  { code: '{team_profit}', description: "Today's team profit", example: '$1,250.00' },
  { code: '{team_commission}', description: "Today's team commission", example: '$125.00' },
  { code: '{profit_tracker_url}', description: 'Link to Profit Tracker', example: 'https://...' },
  { code: '{current_date}', description: "Today's date", example: 'February 3, 2026' },
];

export const MissedTradersWidget = () => {
  const { user } = useAuth();
  const isMasterAdmin = user?.role === 'master_admin';
  
  const [missedTraders, setMissedTraders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sendingReminder, setSendingReminder] = useState(null);
  const [sendingNotify, setSendingNotify] = useState(null);
  const [bulkSending, setBulkSending] = useState(false);
  const [bulkNotifying, setBulkNotifying] = useState(false);
  const [emailDialogOpen, setEmailDialogOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [emailSubject, setEmailSubject] = useState('');
  const [emailBody, setEmailBody] = useState('');
  const [showShortcodes, setShowShortcodes] = useState(false);
  const [todayStats, setTodayStats] = useState({ totalProfit: 0, totalCommission: 0 });
  const [editorMode, setEditorMode] = useState('visual'); // 'visual' or 'code'
  
  // Template management
  const [templates, setTemplates] = useState([]);
  const [templateDialogOpen, setTemplateDialogOpen] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [isCreatingTemplate, setIsCreatingTemplate] = useState(false);
  const [templateName, setTemplateName] = useState('');
  const [templateCategory, setTemplateCategory] = useState('general');
  const [templateEditorMode, setTemplateEditorMode] = useState('visual');
  const [savingTemplate, setSavingTemplate] = useState(false);

  // Quill editor modules
  const quillModules = useMemo(() => ({
    toolbar: [
      [{ 'header': [1, 2, 3, false] }],
      ['bold', 'italic', 'underline', 'strike'],
      [{ 'color': [] }, { 'background': [] }],
      [{ 'list': 'ordered'}, { 'list': 'bullet' }],
      [{ 'align': [] }],
      ['link', 'image'],
      ['clean']
    ],
  }), []);

  const quillFormats = [
    'header', 'bold', 'italic', 'underline', 'strike',
    'color', 'background', 'list', 'bullet', 'align', 'link', 'image'
  ];

  const fetchMissedTraders = useCallback(async () => {
    try {
      setLoading(true);
      const [missedRes, statsRes] = await Promise.all([
        api.get('/admin/analytics/missed-trades'),
        api.get('/admin/analytics/today-stats').catch(() => ({ data: { total_profit: 0, total_commission: 0 } }))
      ]);
      setMissedTraders(missedRes.data.missed_traders || []);
      setTodayStats({
        totalProfit: statsRes.data.total_profit || 0,
        totalCommission: statsRes.data.total_commission || 0
      });
    } catch (error) {
      console.error('Failed to fetch missed traders:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchTemplates = useCallback(async () => {
    try {
      const res = await api.get('/admin/email-templates');
      setTemplates(res.data.templates || []);
    } catch (error) {
      console.error('Failed to fetch templates:', error);
    }
  }, []);

  useEffect(() => {
    fetchMissedTraders();
    fetchTemplates();
  }, [fetchMissedTraders, fetchTemplates]);

  // Process shortcodes in email body
  const processShortcodes = useCallback((body, userData) => {
    const appUrl = process.env.REACT_APP_BACKEND_URL?.replace('/api', '') || window.location.origin;
    const today = new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
    
    return body
      .replace(/\{user_name\}/g, userData.full_name || 'Member')
      .replace(/\{user_email\}/g, userData.email || '')
      .replace(/\{missed_count\}/g, String(userData.missed_trades_count || 0))
      .replace(/\{team_profit\}/g, `$${todayStats.totalProfit.toFixed(2)}`)
      .replace(/\{team_commission\}/g, `$${todayStats.totalCommission.toFixed(2)}`)
      .replace(/\{profit_tracker_url\}/g, `${appUrl}/profit-tracker`)
      .replace(/\{current_date\}/g, today);
  }, [todayStats]);

  // Generate default FOMO email content
  const generateFOMOEmail = useCallback((userData) => {
    const profit = todayStats.totalProfit.toFixed(2);
    const commission = todayStats.totalCommission.toFixed(2);
    const appUrl = process.env.REACT_APP_BACKEND_URL?.replace('/api', '') || window.location.origin;
    const missedCount = userData.missed_trades_count || 0;
    
    return {
      subject: `⚠️ You have ${missedCount} undeclared trade${missedCount > 1 ? 's' : ''}!`,
      body: `
<h2 style="color: #F59E0B;">Hi ${userData.full_name}! 👋</h2>

<p>We noticed you have <strong>${missedCount} undeclared trade${missedCount > 1 ? 's' : ''}</strong> that need your attention.</p>

<div style="background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%); padding: 24px; border-radius: 12px; margin: 24px 0; text-align: center; color: white;">
  <p style="margin: 0 0 8px 0; font-size: 14px; opacity: 0.9;">UNDECLARED TRADES</p>
  <p style="font-size: 48px; font-weight: bold; margin: 0;">${missedCount}</p>
  <p style="margin: 8px 0 0 0; font-size: 14px; opacity: 0.8;">trades waiting for your input</p>
</div>

<p>Meanwhile, the team has generated:</p>
<div style="background: #10B981; padding: 16px; border-radius: 8px; margin: 16px 0; text-align: center; color: white;">
  <p style="margin: 0; font-size: 24px; font-weight: bold;">$${profit}</p>
  <p style="margin: 4px 0 0 0; font-size: 12px; opacity: 0.8;">+ $${commission} in commissions</p>
</div>

<div style="text-align: center; margin: 32px 0;">
  <a href="${appUrl}/profit-tracker" 
     style="display: inline-block; background: #3B82F6; color: white; padding: 14px 28px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 16px;">
    📊 Report Your Trades Now
  </a>
</div>

<p style="color: #666; font-size: 14px; text-align: center;">
  Don't let your results go untracked. Every trade counts! 🚀
</p>
      `.trim()
    };
  }, [todayStats]);

  const handleSendEmail = (userData) => {
    setSelectedUser(userData);
    const { subject, body } = generateFOMOEmail(userData);
    setEmailSubject(subject);
    setEmailBody(body);
    setEditorMode('visual');
    setEmailDialogOpen(true);
  };

  const handleUseTemplate = (template) => {
    setEmailSubject(template.subject);
    setEmailBody(template.body);
    setEditorMode(template.is_html ? 'code' : 'visual');
    toast.success(`Template "${template.name}" loaded`);
  };

  const insertShortcode = (code) => {
    if (editorMode === 'code') {
      setEmailBody(prev => prev + code);
    } else {
      setEmailBody(prev => prev + code);
    }
    setShowShortcodes(false);
  };

  const confirmSendEmail = async () => {
    if (!selectedUser) return;
    
    setSendingReminder(selectedUser.id);
    
    try {
      const processedBody = processShortcodes(emailBody, selectedUser);
      const processedSubject = processShortcodes(emailSubject, selectedUser);
      
      await api.post(`/admin/members/${selectedUser.id}/send-email`, {
        subject: processedSubject,
        body: processedBody
      });
      toast.success(`Email sent to ${selectedUser.full_name}`);
      setEmailDialogOpen(false);
      setSelectedUser(null);
      setEmailSubject('');
      setEmailBody('');
    } catch (error) {
      toast.error('Failed to send email');
      console.error(error);
    } finally {
      setSendingReminder(null);
    }
  };

  const handleNotify = async (userData) => {
    setSendingNotify(userData.id);
    try {
      await api.post(`/admin/members/${userData.id}/notify`, {
        title: `⚠️ ${userData.missed_trades_count} Undeclared Trade${userData.missed_trades_count > 1 ? 's' : ''}`,
        message: `You have ${userData.missed_trades_count} undeclared trade${userData.missed_trades_count > 1 ? 's' : ''}. Please report your results.`
      });
      toast.success(`Notification sent to ${userData.full_name}`);
    } catch (error) {
      toast.info('Sending email notification instead...');
      const { subject, body } = generateFOMOEmail(userData);
      try {
        const processedBody = processShortcodes(body, userData);
        await api.post(`/admin/members/${userData.id}/send-email`, {
          subject: subject,
          body: processedBody
        });
        toast.success(`Email sent to ${userData.full_name}`);
      } catch (emailError) {
        toast.error('Failed to notify user');
      }
    } finally {
      setSendingNotify(null);
    }
  };

  const handleEmailAll = async () => {
    if (missedTraders.length === 0) return;
    
    setBulkSending(true);
    let successCount = 0;
    let failCount = 0;

    for (const trader of missedTraders) {
      const { subject, body } = generateFOMOEmail(trader);
      try {
        const processedBody = processShortcodes(body, trader);
        await api.post(`/admin/members/${trader.id}/send-email`, {
          subject: subject,
          body: processedBody
        });
        successCount++;
      } catch (error) {
        failCount++;
      }
    }

    setBulkSending(false);
    
    if (successCount > 0) {
      toast.success(`Sent ${successCount} email${successCount > 1 ? 's' : ''}`);
    }
    if (failCount > 0) {
      toast.error(`Failed to send ${failCount} email${failCount > 1 ? 's' : ''}`);
    }
  };

  const handleNotifyAll = async () => {
    if (missedTraders.length === 0) return;
    
    setBulkNotifying(true);
    let successCount = 0;
    let failCount = 0;

    for (const trader of missedTraders) {
      try {
        await api.post(`/admin/members/${trader.id}/notify`, {
          title: `⚠️ ${trader.missed_trades_count} Undeclared Trade${trader.missed_trades_count > 1 ? 's' : ''}`,
          message: `You have ${trader.missed_trades_count} undeclared trade${trader.missed_trades_count > 1 ? 's' : ''}. Please report your results.`
        });
        successCount++;
      } catch (error) {
        const { subject, body } = generateFOMOEmail(trader);
        try {
          const processedBody = processShortcodes(body, trader);
          await api.post(`/admin/members/${trader.id}/send-email`, {
            subject: subject,
            body: processedBody
          });
          successCount++;
        } catch (emailError) {
          failCount++;
        }
      }
    }

    setBulkNotifying(false);
    
    if (successCount > 0) {
      toast.success(`Notified ${successCount} member${successCount > 1 ? 's' : ''}`);
    }
    if (failCount > 0) {
      toast.error(`Failed to notify ${failCount} member${failCount > 1 ? 's' : ''}`);
    }
  };

  // Template management functions
  const openTemplateDialog = (template = null) => {
    if (template) {
      setEditingTemplate(template);
      setIsCreatingTemplate(false);
      setTemplateName(template.name);
      setEmailSubject(template.subject);
      setEmailBody(template.body);
      setTemplateCategory(template.category || 'general');
      setTemplateEditorMode(template.is_html ? 'code' : 'visual');
    } else {
      setEditingTemplate(null);
      setIsCreatingTemplate(true);
      setTemplateName('');
      setEmailSubject('');
      setEmailBody('');
      setTemplateCategory('general');
      setTemplateEditorMode('visual');
    }
    setTemplateDialogOpen(true);
  };

  const closeTemplateEdit = () => {
    setEditingTemplate(null);
    setIsCreatingTemplate(false);
  };

  const saveTemplate = async () => {
    if (!templateName.trim()) {
      toast.error('Please enter a template name');
      return;
    }
    if (!emailSubject.trim()) {
      toast.error('Please enter a subject');
      return;
    }
    if (!emailBody.trim()) {
      toast.error('Please enter email body');
      return;
    }

    setSavingTemplate(true);
    try {
      const templateData = {
        name: templateName,
        subject: emailSubject,
        body: emailBody,
        category: templateCategory,
        is_html: templateEditorMode === 'code'
      };

      if (editingTemplate) {
        await api.put(`/admin/email-templates/${editingTemplate.id}`, templateData);
        toast.success('Template updated');
      } else {
        await api.post('/admin/email-templates', templateData);
        toast.success('Template created');
      }
      
      setTemplateDialogOpen(false);
      fetchTemplates();
    } catch (error) {
      toast.error('Failed to save template');
      console.error(error);
    } finally {
      setSavingTemplate(false);
    }
  };

  const deleteTemplate = async (templateId) => {
    if (!window.confirm('Are you sure you want to delete this template?')) return;
    
    try {
      await api.delete(`/admin/email-templates/${templateId}`);
      toast.success('Template deleted');
      fetchTemplates();
    } catch (error) {
      toast.error('Failed to delete template');
    }
  };

  const today = new Date().toLocaleDateString('en-US', { 
    weekday: 'long', 
    month: 'short', 
    day: 'numeric' 
  });

  const totalMissedTrades = missedTraders.reduce((sum, t) => sum + (t.missed_trades_count || 0), 0);

  return (
    <>
      <Card className="glass-card border-zinc-800" data-testid="no-trade-members-widget">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-white flex items-center gap-2 text-sm md:text-base">
              <AlertTriangle className="w-4 h-4 md:w-5 md:h-5 text-amber-400" />
              No Trade Members
            </CardTitle>
            <div className="flex items-center gap-1">
              {isMasterAdmin && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => openTemplateDialog()}
                  className="h-8 w-8 p-0 text-blue-400 hover:text-blue-300"
                  title="Manage Templates"
                >
                  <FileText className="w-4 h-4" />
                </Button>
              )}
              <Button
                variant="ghost"
                size="sm"
                onClick={fetchMissedTraders}
                disabled={loading}
                className="h-8 w-8 p-0"
              >
                {loading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <RefreshCw className="w-4 h-4" />
                )}
              </Button>
            </div>
          </div>
          <p className="text-xs text-zinc-500 flex items-center gap-1">
            <Calendar className="w-3 h-3" /> {today}
          </p>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-zinc-400" />
            </div>
          ) : missedTraders.length === 0 ? (
            <div className="text-center py-6">
              <CheckCircle className="w-10 h-10 text-emerald-400 mx-auto mb-2" />
              <p className="text-zinc-400 text-sm">All members are up to date!</p>
            </div>
          ) : (
            <div className="space-y-3">
              {/* Summary with bulk action buttons */}
              <div className="p-3 bg-amber-500/10 rounded-lg border border-amber-500/20">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Users className="w-4 h-4 text-amber-400" />
                    <span className="text-sm text-amber-300">
                      {missedTraders.length} member{missedTraders.length > 1 ? 's' : ''} haven&apos;t traded today
                    </span>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    className="flex-1 h-8 text-xs border-amber-500/30 text-amber-400 hover:bg-amber-500/20"
                    onClick={handleEmailAll}
                    disabled={bulkSending}
                    data-testid="email-all-btn"
                  >
                    {bulkSending ? (
                      <Loader2 className="w-3 h-3 animate-spin mr-1" />
                    ) : (
                      <Mail className="w-3 h-3 mr-1" />
                    )}
                    Email All
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    className="flex-1 h-8 text-xs border-blue-500/30 text-blue-400 hover:bg-blue-500/20"
                    onClick={handleNotifyAll}
                    disabled={bulkNotifying}
                    data-testid="notify-all-btn"
                  >
                    {bulkNotifying ? (
                      <Loader2 className="w-3 h-3 animate-spin mr-1" />
                    ) : (
                      <Bell className="w-3 h-3 mr-1" />
                    )}
                    Notify All
                  </Button>
                </div>
              </div>

              {/* List */}
              <div className="space-y-2 max-h-[280px] overflow-y-auto pr-1">
                {missedTraders.map((trader) => (
                  <div 
                    key={trader.id}
                    className="flex items-center justify-between p-3 bg-zinc-900/50 rounded-lg border border-zinc-800"
                    data-testid={`missed-trader-${trader.id}`}
                  >
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      <div className="w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center flex-shrink-0">
                        <span className="text-sm font-medium text-zinc-400">
                          {trader.full_name?.charAt(0) || '?'}
                        </span>
                      </div>
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-white truncate">
                          {trader.full_name}
                        </p>
                        <div className="flex items-center gap-1 text-xs text-zinc-500">
                          <Clock className="w-3 h-3 flex-shrink-0" />
                          <span className="truncate">
                            {trader.last_trade_at ? (
                              <>Last: {formatDistanceToNow(new Date(trader.last_trade_at), { addSuffix: true })}</>
                            ) : (
                              'Never traded'
                            )}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-1 flex-shrink-0">
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-8 w-8 p-0 text-amber-400 hover:text-amber-300 hover:bg-amber-500/10"
                        onClick={() => handleSendEmail(trader)}
                        disabled={sendingReminder === trader.id}
                        title="Send Email"
                        data-testid={`email-btn-${trader.id}`}
                      >
                        {sendingReminder === trader.id ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <Mail className="w-4 h-4" />
                        )}
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-8 w-8 p-0 text-blue-400 hover:text-blue-300 hover:bg-blue-500/10"
                        onClick={() => handleNotify(trader)}
                        disabled={sendingNotify === trader.id}
                        title="Send Notification"
                        data-testid={`notify-btn-${trader.id}`}
                      >
                        {sendingNotify === trader.id ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <Bell className="w-4 h-4" />
                        )}
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* WYSIWYG Email Dialog */}
      <Dialog open={emailDialogOpen} onOpenChange={setEmailDialogOpen}>
        <DialogContent className="glass-card border-zinc-800 max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Mail className="w-5 h-5 text-blue-400" />
              Compose Email to {selectedUser?.full_name}
              {selectedUser?.missed_trades_count > 0 && (
                <Badge variant="outline" className="bg-red-500/10 text-red-400 border-red-500/30 ml-2">
                  {selectedUser.missed_trades_count} missed
                </Badge>
              )}
            </DialogTitle>
            <DialogDescription className="text-zinc-400">
              Use the editor below to compose your email. Toggle between Visual and Code mode.
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            {/* Templates Selection */}
            {templates.length > 0 && (
              <div className="space-y-2">
                <Label className="text-zinc-400">Use Template</Label>
                <div className="flex flex-wrap gap-2">
                  {templates.slice(0, 5).map((template) => (
                    <Button
                      key={template.id}
                      variant="outline"
                      size="sm"
                      onClick={() => handleUseTemplate(template)}
                      className="border-zinc-700 text-zinc-300 hover:bg-zinc-800"
                    >
                      <FileText className="w-3 h-3 mr-1" />
                      {template.name}
                    </Button>
                  ))}
                </div>
              </div>
            )}

            {/* Subject Line */}
            <div className="space-y-2">
              <Label htmlFor="email-subject" className="text-zinc-400">Subject</Label>
              <Input
                id="email-subject"
                value={emailSubject}
                onChange={(e) => setEmailSubject(e.target.value)}
                className="input-dark"
                placeholder="Email subject..."
              />
            </div>
            
            {/* Editor Mode Toggle + Shortcodes */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowShortcodes(!showShortcodes)}
                  className="border-zinc-700 text-zinc-400 hover:text-white"
                >
                  <Code className="w-4 h-4 mr-2" />
                  Shortcodes
                </Button>
              </div>
              <Tabs value={editorMode} onValueChange={setEditorMode} className="w-auto">
                <TabsList className="bg-zinc-800">
                  <TabsTrigger value="visual" className="text-xs">Visual</TabsTrigger>
                  <TabsTrigger value="code" className="text-xs">HTML Code</TabsTrigger>
                </TabsList>
              </Tabs>
            </div>
            
            {/* Shortcodes Panel */}
            {showShortcodes && (
              <div className="p-3 rounded-lg bg-zinc-900/50 border border-zinc-800 space-y-2">
                <p className="text-xs text-zinc-400 font-medium mb-2">Click to insert:</p>
                <div className="grid grid-cols-2 gap-2">
                  {SHORTCODES.map((sc) => (
                    <button
                      key={sc.code}
                      type="button"
                      onClick={() => insertShortcode(sc.code)}
                      className="text-left p-2 rounded bg-zinc-800/50 hover:bg-zinc-700/50 transition-colors"
                    >
                      <code className="text-blue-400 text-sm">{sc.code}</code>
                      <p className="text-xs text-zinc-500 mt-0.5">{sc.description}</p>
                    </button>
                  ))}
                </div>
              </div>
            )}
            
            {/* Rich Text / Code Editor */}
            <div className="space-y-2">
              <Label className="text-zinc-400">Email Body</Label>
              {editorMode === 'visual' ? (
                <div className="rounded-lg overflow-hidden border border-zinc-800 bg-white">
                  <ReactQuill
                    theme="snow"
                    value={emailBody}
                    onChange={setEmailBody}
                    modules={quillModules}
                    formats={quillFormats}
                    className="bg-white text-black"
                    style={{ minHeight: '250px' }}
                  />
                </div>
              ) : (
                <Textarea
                  value={emailBody}
                  onChange={(e) => setEmailBody(e.target.value)}
                  className="input-dark font-mono text-sm min-h-[300px]"
                  placeholder="<html>...</html>"
                />
              )}
              <p className="text-xs text-zinc-500">
                💡 Shortcodes like {'{user_name}'} will be replaced with actual values when sent.
              </p>
            </div>
          </div>
          
          <DialogFooter className="gap-2">
            <Button
              variant="outline"
              onClick={() => setEmailDialogOpen(false)}
              className="border-zinc-700"
            >
              Cancel
            </Button>
            <Button
              onClick={confirmSendEmail}
              className="btn-primary"
              disabled={sendingReminder || !emailSubject.trim() || !emailBody.trim()}
            >
              {sendingReminder ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                  Sending...
                </>
              ) : (
                <>
                  <Send className="w-4 h-4 mr-2" />
                  Send Email
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Template Management Dialog (Master Admin Only) */}
      <Dialog open={templateDialogOpen} onOpenChange={setTemplateDialogOpen}>
        <DialogContent className="glass-card border-zinc-800 max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <FileText className="w-5 h-5 text-blue-400" />
              {editingTemplate ? 'Edit Template' : 'Email Templates'}
            </DialogTitle>
            <DialogDescription className="text-zinc-400">
              {editingTemplate 
                ? 'Update your email template with shortcodes for personalization.'
                : 'Create and manage reusable email templates with shortcodes.'}
            </DialogDescription>
          </DialogHeader>
          
          {!editingTemplate && !isCreatingTemplate ? (
            /* Template List View */
            <div className="space-y-4 py-4">
              <div className="flex justify-between items-center">
                <p className="text-sm text-zinc-400">{templates.length} template{templates.length !== 1 ? 's' : ''}</p>
                <Button
                  onClick={() => {
                    setIsCreatingTemplate(true);
                    setEditingTemplate(null);
                    setTemplateName('');
                    setEmailSubject('');
                    setEmailBody('');
                    setTemplateCategory('general');
                    setTemplateEditorMode('visual');
                  }}
                  className="btn-primary"
                  size="sm"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  New Template
                </Button>
              </div>
              
              {templates.length === 0 ? (
                <div className="text-center py-8 text-zinc-500">
                  <FileText className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p>No templates yet. Create your first one!</p>
                </div>
              ) : (
                <div className="space-y-2 max-h-[400px] overflow-y-auto">
                  {templates.map((template) => (
                    <div 
                      key={template.id}
                      className="flex items-center justify-between p-4 bg-zinc-900/50 rounded-lg border border-zinc-800"
                    >
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <h4 className="text-white font-medium truncate">{template.name}</h4>
                          {template.is_html && (
                            <Badge variant="outline" className="bg-purple-500/10 text-purple-400 border-purple-500/30 text-xs">
                              HTML
                            </Badge>
                          )}
                          <Badge variant="outline" className="bg-zinc-500/10 text-zinc-400 border-zinc-500/30 text-xs">
                            {template.category}
                          </Badge>
                        </div>
                        <p className="text-sm text-zinc-500 truncate mt-1">{template.subject}</p>
                      </div>
                      <div className="flex items-center gap-1 ml-4">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setEditingTemplate(template);
                            setIsCreatingTemplate(false);
                            setTemplateName(template.name);
                            setEmailSubject(template.subject);
                            setEmailBody(template.body);
                            setTemplateCategory(template.category || 'general');
                            setTemplateEditorMode(template.is_html ? 'code' : 'visual');
                          }}
                          className="h-8 w-8 p-0 text-blue-400 hover:text-blue-300"
                        >
                          <Edit2 className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => deleteTemplate(template.id)}
                          className="h-8 w-8 p-0 text-red-400 hover:text-red-300"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            /* Template Edit View */
            <div className="space-y-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-zinc-400">Template Name</Label>
                  <Input
                    value={templateName}
                    onChange={(e) => setTemplateName(e.target.value)}
                    className="input-dark"
                    placeholder="e.g., Weekly Reminder"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-zinc-400">Category</Label>
                  <Select value={templateCategory} onValueChange={setTemplateCategory}>
                    <SelectTrigger className="input-dark">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-zinc-900 border-zinc-800">
                      <SelectItem value="general">General</SelectItem>
                      <SelectItem value="reminder">Reminder</SelectItem>
                      <SelectItem value="announcement">Announcement</SelectItem>
                      <SelectItem value="welcome">Welcome</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              <div className="space-y-2">
                <Label className="text-zinc-400">Subject</Label>
                <Input
                  value={emailSubject}
                  onChange={(e) => setEmailSubject(e.target.value)}
                  className="input-dark"
                  placeholder="Email subject with {shortcodes}"
                />
              </div>
              
              {/* Shortcodes Reference */}
              <div className="p-3 rounded-lg bg-zinc-900/50 border border-zinc-800">
                <p className="text-xs text-zinc-400 font-medium mb-2">Available Shortcodes:</p>
                <div className="flex flex-wrap gap-2">
                  {SHORTCODES.map((sc) => (
                    <code 
                      key={sc.code}
                      className="text-xs bg-zinc-800 text-blue-400 px-2 py-1 rounded cursor-pointer hover:bg-zinc-700"
                      onClick={() => {
                        if (templateEditorMode === 'code') {
                          setEmailBody(prev => prev + sc.code);
                        } else {
                          setEmailBody(prev => prev + sc.code);
                        }
                      }}
                      title={sc.description}
                    >
                      {sc.code}
                    </code>
                  ))}
                </div>
              </div>
              
              {/* Editor Mode Toggle */}
              <div className="flex items-center justify-between">
                <Label className="text-zinc-400">Email Body</Label>
                <Tabs value={templateEditorMode} onValueChange={setTemplateEditorMode} className="w-auto">
                  <TabsList className="bg-zinc-800">
                    <TabsTrigger value="visual" className="text-xs">Visual</TabsTrigger>
                    <TabsTrigger value="code" className="text-xs">HTML Code</TabsTrigger>
                  </TabsList>
                </Tabs>
              </div>
              
              {templateEditorMode === 'visual' ? (
                <div className="rounded-lg overflow-hidden border border-zinc-800 bg-white">
                  <ReactQuill
                    theme="snow"
                    value={emailBody}
                    onChange={setEmailBody}
                    modules={quillModules}
                    formats={quillFormats}
                    className="bg-white text-black"
                    style={{ minHeight: '250px' }}
                  />
                </div>
              ) : (
                <Textarea
                  value={emailBody}
                  onChange={(e) => setEmailBody(e.target.value)}
                  className="input-dark font-mono text-sm min-h-[300px]"
                  placeholder="<html>...</html>"
                />
              )}
            </div>
          )}
          
          <DialogFooter className="gap-2">
            {(editingTemplate || isCreatingTemplate) ? (
              <>
                <Button
                  variant="outline"
                  onClick={closeTemplateEdit}
                  className="border-zinc-700"
                >
                  <X className="w-4 h-4 mr-2" />
                  Back
                </Button>
                <Button
                  onClick={saveTemplate}
                  className="btn-primary"
                  disabled={savingTemplate}
                >
                  {savingTemplate ? (
                    <Loader2 className="w-4 h-4 animate-spin mr-2" />
                  ) : (
                    <Save className="w-4 h-4 mr-2" />
                  )}
                  {editingTemplate ? 'Update' : 'Create'} Template
                </Button>
              </>
            ) : (
              <Button
                variant="outline"
                onClick={() => setTemplateDialogOpen(false)}
                className="border-zinc-700"
              >
                Close
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Custom styles for Quill editor */}
      <style>{`
        .ql-toolbar.ql-snow {
          border-color: #3f3f46 !important;
          background: #18181b !important;
        }
        .ql-toolbar.ql-snow .ql-stroke {
          stroke: #a1a1aa !important;
        }
        .ql-toolbar.ql-snow .ql-fill {
          fill: #a1a1aa !important;
        }
        .ql-toolbar.ql-snow .ql-picker-label {
          color: #a1a1aa !important;
        }
        .ql-toolbar.ql-snow button:hover .ql-stroke,
        .ql-toolbar.ql-snow .ql-picker-label:hover .ql-stroke {
          stroke: #fff !important;
        }
        .ql-toolbar.ql-snow button:hover .ql-fill,
        .ql-toolbar.ql-snow .ql-picker-label:hover .ql-fill {
          fill: #fff !important;
        }
        .ql-container.ql-snow {
          border-color: #3f3f46 !important;
          min-height: 200px;
        }
        .ql-editor {
          min-height: 200px;
          font-size: 14px;
        }
      `}</style>
    </>
  );
};

export default MissedTradersWidget;
