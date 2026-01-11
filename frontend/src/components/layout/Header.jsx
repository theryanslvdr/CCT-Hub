import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Settings, Menu } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import { authAPI } from '@/lib/api';

const SECRET_CODE = 'SUPER_ADMIN_BYPASS';
const CLICKS_REQUIRED = 10;

export const Header = ({ onMenuClick, title }) => {
  const { user, updateUser, isSuperAdmin } = useAuth();
  const [currentTime, setCurrentTime] = useState(new Date());
  
  // Secret upgrade feature state
  const [clickCount, setClickCount] = useState(0);
  const [showSecretDialog, setShowSecretDialog] = useState(false);
  const [secretCode, setSecretCode] = useState('');
  const [isUpgrading, setIsUpgrading] = useState(false);
  const clickResetTimeout = useRef(null);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Reset click count after 3 seconds of no clicks
  useEffect(() => {
    return () => {
      if (clickResetTimeout.current) {
        clearTimeout(clickResetTimeout.current);
      }
    };
  }, []);

  const formatTime = (date, timezone = 'UTC') => {
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
      timeZone: timezone,
    });
  };

  const handleSettingsClick = () => {
    // If already super_admin or higher, just navigate to settings
    if (user?.role === 'super_admin' || user?.role === 'master_admin') {
      window.location.href = '/admin/settings';
      return;
    }

    // Secret click counter
    const newCount = clickCount + 1;
    setClickCount(newCount);

    // Clear existing timeout
    if (clickResetTimeout.current) {
      clearTimeout(clickResetTimeout.current);
    }

    // Reset after 3 seconds of no clicks
    clickResetTimeout.current = setTimeout(() => {
      setClickCount(0);
    }, 3000);

    // Check if reached required clicks
    if (newCount >= CLICKS_REQUIRED) {
      setShowSecretDialog(true);
      setClickCount(0);
    }
  };

  const handleSecretUpgrade = async () => {
    if (secretCode !== SECRET_CODE) {
      toast.error('Invalid secret code');
      return;
    }

    setIsUpgrading(true);
    try {
      // Call API to upgrade user to super_admin
      const response = await adminAPI.upgradeRole({
        user_id: user.id,
        new_role: 'super_admin',
        secret_code: secretCode
      });
      
      toast.success('Upgraded to Super Admin! Please refresh the page.');
      setShowSecretDialog(false);
      setSecretCode('');
      
      // Update local user state
      if (updateUser) {
        updateUser({ ...user, role: 'super_admin' });
      }
      
      // Reload to apply new permissions
      setTimeout(() => {
        window.location.reload();
      }, 1500);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Upgrade failed');
    } finally {
      setIsUpgrading(false);
    }
  };

  return (
    <>
      <header className="sticky top-0 z-30 h-16 border-b border-zinc-800/50 bg-zinc-950/80 backdrop-blur-xl flex items-center justify-between px-6">
        <div className="flex items-center gap-4">
          <button
            onClick={onMenuClick}
            className="md:hidden p-2 hover:bg-white/5 rounded-lg text-zinc-400 hover:text-white transition-colors"
            data-testid="mobile-menu-toggle"
          >
            <Menu className="w-5 h-5" />
          </button>
          <h1 className="text-xl font-bold text-white">{title || 'Dashboard'}</h1>
        </div>

        <div className="flex items-center gap-6">
          {/* World Timer */}
          <div className="hidden lg:flex items-center gap-4 text-xs font-mono">
            <div className="flex flex-col items-center">
              <span className="text-zinc-500">UTC</span>
              <span className="text-white font-medium">{formatTime(currentTime, 'UTC')}</span>
            </div>
            <div className="w-px h-8 bg-zinc-800" />
            <div className="flex flex-col items-center">
              <span className="text-zinc-500">{user?.timezone || 'Local'}</span>
              <span className="text-blue-400 font-medium">{formatTime(currentTime, user?.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone)}</span>
            </div>
          </div>

          {/* Settings Button with Secret Feature */}
          <div className="flex items-center">
            <Button
              variant="ghost"
              size="icon"
              onClick={handleSettingsClick}
              className="text-zinc-400 hover:text-white hover:bg-white/5 relative"
              data-testid="header-settings-button"
            >
              <Settings className="w-5 h-5" />
              {/* Secret indicator - only show when counting */}
              {clickCount > 0 && clickCount < CLICKS_REQUIRED && (
                <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-purple-500/20 text-purple-400 text-[10px] flex items-center justify-center">
                  {clickCount}
                </span>
              )}
            </Button>
          </div>
        </div>
      </header>

      {/* Secret Upgrade Dialog */}
      <Dialog open={showSecretDialog} onOpenChange={setShowSecretDialog}>
        <DialogContent className="glass-card border-zinc-800 max-w-sm">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              🔐 Secret Access
            </DialogTitle>
            <DialogDescription className="text-zinc-400">
              Enter the secret code to unlock Super Admin privileges.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div className="space-y-2">
              <Label htmlFor="secret-code" className="text-zinc-400">Secret Code</Label>
              <Input
                id="secret-code"
                type="password"
                value={secretCode}
                onChange={(e) => setSecretCode(e.target.value)}
                placeholder="Enter secret code..."
                className="input-dark"
                onKeyDown={(e) => e.key === 'Enter' && handleSecretUpgrade()}
                data-testid="secret-code-input"
              />
            </div>
            <div className="flex gap-3">
              <Button
                onClick={handleSecretUpgrade}
                disabled={isUpgrading || !secretCode}
                className="btn-primary flex-1"
                data-testid="secret-upgrade-btn"
              >
                {isUpgrading ? 'Upgrading...' : 'Unlock'}
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  setShowSecretDialog(false);
                  setSecretCode('');
                }}
                className="btn-secondary"
              >
                Cancel
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};
