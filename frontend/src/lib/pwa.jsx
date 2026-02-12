import { useState, useEffect } from 'react';
import { X, Download, Monitor, Smartphone, Apple, Chrome } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';

let deferredPrompt = null;

// Detect user's platform
const getPlatform = () => {
  const ua = navigator.userAgent || '';
  const isIOS = /iPad|iPhone|iPod/.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  const isAndroid = /Android/.test(ua);
  const isMac = /Macintosh|Mac OS X/.test(ua) && !isIOS;
  const isWindows = /Windows/.test(ua);
  const isSafari = /Safari/.test(ua) && !/Chrome/.test(ua);
  const isChrome = /Chrome/.test(ua) && !/Edg/.test(ua);
  const isEdge = /Edg/.test(ua);

  if (isIOS) return 'ios';
  if (isAndroid) return 'android';
  if (isMac) return 'mac';
  if (isWindows) return 'windows';
  return 'desktop';
};

const INSTALL_INSTRUCTIONS = {
  windows: {
    title: 'Install on Windows PC',
    icon: Monitor,
    browsers: [
      {
        name: 'Chrome',
        steps: [
          'Look for the install icon in the address bar (right side)',
          'Click it and select "Install"',
          'Or click the three-dot menu (...) > "Save and share" > "Install page as app"',
          'The app will open in its own window'
        ]
      },
      {
        name: 'Edge',
        steps: [
          'Click the three-dot menu (...) in the top-right',
          'Select "Apps" > "Install this site as an app"',
          'Click "Install" in the popup',
          'The app will be added to your Start Menu'
        ]
      }
    ]
  },
  mac: {
    title: 'Install on Mac',
    icon: Apple,
    browsers: [
      {
        name: 'Chrome',
        steps: [
          'Look for the install icon in the address bar (right side)',
          'Click it and select "Install"',
          'Or click the three-dot menu (...) > "Save and share" > "Install page as app"',
          'The app will appear in your Applications folder'
        ]
      },
      {
        name: 'Safari (macOS Sonoma+)',
        steps: [
          'Click "File" in the menu bar',
          'Select "Add to Dock"',
          'The app will appear in your Dock'
        ]
      }
    ]
  },
  android: {
    title: 'Install on Android',
    icon: Smartphone,
    browsers: [
      {
        name: 'Chrome',
        steps: [
          'Tap the three-dot menu at the top-right',
          'Select "Add to Home screen" or "Install app"',
          'Tap "Install" in the popup',
          'The app icon will appear on your home screen'
        ]
      }
    ]
  },
  ios: {
    title: 'Install on iPhone / iPad',
    icon: Smartphone,
    browsers: [
      {
        name: 'Safari (Required)',
        steps: [
          'Open this site in Safari (not Chrome or other browsers)',
          'Tap the Share button at the bottom of the screen',
          'Scroll down and tap "Add to Home Screen"',
          'Tap "Add" in the top-right corner',
          'The app icon will appear on your home screen'
        ],
        note: 'iOS only supports PWA installation through Safari. If you are using Chrome or another browser, please copy the URL and open it in Safari first.'
      }
    ]
  },
  desktop: {
    title: 'Install on Desktop',
    icon: Monitor,
    browsers: [
      {
        name: 'Chrome / Edge',
        steps: [
          'Look for the install icon in the address bar',
          'Or open the browser menu and look for "Install" option',
          'Click "Install" to add the app to your system'
        ]
      }
    ]
  }
};

