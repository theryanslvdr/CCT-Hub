import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { userAPI, authAPI } from '@/lib/api';
import api from '@/lib/api';
import { usePushNotifications } from '@/lib/usePushNotifications';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { toast } from 'sonner';
import { User, Globe, Lock, Save, Eye, EyeOff, Bell, Radio, Clock, AlertTriangle, Users, TrendingUp, BarChart3, Loader2, BellRing, BellOff } from 'lucide-react';

const timezones = [
  { value: 'Asia/Manila', label: 'Philippines (GMT+8)' },
  { value: 'Asia/Singapore', label: 'Singapore (GMT+8)' },
  { value: 'Asia/Taipei', label: 'Taiwan (GMT+8)' },
  { value: 'Asia/Hong_Kong', label: 'Hong Kong (GMT+8)' },
  { value: 'Asia/Tokyo', label: 'Japan (GMT+9)' },
  { value: 'Asia/Seoul', label: 'South Korea (GMT+9)' },
  { value: 'Asia/Kolkata', label: 'India (GMT+5:30)' },
  { value: 'Asia/Dubai', label: 'Dubai (GMT+4)' },
  { value: 'Europe/London', label: 'London (GMT+0)' },
  { value: 'Europe/Paris', label: 'Paris (GMT+1)' },
  { value: 'America/New_York', label: 'New York (GMT-5)' },
  { value: 'America/Los_Angeles', label: 'Los Angeles (GMT-8)' },
  { value: 'Australia/Sydney', label: 'Sydney (GMT+11)' },
  { value: 'UTC', label: 'UTC (GMT+0)' },
];

const MEMBER_NOTIFICATION_ITEMS = [
  { key: 'trading_signal', label: 'Trading Signal Alerts', desc: 'Get notified when a new trading signal is published', icon: Radio, color: 'text-orange-400' },
  { key: 'pre_trade_10min', label: '10-Minute Pre-Trade Alert', desc: 'Reminder 10 minutes before scheduled trade time', icon: Clock, color: 'text-amber-400' },
  { key: 'pre_trade_5min', label: '5-Minute Pre-Trade Alert', desc: 'Reminder 5 minutes before scheduled trade time', icon: Clock, color: 'text-orange-400' },
  { key: 'missed_trade_report', label: 'Missed Trade Reports', desc: 'Get notified when you miss a trading day', icon: AlertTriangle, color: 'text-red-400' },
];

const ADMIN_NOTIFICATION_ITEMS = [
  { key: 'member_trade_submitted', label: 'Member Trade Submitted', desc: 'When members submit their trade results', icon: Users, color: 'text-emerald-400' },
  { key: 'member_missed_trade', label: 'Member Missed Trade', desc: 'When members miss their trades', icon: AlertTriangle, color: 'text-red-400' },
  { key: 'member_profit_report', label: 'Member Profit Reports', desc: 'Profit and commission details per member', icon: TrendingUp, color: 'text-cyan-400' },
  { key: 'daily_summary', label: 'Daily Trade Summary', desc: 'End-of-day summary of all trading activity', icon: BarChart3, color: 'text-purple-400' },
];

const NotifToggle = ({ item, value, onChange }) => {
  const Icon = item.icon;
  return (
    <div className="flex items-center justify-between p-3 rounded-lg bg-[#0d0d0d]/50 border border-white/[0.06] hover:border-white/[0.08] transition-colors" data-testid={`notif-toggle-${item.key}`}>
      <div className="flex items-center gap-3 flex-1 min-w-0">
        <div className={`w-8 h-8 rounded-lg bg-[#1a1a1a] flex items-center justify-center flex-shrink-0 ${item.color}`}>
          <Icon className="w-4 h-4" />
        </div>
        <div className="min-w-0">
          <p className="text-sm font-medium text-white">{item.label}</p>
          <p className="text-xs text-zinc-500 truncate">{item.desc}</p>
        </div>
      </div>
      <Switch checked={value} onCheckedChange={onChange} data-testid={`notif-switch-${item.key}`} />
    </div>
  );
};

