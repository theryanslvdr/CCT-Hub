import React, { useState, useEffect, useRef } from 'react';
import { versionAPI } from '@/lib/api';
import { RefreshCw } from 'lucide-react';

const CHECK_INTERVAL = 60000; // Check every 60 seconds
const STORAGE_KEY = 'app_build_version';

export const VersionBanner = () => {
  const [showBanner, setShowBanner] = useState(false);
  const cachedVersion = useRef(null);

  useEffect(() => {
    const fetchVersion = async () => {
      try {
        const res = await versionAPI.getVersion();
        const serverVersion = res.data.build_version;

        if (!cachedVersion.current) {
          // First load — store the version
          cachedVersion.current = serverVersion;
          localStorage.setItem(STORAGE_KEY, serverVersion);
          return;
        }

        // Compare with cached version
        if (serverVersion !== cachedVersion.current) {
          setShowBanner(true);
        }
      } catch {
        // Silently fail — don't interrupt user
      }
    };

    // Also check against localStorage (persists across tab refreshes within same deploy)
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) cachedVersion.current = stored;

    fetchVersion();
    const interval = setInterval(fetchVersion, CHECK_INTERVAL);
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = () => {
    localStorage.removeItem(STORAGE_KEY);
    window.location.reload(true);
  };

  if (!showBanner) return null;

  return (
    <div
      data-testid="version-update-banner"
      className="fixed top-0 left-0 right-0 z-[9999] bg-gradient-to-r from-orange-600 to-indigo-600 text-white px-4 py-3 flex items-center justify-center gap-3 shadow-lg"
    >
      <RefreshCw className="w-4 h-4 animate-spin" />
      <span className="text-sm font-medium">A new version has been deployed.</span>
      <button
        data-testid="version-refresh-btn"
        onClick={handleRefresh}
        className="px-3 py-1 text-xs font-bold bg-white text-orange-700 rounded-full hover:bg-orange-50 transition-colors"
      >
        Refresh Now
      </button>
    </div>
  );
};
