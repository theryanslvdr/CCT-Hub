import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { settingsAPI } from '@/lib/api';
import { Sparkles } from 'lucide-react';

export const Footer = () => {
  const [settings, setSettings] = useState(null);

  useEffect(() => {
    const loadSettings = async () => {
      try {
        const res = await settingsAPI.getPlatform();
        setSettings(res.data);
      } catch (error) {
        console.error('Failed to load settings');
      }
    };
    loadSettings();
  }, []);

  return (
    <footer className="mt-auto py-4 px-6 border-t border-zinc-800 bg-zinc-950/50" data-testid="app-footer">
      <div className="flex flex-wrap items-center justify-between gap-4 text-sm">
        {/* Copyright */}
        <span className="text-zinc-500">
          {settings?.footer_copyright || '© 2024 CrossCurrent Finance Center. All rights reserved.'}
        </span>
        
        {/* Footer Links */}
        <div className="flex items-center gap-4">
          {(settings?.footer_links || []).map((link, index) => (
            link.url.startsWith('http') ? (
              <a
                key={index}
                href={link.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-zinc-400 hover:text-white transition-colors"
              >
                {link.label}
              </a>
            ) : (
              <Link
                key={index}
                to={link.url}
                className="text-zinc-400 hover:text-white transition-colors"
              >
                {link.label}
              </Link>
            )
          ))}
          
          {/* Emergent Badge - only show if not hidden */}
          {!settings?.hide_emergent_badge && (
            <a
              href="https://emergentagent.com"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-400 hover:bg-purple-500/20 transition-colors text-xs"
            >
              <Sparkles className="w-3 h-3" />
              Made with Emergent
            </a>
          )}
        </div>
      </div>
    </footer>
  );
};

export default Footer;