const PushNotificationToggle = () => {
  const { isSubscribed, isSupported, permission, loading, subscribe, unsubscribe } = usePushNotifications();

  if (!isSupported) {
    return (
      <div className="p-3 rounded-lg bg-[#0d0d0d]/50 border border-white/[0.06]">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-[#1a1a1a] flex items-center justify-center text-zinc-500">
            <BellOff className="w-4 h-4" />
          </div>
          <div>
            <p className="text-sm text-zinc-400">Push notifications not supported</p>
            <p className="text-xs text-zinc-600">Your browser doesn't support push notifications</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-3 rounded-lg bg-[#0d0d0d]/50 border border-orange-500/20 hover:border-orange-500/30 transition-colors" data-testid="push-notification-toggle">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${isSubscribed ? 'bg-orange-500/10 text-orange-400' : 'bg-[#1a1a1a] text-zinc-400'}`}>
            {isSubscribed ? <BellRing className="w-4 h-4" /> : <Bell className="w-4 h-4" />}
          </div>
          <div>
            <p className="text-sm font-medium text-white">Push Notifications</p>
            <p className="text-xs text-zinc-500">
              {isSubscribed ? 'Receiving push notifications on this device' : 
               permission === 'denied' ? 'Blocked — enable in browser settings' :
               'Enable to receive real-time alerts'}
            </p>
          </div>
        </div>
        <Switch
          checked={isSubscribed}
          disabled={loading || permission === 'denied'}
          onCheckedChange={async (checked) => {
            if (checked) {
              const success = await subscribe();
              if (success) toast.success('Push notifications enabled!');
              else if (permission === 'denied') toast.error('Notifications blocked. Please enable in browser settings.');
            } else {
              const success = await unsubscribe();
              if (success) toast.success('Push notifications disabled');
            }
          }}
          data-testid="push-notification-switch"
        />
      </div>
    </div>
  );
};

export const ProfilePage = () => {
  const { user, updateUser, isSuperAdmin, isMasterAdmin } = useAuth();
  const isAdmin = isSuperAdmin() || isMasterAdmin();
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [timezone, setTimezone] = useState(user?.timezone || 'Asia/Manila');
  const [saving, setSaving] = useState(false);
  
  // Password reset fields
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [changingPassword, setChangingPassword] = useState(false);

  // Notification preferences
  const [notifPrefs, setNotifPrefs] = useState(null);
  const [loadingPrefs, setLoadingPrefs] = useState(true);
  const [savingPrefs, setSavingPrefs] = useState(false);

  useEffect(() => {
    if (user) {
      setFullName(user.full_name || '');
      setTimezone(user.timezone || 'Asia/Manila');
    }
  }, [user]);

  useEffect(() => {
    const fetchPrefs = async () => {
      try {
        const res = await api.get('/users/notification-preferences');
        setNotifPrefs(res.data.preferences);
      } catch {
        // Use defaults
        setNotifPrefs(isAdmin ? {
          trading_signal: true, pre_trade_10min: true, pre_trade_5min: true,
          missed_trade_report: true, member_trade_submitted: true,
          member_missed_trade: true, member_profit_report: true, daily_summary: true,
        } : {
          trading_signal: true, pre_trade_10min: true, pre_trade_5min: true, missed_trade_report: true,
        });
      } finally {
        setLoadingPrefs(false);
      }
    };
    fetchPrefs();
  }, [isAdmin]);

  const handleSave = async () => {
    setSaving(true);
    try {
      const response = await userAPI.updateProfile({ full_name: fullName, timezone });
      updateUser(response.data);
      toast.success('Profile updated successfully!');
    } catch {
      toast.error('Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  const handleSaveNotifPrefs = async () => {
    setSavingPrefs(true);
    try {
      await api.put('/users/notification-preferences', notifPrefs);
      toast.success('Notification preferences saved!');
    } catch {
      toast.error('Failed to save notification preferences');
    } finally {
      setSavingPrefs(false);
    }
  };

  const handleChangePassword = async () => {
    if (!currentPassword || !newPassword || !confirmPassword) {
      toast.error('Please fill in all password fields');
      return;
    }
    if (newPassword !== confirmPassword) {
      toast.error('New passwords do not match');
      return;
    }
    if (newPassword.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }
    setChangingPassword(true);
    try {
      await userAPI.changePassword({ current_password: currentPassword, new_password: newPassword });
      toast.success('Password changed successfully!');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to change password');
    } finally {
      setChangingPassword(false);
    }
  };

  const currentTime = new Date().toLocaleTimeString('en-US', {
    hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false, timeZone: timezone,
  });

  const togglePref = (key) => {
    setNotifPrefs(prev => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <Card className="glass-card">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <User className="w-5 h-5" /> Profile Settings
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div>
            <Label className="text-zinc-300">Full Name</Label>
            <Input value={fullName} onChange={(e) => setFullName(e.target.value)} className="input-dark mt-1" data-testid="profile-name-input" />
          </div>
          <div>
            <Label className="text-zinc-300">Email</Label>
            <Input value={user?.email || ''} disabled className="input-dark mt-1 opacity-50 cursor-not-allowed" />
            <p className="text-xs text-zinc-500 mt-1">Email cannot be changed</p>
          </div>
        </CardContent>
      </Card>

      {/* Timezone Settings */}
      <Card className="glass-card">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Globe className="w-5 h-5" /> Timezone Settings
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div>
            <Label className="text-zinc-300">Your Timezone</Label>
            <Select value={timezone} onValueChange={setTimezone}>
              <SelectTrigger className="input-dark mt-1" data-testid="timezone-select">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {timezones.map((tz) => (
                  <SelectItem key={tz.value} value={tz.value}>{tz.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-xs text-zinc-500 mt-1">This timezone will be used in the Trade Monitor</p>
          </div>
          <div className="p-4 rounded-lg bg-[#0d0d0d]/50 border border-white/[0.06]">
            <p className="text-xs text-zinc-500 mb-2">Current time in your timezone:</p>
            <p className="text-3xl font-mono font-bold text-white">{currentTime}</p>
          </div>
        </CardContent>
      </Card>

      {/* Notification Preferences */}
      <Card className="glass-card" data-testid="notification-preferences-card">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Bell className="w-5 h-5" /> Notification Preferences
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Push Notifications Toggle */}
          <PushNotificationToggle />
          
          {loadingPrefs ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-zinc-400" />
            </div>
          ) : notifPrefs ? (
            <>
              {/* Trading Notifications */}
              <div>
                <p className="text-xs text-zinc-500 uppercase tracking-wider mb-3">Trading Notifications</p>
                <div className="space-y-2">
                  {MEMBER_NOTIFICATION_ITEMS.map(item => (
                    <NotifToggle
                      key={item.key}
                      item={item}
                      value={notifPrefs[item.key] ?? true}
                      onChange={() => togglePref(item.key)}
                    />
                  ))}
                </div>
              </div>

              {/* Admin Notifications */}
              {isAdmin && (
                <div>
                  <p className="text-xs text-zinc-500 uppercase tracking-wider mb-3 mt-6">Admin Notifications</p>
                  <div className="space-y-2">
                    {ADMIN_NOTIFICATION_ITEMS.map(item => (
                      <NotifToggle
                        key={item.key}
                        item={item}
                        value={notifPrefs[item.key] ?? true}
                        onChange={() => togglePref(item.key)}
                      />
                    ))}
                  </div>
                </div>
              )}

              <Button
                onClick={handleSaveNotifPrefs}
                className="btn-primary w-full mt-4 gap-2"
                disabled={savingPrefs}
                data-testid="save-notification-prefs-button"
              >
                <Bell className="w-4 h-4" />
                {savingPrefs ? 'Saving...' : 'Save Notification Preferences'}
              </Button>
            </>
          ) : null}
        </CardContent>
      </Card>

      {/* Password Reset */}
      <Card className="glass-card">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Lock className="w-5 h-5" /> Change Password
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label className="text-zinc-300">Current Password</Label>
            <div className="relative mt-1">
              <Input
                type={showCurrentPassword ? 'text' : 'password'}
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                className="input-dark pr-10"
                placeholder="Enter current password"
                data-testid="current-password-input"
              />
              <button type="button" onClick={() => setShowCurrentPassword(!showCurrentPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-white">
                {showCurrentPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>
          <div>
            <Label className="text-zinc-300">New Password</Label>
            <div className="relative mt-1">
              <Input
                type={showNewPassword ? 'text' : 'password'}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="input-dark pr-10"
                placeholder="Enter new password"
                data-testid="new-password-input"
              />
              <button type="button" onClick={() => setShowNewPassword(!showNewPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-white">
                {showNewPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>
          <div>
            <Label className="text-zinc-300">Confirm New Password</Label>
            <Input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} className="input-dark mt-1" placeholder="Confirm new password" data-testid="confirm-password-input" />
          </div>
          <Button onClick={handleChangePassword} className="btn-secondary w-full" disabled={changingPassword} data-testid="change-password-button">
            {changingPassword ? 'Changing...' : 'Change Password'}
          </Button>
        </CardContent>
      </Card>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button onClick={handleSave} className="btn-primary gap-2" disabled={saving} data-testid="save-profile-button">
          <Save className="w-4 h-4" />
          {saving ? 'Saving...' : 'Save Profile Changes'}
        </Button>
      </div>
    </div>
  );
};
