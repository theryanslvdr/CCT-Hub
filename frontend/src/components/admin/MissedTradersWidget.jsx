import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import api from '@/lib/api';
import { toast } from 'sonner';
import { 
  AlertTriangle, Users, Mail, RefreshCw, Loader2, 
  Clock, Calendar, Send, CheckCircle, XCircle
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

export const MissedTradersWidget = () => {
  const [missedTraders, setMissedTraders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sendingReminder, setSendingReminder] = useState(null);
  const [bulkSending, setBulkSending] = useState(false);
  const [emailDialogOpen, setEmailDialogOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [customMessage, setCustomMessage] = useState('');

  const fetchMissedTraders = useCallback(async () => {
    try {
      setLoading(true);
      const res = await api.get('/admin/analytics/missed-trades');
      setMissedTraders(res.data.missed_traders || []);
    } catch (error) {
      console.error('Failed to fetch missed traders:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMissedTraders();
  }, [fetchMissedTraders]);

  const handleSendReminder = async (user) => {
    setSelectedUser(user);
    setCustomMessage(`Hi ${user.full_name},\n\nWe noticed you haven't logged your trade for today. Don't forget to record your results in the Trade Monitor!\n\nKeep up the great work!`);
    setEmailDialogOpen(true);
  };

  const confirmSendReminder = async () => {
    if (!selectedUser) return;
    
    setSendingReminder(selectedUser.id);
    try {
      await api.post(`/admin/members/${selectedUser.id}/send-email`, {
        subject: '📊 Trade Reminder - Log Your Results',
        body: customMessage.replace(/\n/g, '<br>')
      });
      toast.success(`Reminder sent to ${selectedUser.full_name}`);
      setEmailDialogOpen(false);
      setSelectedUser(null);
      setCustomMessage('');
    } catch (error) {
      toast.error('Failed to send reminder');
      console.error(error);
    } finally {
      setSendingReminder(null);
    }
  };

  const handleSendBulkReminders = async () => {
    if (missedTraders.length === 0) return;
    
    setBulkSending(true);
    let successCount = 0;
    let failCount = 0;

    for (const trader of missedTraders) {
      try {
        await api.post(`/admin/members/${trader.id}/send-email`, {
          subject: '📊 Trade Reminder - Log Your Results',
          body: `Hi ${trader.full_name},<br><br>We noticed you haven't logged your trade for today. Don't forget to record your results in the Trade Monitor!<br><br>Keep up the great work!`
        });
        successCount++;
      } catch (error) {
        failCount++;
        console.error(`Failed to send to ${trader.full_name}:`, error);
      }
    }

    setBulkSending(false);
    
    if (successCount > 0) {
      toast.success(`Sent ${successCount} reminder${successCount > 1 ? 's' : ''}`);
    }
    if (failCount > 0) {
      toast.error(`Failed to send ${failCount} reminder${failCount > 1 ? 's' : ''}`);
    }
  };

  const today = new Date().toLocaleDateString('en-US', { 
    weekday: 'long', 
    month: 'short', 
    day: 'numeric' 
  });

  return (
    <>
      <Card className="glass-card border-zinc-800">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-white flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-400" />
              Didn&apos;t Trade Today
            </CardTitle>
            <Button
              variant="ghost"
              size="sm"
              onClick={fetchMissedTraders}
              disabled={loading}
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
              <p className="text-zinc-400 text-sm">Everyone traded today!</p>
            </div>
          ) : (
            <div className="space-y-3">
              {/* Summary */}
              <div className="flex items-center justify-between p-2 bg-amber-500/10 rounded-lg border border-amber-500/20">
                <div className="flex items-center gap-2">
                  <Users className="w-4 h-4 text-amber-400" />
                  <span className="text-sm text-amber-300">
                    {missedTraders.length} member{missedTraders.length > 1 ? 's' : ''} haven&apos;t traded
                  </span>
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  className="h-7 text-xs border-amber-500/30 text-amber-400 hover:bg-amber-500/20"
                  onClick={handleSendBulkReminders}
                  disabled={bulkSending}
                >
                  {bulkSending ? (
                    <Loader2 className="w-3 h-3 animate-spin mr-1" />
                  ) : (
                    <Mail className="w-3 h-3 mr-1" />
                  )}
                  Send All
                </Button>
              </div>

              {/* List */}
              <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1">
                {missedTraders.map((trader) => (
                  <div 
                    key={trader.id}
                    className="flex items-center justify-between p-3 bg-zinc-900/50 rounded-lg border border-zinc-800"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center">
                        <span className="text-sm font-medium text-zinc-400">
                          {trader.full_name?.charAt(0) || '?'}
                        </span>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-white">
                          {trader.full_name}
                        </p>
                        <div className="flex items-center gap-2 text-xs text-zinc-500">
                          <Clock className="w-3 h-3" />
                          {trader.last_trade_at ? (
                            `Last trade ${formatDistanceToNow(new Date(trader.last_trade_at), { addSuffix: true })}`
                          ) : (
                            'No trades yet'
                          )}
                        </div>
                      </div>
                    </div>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="h-8 text-xs text-zinc-400 hover:text-white"
                      onClick={() => handleSendReminder(trader)}
                      disabled={sendingReminder === trader.id}
                    >
                      {sendingReminder === trader.id ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Mail className="w-4 h-4" />
                      )}
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Email Dialog */}
      <Dialog open={emailDialogOpen} onOpenChange={setEmailDialogOpen}>
        <DialogContent className="glass-card border-zinc-800">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Mail className="w-5 h-5 text-blue-400" />
              Send Reminder to {selectedUser?.full_name}
            </DialogTitle>
            <DialogDescription className="text-zinc-400">
              Customize your message before sending
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Textarea
              value={customMessage}
              onChange={(e) => setCustomMessage(e.target.value)}
              className="input-dark min-h-[150px]"
              placeholder="Enter your message..."
            />
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
              onClick={confirmSendReminder}
              className="btn-primary"
              disabled={sendingReminder}
            >
              {sendingReminder ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                  Sending...
                </>
              ) : (
                <>
                  <Send className="w-4 h-4 mr-2" />
                  Send Reminder
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default MissedTradersWidget;
