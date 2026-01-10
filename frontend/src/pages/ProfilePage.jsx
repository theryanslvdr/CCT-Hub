import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { userAPI } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import { User, Globe, Calculator, Save } from 'lucide-react';

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

export const ProfilePage = () => {
  const { user, updateUser } = useAuth();
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [timezone, setTimezone] = useState(user?.timezone || 'Asia/Manila');
  const [lotSize, setLotSize] = useState(user?.lot_size || 0.01);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (user) {
      setFullName(user.full_name || '');
      setTimezone(user.timezone || 'Asia/Manila');
      setLotSize(user.lot_size || 0.01);
    }
  }, [user]);

  const handleSave = async () => {
    setSaving(true);
    try {
      const response = await userAPI.updateProfile({
        full_name: fullName,
        timezone: timezone,
        lot_size: parseFloat(lotSize),
      });
      
      // Update local user state
      updateUser(response.data);
      toast.success('Profile updated successfully!');
    } catch (error) {
      toast.error('Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  const currentTime = new Date().toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
    timeZone: timezone,
  });

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <Card className="glass-card">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <User className="w-5 h-5" /> Profile Settings
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Full Name */}
          <div>
            <Label className="text-zinc-300">Full Name</Label>
            <Input
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="input-dark mt-1"
              data-testid="profile-name-input"
            />
          </div>

          {/* Email (read-only) */}
          <div>
            <Label className="text-zinc-300">Email</Label>
            <Input
              value={user?.email || ''}
              disabled
              className="input-dark mt-1 opacity-50 cursor-not-allowed"
            />
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
                  <SelectItem key={tz.value} value={tz.value}>
                    {tz.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-xs text-zinc-500 mt-1">
              This timezone will be used in the Trade Monitor
            </p>
          </div>

          {/* Preview */}
          <div className="p-4 rounded-lg bg-zinc-900/50 border border-zinc-800">
            <p className="text-xs text-zinc-500 mb-2">Current time in your timezone:</p>
            <p className="text-3xl font-mono font-bold text-white">{currentTime}</p>
          </div>
        </CardContent>
      </Card>

      {/* Trading Settings */}
      <Card className="glass-card">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Calculator className="w-5 h-5" /> Trading Settings
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div>
            <Label className="text-zinc-300">Default LOT Size</Label>
            <Input
              type="number"
              step="0.01"
              value={lotSize}
              onChange={(e) => setLotSize(e.target.value)}
              className="input-dark mt-1"
              data-testid="lot-size-input"
            />
            <p className="text-xs text-zinc-500 mt-1">
              This will be your default LOT size in the Trade Monitor
            </p>
          </div>

          {/* Preview */}
          <div className="p-4 rounded-lg bg-gradient-to-br from-blue-500/10 to-cyan-500/10 border border-blue-500/20">
            <p className="text-xs text-zinc-500 mb-2">Projected Exit Value (LOT × 15):</p>
            <p className="text-3xl font-mono font-bold text-gradient">
              ${(parseFloat(lotSize) * 15).toFixed(2)}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button
          onClick={handleSave}
          className="btn-primary gap-2"
          disabled={saving}
          data-testid="save-profile-button"
        >
          <Save className="w-4 h-4" />
          {saving ? 'Saving...' : 'Save Changes'}
        </Button>
      </div>
    </div>
  );
};
