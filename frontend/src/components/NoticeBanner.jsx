import React, { useState, useEffect } from 'react';
import { settingsAPI } from '@/lib/api';
import { useLocation } from 'react-router-dom';
import { X, ExternalLink } from 'lucide-react';

const DISMISS_KEY = 'notice_banner_dismissed';

const routeToPageKey = {
  '/dashboard': 'dashboard',
  '/profit-tracker': 'profit_tracker',
  '/trade-monitor': 'trade_monitor',
  '/goals': 'goals',
  '/debt': 'debt',
  '/profile': 'profile',
  '/notifications': 'notifications',
  '/habits': 'habits',
};

export const NoticeBanner = () => {
  const [banner, setBanner] = useState(null);
  const [dismissed, setDismissed] = useState(false);
  const location = useLocation();
  const tracked = React.useRef(false);

  useEffect(() => {
    if (sessionStorage.getItem(DISMISS_KEY)) {
      setDismissed(true);
      return;
    }
    settingsAPI.getNoticeBanner()
      .then(res => {
        if (res.data.enabled) setBanner(res.data);
      })
      .catch(() => {});
  }, []);

  // Track impression once per session
  useEffect(() => {
    if (banner && !tracked.current) {
      tracked.current = true;
      settingsAPI.trackBannerEvent('impression', 'notice_banner').catch(() => {});
    }
  }, [banner]);

  const handleDismiss = () => {
    setDismissed(true);
    sessionStorage.setItem(DISMISS_KEY, '1');
    settingsAPI.trackBannerEvent('dismiss', 'notice_banner').catch(() => {});
  };

  if (!banner || dismissed) return null;

  // Check if current page is in the configured pages list
  const currentPage = routeToPageKey[location.pathname];
  if (banner.pages?.length && !banner.pages.includes(currentPage)) return null;

  return (
    <div
      data-testid="notice-banner"
      className="w-full px-4 py-2.5 flex items-center justify-center gap-3 text-sm relative"
      style={{ backgroundColor: banner.bg_color, color: banner.text_color }}
    >
      <span className="font-medium text-center">{banner.text}</span>
      {banner.link_text && banner.link_url && (
        <a
          href={banner.link_url}
          target="_blank"
          rel="noopener noreferrer"
          className="underline underline-offset-2 font-semibold flex items-center gap-1 hover:opacity-80"
          style={{ color: banner.text_color }}
          data-testid="notice-banner-link"
        >
          {banner.link_text} <ExternalLink className="w-3 h-3" />
        </a>
      )}
      <button
        onClick={handleDismiss}
        className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded hover:opacity-70 transition-opacity"
        data-testid="notice-banner-dismiss"
        aria-label="Dismiss"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
};