export const usePWAInstall = () => {
  const [canInstall, setCanInstall] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    const handler = (e) => {
      e.preventDefault();
      deferredPrompt = e;
      if (!sessionStorage.getItem('pwa-dismissed')) {
        setCanInstall(true);
      }
    };
    window.addEventListener('beforeinstallprompt', handler);

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

export const PWAInstallInstructions = ({ open, onOpenChange }) => {
  const [platform, setPlatform] = useState('desktop');
  const { install } = usePWAInstall();

  useEffect(() => {
    setPlatform(getPlatform());
  }, []);

  const instructions = INSTALL_INSTRUCTIONS[platform];
  const allPlatforms = Object.entries(INSTALL_INSTRUCTIONS);
  const IconComponent = instructions.icon;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="glass-card border-zinc-800 max-w-lg max-h-[85vh] overflow-y-auto" data-testid="pwa-instructions-dialog">
        <DialogHeader>
          <DialogTitle className="text-white flex items-center gap-2">
            <Download className="w-5 h-5 text-blue-400" /> Install The CrossCurrent Hub
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 mt-2">
          {/* Quick install button if browser supports it */}
          {deferredPrompt && (
            <Button
              onClick={async () => { await install(); onOpenChange(false); }}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white"
              data-testid="pwa-quick-install-btn"
            >
              <Download className="w-4 h-4 mr-2" /> Install Now (One Click)
            </Button>
          )}

          {/* Auto-detected platform */}
          <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/30">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-xl bg-blue-500/20 flex items-center justify-center">
                <IconComponent className="w-5 h-5 text-blue-400" />
              </div>
              <div>
                <p className="text-sm font-semibold text-white">{instructions.title}</p>
                <p className="text-xs text-zinc-400">Detected your device automatically</p>
              </div>
            </div>

            {instructions.browsers.map((browser, idx) => (
              <div key={idx} className="mt-3">
                <p className="text-xs font-semibold text-zinc-300 mb-2 flex items-center gap-1.5">
                  <Chrome className="w-3.5 h-3.5" /> {browser.name}
                </p>
                <ol className="space-y-1.5 ml-1">
                  {browser.steps.map((step, i) => (
                    <li key={i} className="flex gap-2 text-xs text-zinc-400">
                      <span className="text-blue-400 font-bold min-w-[16px]">{i + 1}.</span>
                      <span>{step}</span>
                    </li>
                  ))}
                </ol>
                {browser.note && (
                  <div className="mt-2 p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/20">
                    <p className="text-xs text-amber-300">{browser.note}</p>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Other platforms */}
          <div>
            <p className="text-xs text-zinc-500 mb-2">Other devices:</p>
            <div className="grid grid-cols-2 gap-2">
              {allPlatforms
                .filter(([key]) => key !== platform)
                .map(([key, info]) => {
                  const PlatformIcon = info.icon;
                  return (
                    <button
                      key={key}
                      onClick={() => setPlatform(key)}
                      className="p-3 rounded-lg bg-zinc-800/60 border border-zinc-700/50 text-left hover:border-zinc-600 transition-colors"
                      data-testid={`pwa-platform-${key}`}
                    >
                      <PlatformIcon className="w-4 h-4 text-zinc-400 mb-1" />
                      <p className="text-xs text-zinc-300">{info.title}</p>
                    </button>
                  );
                })}
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export const PWAInstallBanner = () => {
  const { canInstall, install, dismiss } = usePWAInstall();
  const [showInstructions, setShowInstructions] = useState(false);

  // On iOS/Safari, never show the native install prompt but allow instructions
  const platform = getPlatform();
  const showBanner = canInstall || platform === 'ios';

  if (!showBanner && !showInstructions) return null;

  // If already installed, don't show anything
  if (window.matchMedia('(display-mode: standalone)').matches) return null;

  // Check if dismissed
  if (sessionStorage.getItem('pwa-dismissed')) return null;

  return (
    <>
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
            onClick={() => {
              if (canInstall) {
                install();
              } else {
                setShowInstructions(true);
              }
            }}
            className="bg-blue-600 hover:bg-blue-700 text-white text-xs h-8 px-3 flex-shrink-0"
            data-testid="pwa-install-button"
          >
            Install
          </Button>
          <button
            onClick={() => {
              dismiss();
              sessionStorage.setItem('pwa-dismissed', '1');
            }}
            className="text-zinc-500 hover:text-zinc-300 flex-shrink-0"
            data-testid="pwa-install-dismiss"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>
      <PWAInstallInstructions open={showInstructions} onOpenChange={setShowInstructions} />
    </>
  );
};
