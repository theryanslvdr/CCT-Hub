import React, { useState, useEffect } from 'react';
import { settingsAPI } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { toast } from 'sonner';
import { Settings, Upload, Globe, Image, Palette, RefreshCw } from 'lucide-react';

export const AdminSettingsPage = () => {
  const [settings, setSettings] = useState({
    site_title: 'CrossCurrent Finance Center',
    site_description: 'Trading profit management platform',
    favicon_url: '',
    logo_url: '',
    og_image_url: '',
    primary_color: '#3B82F6',
    accent_color: '#06B6D4',
    hide_emergent_badge: false,
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  // Apply settings to document
  useEffect(() => {
    // Update favicon
    if (settings.favicon_url) {
      const favicon = document.querySelector("link[rel~='icon']") || document.createElement('link');
      favicon.rel = 'icon';
      favicon.href = settings.favicon_url;
      document.head.appendChild(favicon);
    }
    
    // Update title
    if (settings.site_title) {
      document.title = settings.site_title;
    }
  }, [settings.favicon_url, settings.site_title]);

  const loadSettings = async () => {
    try {
      const res = await settingsAPI.getPlatform();
      setSettings(prev => ({ ...prev, ...res.data }));
    } catch (error) {
      console.error('Failed to load settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await settingsAPI.updatePlatform(settings);
      toast.success('Settings saved! Refreshing page...');
      
      // Auto-refresh after 1.5 seconds
      setTimeout(() => {
        window.location.reload();
      }, 1500);
    } catch (error) {
      toast.error('Failed to save settings');
      setSaving(false);
    }
  };

  const handleLogoUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      const res = await settingsAPI.uploadLogo(file);
      setSettings(prev => ({ ...prev, logo_url: res.data.url }));
      toast.success('Logo uploaded!');
    } catch (error) {
      toast.error('Failed to upload logo');
    }
  };

  const handleFaviconUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      const res = await settingsAPI.uploadFavicon(file);
      setSettings(prev => ({ ...prev, favicon_url: res.data.url }));
      toast.success('Favicon uploaded!');
    } catch (error) {
      toast.error('Failed to upload favicon');
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="w-8 h-8 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" /></div>;
  }

  return (
    <div className="space-y-6">
      {/* SEO Settings */}
      <Card className="glass-card">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Globe className="w-5 h-5" /> SEO & Meta Settings
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label className="text-zinc-300">Site Title (Browser Tab)</Label>
            <Input
              value={settings.site_title}
              onChange={(e) => setSettings({ ...settings, site_title: e.target.value })}
              className="input-dark mt-1"
              placeholder="CrossCurrent Finance Center"
              data-testid="site-title-input"
            />
            <p className="text-xs text-zinc-500 mt-1">This appears in the browser tab</p>
          </div>
          <div>
            <Label className="text-zinc-300">Site Description</Label>
            <Input
              value={settings.site_description}
              onChange={(e) => setSettings({ ...settings, site_description: e.target.value })}
              className="input-dark mt-1"
              data-testid="site-description-input"
            />
          </div>
          <div>
            <Label className="text-zinc-300">OG Image URL (for social sharing)</Label>
            <Input
              value={settings.og_image_url}
              onChange={(e) => setSettings({ ...settings, og_image_url: e.target.value })}
              placeholder="https://example.com/og-image.png"
              className="input-dark mt-1"
            />
          </div>
        </CardContent>
      </Card>

      {/* Branding */}
      <Card className="glass-card">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Image className="w-5 h-5" /> Branding
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Logo */}
          <div>
            <Label className="text-zinc-300">Logo (replaces "CrossCurrent" text in sidebar)</Label>
            <div className="mt-2 flex items-center gap-4">
              {settings.logo_url ? (
                <div className="w-32 h-16 rounded-lg bg-zinc-900 flex items-center justify-center overflow-hidden">
                  <img src={settings.logo_url} alt="Logo" className="max-w-full max-h-full object-contain" />
                </div>
              ) : (
                <div className="w-32 h-16 rounded-lg bg-zinc-900 flex items-center justify-center border-2 border-dashed border-zinc-700">
                  <span className="text-zinc-500 text-sm">No logo</span>
                </div>
              )}
              <div>
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleLogoUpload}
                  className="hidden"
                  id="logo-upload"
                />
                <label htmlFor="logo-upload">
                  <Button asChild variant="outline" className="btn-secondary cursor-pointer">
                    <span>
                      <Upload className="w-4 h-4 mr-2" /> Upload Logo
                    </span>
                  </Button>
                </label>
              </div>
            </div>
          </div>

          {/* Favicon */}
          <div>
            <Label className="text-zinc-300">Favicon (browser tab icon)</Label>
            <div className="mt-2 flex items-center gap-4">
              {settings.favicon_url ? (
                <div className="w-12 h-12 rounded-lg bg-zinc-900 flex items-center justify-center overflow-hidden">
                  <img src={settings.favicon_url} alt="Favicon" className="w-8 h-8 object-contain" />
                </div>
              ) : (
                <div className="w-12 h-12 rounded-lg bg-zinc-900 flex items-center justify-center border-2 border-dashed border-zinc-700">
                  <span className="text-zinc-500 text-xs">None</span>
                </div>
              )}
              <div>
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleFaviconUpload}
                  className="hidden"
                  id="favicon-upload"
                />
                <label htmlFor="favicon-upload">
                  <Button asChild variant="outline" className="btn-secondary cursor-pointer">
                    <span>
                      <Upload className="w-4 h-4 mr-2" /> Upload Favicon
                    </span>
                  </Button>
                </label>
              </div>
            </div>
          </div>

          {/* Hide Emergent Badge Toggle */}
          <div className="flex items-center justify-between p-4 rounded-lg bg-zinc-900/50 border border-zinc-800">
            <div>
              <Label className="text-zinc-300">Hide "Made with Emergent" Badge</Label>
              <p className="text-xs text-zinc-500 mt-1">Toggle to show/hide the Emergent branding badge</p>
            </div>
            <Switch
              checked={settings.hide_emergent_badge}
              onCheckedChange={(v) => setSettings({ ...settings, hide_emergent_badge: v })}
              data-testid="hide-badge-toggle"
            />
          </div>
        </CardContent>
      </Card>

      {/* Colors */}
      <Card className="glass-card">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Palette className="w-5 h-5" /> UI Customization
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label className="text-zinc-300">Primary Color</Label>
              <div className="flex items-center gap-3 mt-1">
                <input
                  type="color"
                  value={settings.primary_color}
                  onChange={(e) => setSettings({ ...settings, primary_color: e.target.value })}
                  className="w-12 h-10 rounded cursor-pointer bg-transparent"
                />
                <Input
                  value={settings.primary_color}
                  onChange={(e) => setSettings({ ...settings, primary_color: e.target.value })}
                  className="input-dark flex-1"
                  data-testid="primary-color-input"
                />
              </div>
            </div>
            <div>
              <Label className="text-zinc-300">Accent Color</Label>
              <div className="flex items-center gap-3 mt-1">
                <input
                  type="color"
                  value={settings.accent_color}
                  onChange={(e) => setSettings({ ...settings, accent_color: e.target.value })}
                  className="w-12 h-10 rounded cursor-pointer bg-transparent"
                />
                <Input
                  value={settings.accent_color}
                  onChange={(e) => setSettings({ ...settings, accent_color: e.target.value })}
                  className="input-dark flex-1"
                  data-testid="accent-color-input"
                />
              </div>
            </div>
          </div>

          {/* Preview */}
          <div className="p-4 rounded-lg bg-zinc-900/50 border border-zinc-800">
            <p className="text-xs text-zinc-500 mb-3">Preview:</p>
            <div className="flex gap-4">
              <Button style={{ backgroundColor: settings.primary_color }} className="text-white">
                Primary Button
              </Button>
              <Button style={{ backgroundColor: settings.accent_color }} className="text-white">
                Accent Button
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button onClick={handleSave} className="btn-primary gap-2" disabled={saving} data-testid="save-settings-button">
          {saving ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" /> Saving & Refreshing...
            </>
          ) : (
            <>Save Settings</>
          )}
        </Button>
      </div>
    </div>
  );
};
