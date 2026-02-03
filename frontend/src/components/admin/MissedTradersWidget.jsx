import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import api from '@/lib/api';
import { toast } from 'sonner';
import { 
  AlertTriangle, Users, Mail, RefreshCw, Loader2, 
  Clock, Calendar, Send, CheckCircle, Bell, Code, Smile
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import ReactQuill from 'react-quill';
import 'react-quill/dist/quill.snow.css';

// Available shortcodes for email templates
const SHORTCODES = [
  { code: '{user_name}', description: "Recipient's name", example: 'John Doe' },
  { code: '{team_profit}', description: "Today's team profit", example: '$1,250.00' },
  { code: '{team_commission}', description: "Today's team commission", example: '$125.00' },
  { code: '{profit_tracker_url}', description: 'Link to Profit Tracker', example: 'https://...' },
];

export const MissedTradersWidget = () => {
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

  // Quill editor modules
  const quillModules = useMemo(() => ({
    toolbar: [
      [{ 'header': [1, 2, 3, false] }],
      ['bold', 'italic', 'underline', 'strike'],
      [{ 'color': [] }, { 'background': [] }],
      [{ 'list': 'ordered'}, { 'list': 'bullet' }],
      [{ 'align': [] }],
      ['link'],
      ['clean']
    ],
  }), []);

  const quillFormats = [
    'header', 'bold', 'italic', 'underline', 'strike',
    'color', 'background', 'list', 'bullet', 'align', 'link'
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

  useEffect(() => {
    fetchMissedTraders();
  }, [fetchMissedTraders]);

  // Process shortcodes in email body
  const processShortcodes = useCallback((body, userName) => {
    const appUrl = process.env.REACT_APP_BACKEND_URL?.replace('/api', '') || window.location.origin;
    
    return body
      .replace(/\{user_name\}/g, userName)
      .replace(/\{team_profit\}/g, `$${todayStats.totalProfit.toFixed(2)}`)
      .replace(/\{team_commission\}/g, `$${todayStats.totalCommission.toFixed(2)}`)
      .replace(/\{profit_tracker_url\}/g, `${appUrl}/profit-tracker`);
  }, [todayStats]);

  // Generate default FOMO email content
  const generateFOMOEmail = useCallback((userName) => {
    const profit = todayStats.totalProfit.toFixed(2);
    const commission = todayStats.totalCommission.toFixed(2);
    const appUrl = process.env.REACT_APP_BACKEND_URL?.replace('/api', '') || window.location.origin;
    
    return {
      subject: `💰 You're Missing Out! The Team Made $${profit} Today`,
      body: `
<h2 style="color: #10B981;">Hi ${userName}! 👋</h2>

<p>We noticed you haven't reported your trade results yet today.</p>

<div style="background: linear-gradient(135deg, #10B981 0%, #059669 100%); padding: 24px; border-radius: 12px; margin: 24px 0; text-align: center; color: white;">
  <p style="margin: 0 0 8px 0; font-size: 14px; opacity: 0.9;">THE TEAM GENERATED TODAY</p>
  <p style="font-size: 36px; font-weight: bold; margin: 0;">$${profit}</p>
  <p style="margin: 8px 0 0 0; font-size: 14px; opacity: 0.8;">+ $${commission} in commissions</p>
</div>

<p style="font-size: 18px; color: #EF4444; font-weight: bold; text-align: center;">
  🚨 If you didn't trade, you're missing out!
</p>

<div style="text-align: center; margin: 32px 0;">
  <a href="${appUrl}/profit-tracker" 
     style="display: inline-block; background: #3B82F6; color: white; padding: 14px 28px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 16px;">
    📊 Oh, you traded? Report Your Profit Now
  </a>
</div>

<p style="color: #666; font-size: 14px; text-align: center;">
  Don't let your results go untracked. Every trade counts towards your growth! 🚀
</p>
      `.trim()
    };
  }, [todayStats]);

  const handleSendEmail = (user) => {
    setSelectedUser(user);
    const { subject, body } = generateFOMOEmail(user.full_name);
    setEmailSubject(subject);
    setEmailBody(body);
    setEmailDialogOpen(true);
  };

  const insertShortcode = (code) => {
    setEmailBody(prev => prev + code);
    setShowShortcodes(false);
  };

  const confirmSendEmail = async () => {
    if (!selectedUser) return;
    
    setSendingReminder(selectedUser.id);
    
    try {
      // Process shortcodes before sending
      const processedBody = processShortcodes(emailBody, selectedUser.full_name);
      const processedSubject = processShortcodes(emailSubject, selectedUser.full_name);
      
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

  const handleNotify = async (user) => {
    setSendingNotify(user.id);
    try {
      await api.post(`/admin/members/${user.id}/notify`, {
        title: "📊 Report Your Trade Results",
        message: `The team made $${todayStats.totalProfit.toFixed(2)} today! Don't forget to log your results.`
      });
      toast.success(`Notification sent to ${user.full_name}`);
    } catch (error) {
      toast.info('Sending email notification instead...');
      const { subject, body } = generateFOMOEmail(user.full_name);
      try {
        await api.post(`/admin/members/${user.id}/send-email`, {
          subject: subject,
          body: body
        });
        toast.success(`Email sent to ${user.full_name}`);
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
      const { subject, body } = generateFOMOEmail(trader.full_name);
      try {
        await api.post(`/admin/members/${trader.id}/send-email`, {
          subject: subject,
          body: body
        });
        successCount++;
      } catch (error) {
        failCount++;
        console.error(`Failed to send to ${trader.full_name}:`, error);
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
          title: "📊 Report Your Trade Results",
          message: `The team made $${todayStats.totalProfit.toFixed(2)} today! Don't forget to log your results.`
        });
        successCount++;
      } catch (error) {
        const { subject, body } = generateFOMOEmail(trader.full_name);
        try {
          await api.post(`/admin/members/${trader.id}/send-email`, {
            subject: subject,
            body: body
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

  const today = new Date().toLocaleDateString('en-US', { 
    weekday: 'long', 
    month: 'short', 
    day: 'numeric' 
  });

  return (
    <>
      <Card className="glass-card border-zinc-800" data-testid="missed-traders-widget">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-white flex items-center gap-2 text-sm md:text-base">
              <AlertTriangle className="w-4 h-4 md:w-5 md:h-5 text-amber-400" />
              Didn&apos;t Report Today
            </CardTitle>
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
              <p className="text-zinc-400 text-sm">Everyone reported today!</p>
            </div>
          ) : (
            <div className="space-y-3">
              {/* Today's Stats Summary */}
              {(todayStats.totalProfit > 0 || todayStats.totalCommission > 0) && (
                <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-center">
                  <p className="text-xs text-emerald-400 uppercase tracking-wider">Team Made Today</p>
                  <div className="flex items-center justify-center gap-3 mt-1">
                    <span className="text-lg font-mono font-bold text-emerald-400">
                      ${todayStats.totalProfit.toFixed(2)}
                    </span>
                    {todayStats.totalCommission > 0 && (
                      <span className="text-sm text-emerald-400/70">
                        +${todayStats.totalCommission.toFixed(2)} comm
                      </span>
                    )}
                  </div>
                </div>
              )}

              {/* Summary with bulk action buttons */}
              <div className="p-3 bg-amber-500/10 rounded-lg border border-amber-500/20">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Users className="w-4 h-4 text-amber-400" />
                    <span className="text-sm text-amber-300">
                      {missedTraders.length} haven&apos;t reported
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
                              formatDistanceToNow(new Date(trader.last_trade_at), { addSuffix: true })
                            ) : (
                              'Never'
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
        <DialogContent className="glass-card border-zinc-800 max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Mail className="w-5 h-5 text-blue-400" />
              Compose Email to {selectedUser?.full_name}
            </DialogTitle>
            <DialogDescription className="text-zinc-400">
              Use the rich text editor to format your email. Click &quot;Shortcodes&quot; to insert dynamic content.
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
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
            
            {/* Shortcodes Button */}
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
              <span className="text-xs text-zinc-500">Insert dynamic content into your email</span>
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
            
            {/* Rich Text Editor */}
            <div className="space-y-2">
              <Label className="text-zinc-400">Email Body</Label>
              <div className="rounded-lg overflow-hidden border border-zinc-800 bg-white">
                <ReactQuill
                  theme="snow"
                  value={emailBody}
                  onChange={setEmailBody}
                  modules={quillModules}
                  formats={quillFormats}
                  className="bg-white text-black"
                  style={{ minHeight: '200px' }}
                />
              </div>
              <p className="text-xs text-zinc-500">
                💡 Tip: Use emojis directly in your text! Just copy/paste them: 🎉 💰 📊 🚀 ✨
              </p>
            </div>
          </div>
          
          <DialogFooter>
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
