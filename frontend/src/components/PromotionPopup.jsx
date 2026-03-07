import React, { useState, useEffect } from 'react';
import { settingsAPI } from '@/lib/api';
import { Dialog, DialogContent, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { X, Megaphone, Sparkles, Rocket } from 'lucide-react';

const SESSION_KEY = 'promo_popup_dismissed';
const DAY_KEY = 'promo_popup_day_dismissed';

const PRESET_STYLES = {
  announcement: {
    accent: 'from-blue-500 to-indigo-600',
    icon: Megaphone,
    iconBg: 'bg-blue-500/20',
    iconColor: 'text-blue-400',
    btnClass: 'bg-blue-600 hover:bg-blue-700',
  },
  promo: {
    accent: 'from-amber-500 to-orange-600',
    icon: Sparkles,
    iconBg: 'bg-amber-500/20',
    iconColor: 'text-amber-400',
    btnClass: 'bg-amber-600 hover:bg-amber-700',
  },
  feature_update: {
    accent: 'from-emerald-500 to-teal-600',
    icon: Rocket,
    iconBg: 'bg-emerald-500/20',
    iconColor: 'text-emerald-400',
    btnClass: 'bg-emerald-600 hover:bg-emerald-700',
  },
};

export const PromotionPopup = () => {
  const [popup, setPopup] = useState(null);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    settingsAPI.getPromotionPopup()
      .then(res => {
        if (!res.data.enabled) return;
        const freq = res.data.frequency;

        if (freq === 'once_per_session' && sessionStorage.getItem(SESSION_KEY)) return;
        if (freq === 'once_per_day') {
          const last = localStorage.getItem(DAY_KEY);
          if (last === new Date().toISOString().slice(0, 10)) return;
        }

        setPopup(res.data);
        setOpen(true);
        settingsAPI.trackBannerEvent('impression', 'promo_popup').catch(() => {});
      })
      .catch(() => {});
  }, []);

  const handleClose = () => {
    setOpen(false);
    settingsAPI.trackBannerEvent('dismiss', 'promo_popup').catch(() => {});
    if (popup) {
      sessionStorage.setItem(SESSION_KEY, '1');
      if (popup.frequency === 'once_per_day') {
        localStorage.setItem(DAY_KEY, new Date().toISOString().slice(0, 10));
      }
    }
  };

  if (!popup) return null;

  const style = PRESET_STYLES[popup.preset] || PRESET_STYLES.announcement;
  const Icon = style.icon;

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="glass-card border-zinc-700 sm:max-w-md p-0 overflow-hidden" data-testid="promotion-popup">
        <DialogTitle className="sr-only">{popup.title || 'Announcement'}</DialogTitle>
        {/* Accent header bar */}
        <div className={`h-1.5 bg-gradient-to-r ${style.accent}`} />

        <button
          onClick={handleClose}
          className="absolute right-3 top-3 p-1.5 rounded-full bg-zinc-800 hover:bg-zinc-700 text-zinc-400 hover:text-white transition-colors z-10"
          data-testid="promo-popup-close"
        >
          <X className="w-4 h-4" />
        </button>

        <div className="px-6 pt-5 pb-6 space-y-4">
          {/* Icon */}
          <div className={`w-12 h-12 rounded-xl ${style.iconBg} flex items-center justify-center`}>
            <Icon className={`w-6 h-6 ${style.iconColor}`} />
          </div>

          {/* Title */}
          {popup.title && (
            <h3 className="text-lg font-semibold text-white" data-testid="promo-popup-title">{popup.title}</h3>
          )}

          {/* Image */}
          {popup.image_url && (
            <img
              src={popup.image_url}
              alt=""
              className="w-full rounded-lg max-h-48 object-cover"
              data-testid="promo-popup-image"
            />
          )}

          {/* Body */}
          {popup.body && (
            <p className="text-sm text-zinc-300 leading-relaxed" data-testid="promo-popup-body">{popup.body}</p>
          )}

          {/* CTA */}
          {popup.cta_text && popup.cta_url && (
            <Button
              asChild
              className={`w-full ${style.btnClass} text-white`}
              data-testid="promo-popup-cta"
            >
              <a href={popup.cta_url} target="_blank" rel="noopener noreferrer">{popup.cta_text}</a>
            </Button>
          )}

          {/* Dismiss link */}
          <button
            onClick={handleClose}
            className="w-full text-center text-xs text-zinc-500 hover:text-zinc-400 transition-colors pt-1"
            data-testid="promo-popup-dismiss"
          >
            No thanks, dismiss
          </button>
        </div>
      </DialogContent>
    </Dialog>
  );
};
