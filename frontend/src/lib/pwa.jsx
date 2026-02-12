import { useState, useEffect } from 'react';
import { X, Download } from 'lucide-react';
import { Button } from '../components/ui/button';

let deferredPrompt = null;

export const usePWAInstall = () => {
  const [canInstall, setCanInstall] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    const handler = (e) => {
      e.preventDefault();
      deferredPrompt = e;
      // Don't show if user already dismissed this session
      if (!sessionStorage.getItem('pwa-dismissed')) {
        setCanInstall(true);
      }
    };
    window.addEventListener('beforeinstallprompt', handler);

    // Check if already installed
    if (window.matchMedia('(display-mode: standalone)').matches) {
      setCanInstall(false);
    }

    return () => window.removeEventListener('beforeinstallprompt', handler);
  }, []);

  const install = async () => {
    if (!deferredPrompt) return false;
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    deferredPrompt = null;
    setCanInstall(false);
    return outcome === 'accepted';
  };

  const dismiss = () => {
    setDismissed(true);
    setCanInstall(false);
    sessionStorage.setItem('pwa-dismissed', '1');
  };

  return { canInstall: canInstall && !dismissed, install, dismiss };
};

export const PWAInstallBanner = () => {
  const { canInstall, install, dismiss } = usePWAInstall();

  if (!canInstall) return null;

  return (
    <div
      className="fixed bottom-4 left-4 right-4 md:left-auto md:right-4 md:w-[380px] z-50 animate-in slide-in-from-bottom-4 duration-300"
      data-testid="pwa-install-banner"
    >
      <div className="glass-card border border-blue-500/30 rounded-xl p-4 flex items-center gap-3 shadow-lg shadow-blue-500/10">
        <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center flex-shrink-0">
          <Download className="w-5 h-5 text-blue-400" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-white">Install CrossCurrent Hub</p>
          <p className="text-xs text-zinc-400 truncate">Quick access from your home screen</p>
        </div>
        <Button
          size="sm"
          onClick={install}
          className="bg-blue-600 hover:bg-blue-700 text-white text-xs h-8 px-3 flex-shrink-0"
          data-testid="pwa-install-button"
        >
          Install
        </Button>
        <button
          onClick={dismiss}
          className="text-zinc-500 hover:text-zinc-300 flex-shrink-0"
          data-testid="pwa-install-dismiss"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
