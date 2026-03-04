import React, { useState, useEffect } from 'react';
import { settingsAPI, adminAPI, rewardsAPI, publitioAPI } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Calendar } from '@/components/ui/calendar';
import { toast } from 'sonner';
import { 
  Settings, Upload, Globe, Image, Palette, RefreshCw, Crown, 
  Plug, Eye, EyeOff, Mail, Cloud, Heart, Key, CheckCircle2,
  FileText, Zap, XCircle, Loader2, Code, Eye as EyePreview, ExternalLink, Link,
  LogIn, Plus, Trash2, GripVertical, Copyright, Wrench, Megaphone, AlertTriangle, Send,
  TreePine, Calendar as CalendarIcon, TrendingUp, Shield, Database, Smartphone, ImageIcon
} from 'lucide-react';
import { CustomEmailTemplates } from '@/components/admin/CustomEmailTemplates';
import { HabitManagerCard } from './settings/HabitManagerCard';
import { AffiliateManagerCard } from './settings/AffiliateManagerCard';
import { BannerAnalyticsCard } from './settings/BannerAnalyticsCard';
import { EmailsTab } from './settings/EmailsTab';
import { TradingTab } from './settings/TradingTab';
import { DiagnosticsTab } from './settings/DiagnosticsTab';

export const AdminSettingsPage = () => {
  const { user, isMasterAdmin, isSuperAdmin } = useAuth();
  const [settings, setSettings] = useState({
    platform_name: 'CrossCurrent',
    tagline: 'Finance Center',
    site_title: 'CrossCurrent Finance Center',
    site_description: 'Trading profit management platform',
    favicon_url: '',
    logo_url: '',
    pwa_icon_url: '',
    og_image_url: '',
    primary_color: '#3B82F6',
    accent_color: '#06B6D4',
    hide_emergent_badge: false,
    // Login Customization
    login_title: '',
    login_tagline: '',
    login_notice: 'Only CrossCurrent community members can access this platform.',
    // Production URL
    production_site_url: '',
    // Integration API Keys
    emailit_api_key: '',
    cloudinary_cloud_name: '',
    cloudinary_api_key: '',
    cloudinary_api_secret: '',
    heartbeat_api_key: '',
    publitio_api_key: '',
    publitio_api_secret: '',
    // Custom Links
    custom_registration_link: '',
    // Footer
    footer_copyright: '© 2024 CrossCurrent Finance Center. All rights reserved.',
    footer_links: [],
    // Maintenance
    maintenance_mode: false,
    maintenance_message: 'Our services are undergoing maintenance, and will be back soon!',
    // Announcements
    announcements: [],
    // Content Protection (Security)
    content_protection_enabled: false,
    content_protection_watermark: true,
    content_protection_watermark_custom: '',
    content_protection_disable_copy: true,
    content_protection_disable_rightclick: true,
    content_protection_disable_shortcuts: true,
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('seo');
  
  // Footer links management
  const [newFooterLink, setNewFooterLink] = useState({ label: '', url: '' });
  // Integration test states
  const [testingEmailit, setTestingEmailit] = useState(false);
  const [testingCloudinary, setTestingCloudinary] = useState(false);
  const [testingHeartbeat, setTestingHeartbeat] = useState(false);
  const [testingPublitio, setTestingPublitio] = useState(false);
  const [testResults, setTestResults] = useState({});
  
  // Visibility toggles for sensitive fields
  const [showKeys, setShowKeys] = useState({
    emailit: false,
    cloudinary_key: false,
    cloudinary_secret: false,
    heartbeat: false,
    publitio_key: false,
    publitio_secret: false
  });

  useEffect(() => {
    loadSettings();
  }, [isMasterAdmin]);

  // Apply settings to document
  useEffect(() => {
    if (settings.favicon_url) {
      const favicon = document.querySelector("link[rel~='icon']") || document.createElement('link');
      favicon.rel = 'icon';
      favicon.href = settings.favicon_url;
      document.head.appendChild(favicon);
    }
    
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

  const handleTestEmailit = async () => {
    setTestingEmailit(true);
    try {
      const res = await settingsAPI.testEmailit();
      setTestResults(prev => ({ ...prev, emailit: res.data }));
      if (res.data.success) {
        toast.success('Emailit connection successful!');
      } else {
        toast.error(res.data.message || 'Connection failed');
      }
    } catch (error) {
      setTestResults(prev => ({ ...prev, emailit: { success: false, message: 'Connection failed' } }));
      toast.error('Failed to test connection');
    } finally {
      setTestingEmailit(false);
    }
  };

  const handleTestCloudinary = async () => {
    setTestingCloudinary(true);
    try {
      const res = await settingsAPI.testCloudinary();
      setTestResults(prev => ({ ...prev, cloudinary: res.data }));
      if (res.data.success) {
        toast.success('Cloudinary connection successful!');
      } else {
        toast.error(res.data.message || 'Connection failed');
      }
    } catch (error) {
      setTestResults(prev => ({ ...prev, cloudinary: { success: false, message: 'Connection failed' } }));
      toast.error('Failed to test connection');
    } finally {
      setTestingCloudinary(false);
    }
  };

  const handleTestHeartbeat = async () => {
    setTestingHeartbeat(true);
    try {
      const res = await settingsAPI.testHeartbeat();
      setTestResults(prev => ({ ...prev, heartbeat: res.data }));
      if (res.data.success) {
        toast.success('Heartbeat connection successful!');
      } else {
        toast.error(res.data.message || 'Connection failed');
      }
    } catch (error) {
      setTestResults(prev => ({ ...prev, heartbeat: { success: false, message: 'Connection failed' } }));
      toast.error('Failed to test connection');
    } finally {
      setTestingHeartbeat(false);
    }
  };

  const handleTestPublitio = async () => {
    setTestingPublitio(true);
    try {
      const res = await publitioAPI.testConnection();
      setTestResults(prev => ({ ...prev, publitio: res.data }));
      if (res.data.success) {
        toast.success('Publitio connection successful!');
      } else {
        toast.error(res.data.message || 'Connection failed');
      }
    } catch (error) {
      setTestResults(prev => ({ ...prev, publitio: { success: false, message: 'Connection failed' } }));
      toast.error('Failed to test connection');
    } finally {
      setTestingPublitio(false);
    }
  };

  // Footer link handlers
  const handleAddFooterLink = () => {
    if (!newFooterLink.label.trim() || !newFooterLink.url.trim()) {
      toast.error('Please enter both label and URL');
      return;
    }
    const currentLinks = settings.footer_links || [];
    setSettings({
      ...settings,
      footer_links: [...currentLinks, { ...newFooterLink, id: Date.now().toString() }]
    });
    setNewFooterLink({ label: '', url: '' });
  };

  const handleRemoveFooterLink = (index) => {
    const currentLinks = settings.footer_links || [];
    setSettings({
      ...settings,
      footer_links: currentLinks.filter((_, i) => i !== index)
    });
  };

  // Announcement handlers
  const [newAnnouncement, setNewAnnouncement] = useState({
    title: '',
    message: '',
    link_url: '',
    link_text: '',
    type: 'info', // info, warning, success
    sticky: false,
    active: true
  });

  const handleAddAnnouncement = () => {
    if (!newAnnouncement.message.trim()) {
      toast.error('Please enter announcement message');
      return;
    }
    const currentAnnouncements = settings.announcements || [];
    setSettings({
      ...settings,
      announcements: [...currentAnnouncements, { 
        ...newAnnouncement, 
        id: Date.now().toString(),
        created_at: new Date().toISOString()
      }]
    });
    setNewAnnouncement({
      title: '',
      message: '',
      link_url: '',
      link_text: '',
      type: 'info',
      sticky: false,
      active: true
    });
    toast.success('Announcement added! Remember to save settings.');
  };

  const handleRemoveAnnouncement = (index) => {
    const currentAnnouncements = settings.announcements || [];
    setSettings({
      ...settings,
      announcements: currentAnnouncements.filter((_, i) => i !== index)
    });
  };

  const handleToggleAnnouncement = (index) => {
    const currentAnnouncements = [...(settings.announcements || [])];
    currentAnnouncements[index].active = !currentAnnouncements[index].active;
    setSettings({ ...settings, announcements: currentAnnouncements });
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await settingsAPI.updatePlatform(settings);
      toast.success('Settings saved! Refreshing page...');
      
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

  const handlePwaIconUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      const res = await settingsAPI.uploadPwaIcon(file);
      setSettings(prev => ({ ...prev, pwa_icon_url: res.data.url }));
      toast.success('PWA icon uploaded! Users will see the new icon after reinstalling.');
    } catch (error) {
      const detail = error.response?.data?.detail;
      toast.error(`Upload failed: ${typeof detail === 'string' ? detail : 'Try using the URL method instead'}`);
    }
  };

  const handlePwaIconUrl = async () => {
    const url = settings.pwa_icon_url_input || '';
    if (!url.startsWith('http')) {
      toast.error('Please enter a valid URL starting with http');
      return;
    }
    try {
      await settingsAPI.setPwaIconUrl(url);
      setSettings(prev => ({ ...prev, pwa_icon_url: url, pwa_icon_url_input: '' }));
      toast.success('PWA icon URL saved! Users will see the new icon after reinstalling.');
    } catch (error) {
      toast.error('Failed to save icon URL');
    }
  };

  const toggleKeyVisibility = (key) => {
    setShowKeys(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const maskValue = (value) => {
    if (!value) return '';
    if (value.length <= 8) return '••••••••';
    return value.slice(0, 4) + '••••••••' + value.slice(-4);
  };

  // ===== DIAGNOSTIC FUNCTIONS =====
  
  // Load last sync date from localStorage
  useEffect(() => {
    const savedLastSync = localStorage.getItem('lastLicenseeSyncDate');
    if (savedLastSync) {
      setLastSyncDate(new Date(savedLastSync));
      // Recommend sync every 7 days
      const nextSync = new Date(savedLastSync);
      nextSync.setDate(nextSync.getDate() + 7);
      setNextSyncRecommended(nextSync);
    }
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-4 md:space-y-6 pb-20 md:pb-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <h1 className="text-xl md:text-2xl font-bold text-white flex items-center gap-2">
          <Settings className="w-5 h-5 md:w-6 md:h-6" /> Platform Settings
        </h1>
        <Button onClick={handleSave} className="btn-primary gap-2 w-full sm:w-auto" disabled={saving} data-testid="save-settings-button">
          {saving ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" /> Saving...
            </>
          ) : (
            <>
              <CheckCircle2 className="w-4 h-4" /> Save All Settings
            </>
          )}
        </Button>
      </div>

      {/* Mobile: Horizontal scrollable tabs */}
      <div className="md:hidden overflow-x-auto pb-2 -mx-3 px-3">
        <div className="flex gap-2 min-w-max">
          {[
            { key: 'seo', icon: Globe, label: 'SEO' },
            { key: 'branding', icon: Image, label: 'Brand' },
            { key: 'ui', icon: Palette, label: 'UI' },
            { key: 'integrations', icon: Plug, label: 'API' },
            { key: 'links', icon: ExternalLink, label: 'Links' },
            { key: 'emails', icon: Mail, label: 'Email' },
            { key: 'announcements', icon: Megaphone, label: 'News' },
            { key: 'trading', icon: TrendingUp, label: 'Trading' },
            { key: 'banners', icon: Megaphone, label: 'Banners' },
            { key: 'habits', icon: CheckCircle2, label: 'Habits' },
            { key: 'affiliate', icon: ExternalLink, label: 'Affiliate' },
            { key: 'security', icon: Shield, label: 'Security' },
            { key: 'holidays', icon: TreePine, label: 'Holidays' },
            { key: 'diagnostics', icon: Database, label: 'Diagnostic' },
            { key: 'maintenance', icon: Wrench, label: 'Maint' },
          ].map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium whitespace-nowrap transition-colors ${
                  activeTab === tab.key 
                    ? 'bg-blue-500 text-white' 
                    : 'bg-zinc-800 text-zinc-400 hover:text-white'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Sidebar + Content Layout */}
      <div className="flex gap-6">
        {/* Desktop Sidebar Navigation */}
        <div className="hidden md:block w-56 flex-shrink-0">
          <div className="sticky top-4 space-y-1 bg-zinc-900/50 rounded-lg border border-zinc-800 p-2">
            {/* Regular Settings */}
            <button
              onClick={() => setActiveTab('seo')}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-md text-sm transition-colors ${
                activeTab === 'seo' ? 'bg-blue-500 text-white' : 'text-zinc-300 hover:bg-zinc-800 hover:text-white'
              }`}
              data-testid="tab-seo"
            >
              <Globe className="w-4 h-4" /> SEO & Meta
            </button>
            <button
              onClick={() => setActiveTab('branding')}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-md text-sm transition-colors ${
                activeTab === 'branding' ? 'bg-blue-500 text-white' : 'text-zinc-300 hover:bg-zinc-800 hover:text-white'
              }`}
              data-testid="tab-branding"
            >
              <Image className="w-4 h-4" /> Branding
            </button>
            <button
              onClick={() => setActiveTab('ui')}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-md text-sm transition-colors ${
                activeTab === 'ui' ? 'bg-blue-500 text-white' : 'text-zinc-300 hover:bg-zinc-800 hover:text-white'
              }`}
              data-testid="tab-ui"
            >
              <Palette className="w-4 h-4" /> UI Settings
            </button>
            <button
              onClick={() => setActiveTab('integrations')}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-md text-sm transition-colors ${
                activeTab === 'integrations' ? 'bg-blue-500 text-white' : 'text-zinc-300 hover:bg-zinc-800 hover:text-white'
              }`}
              data-testid="tab-integrations"
            >
              <Plug className="w-4 h-4" /> API Keys
            </button>
            <button
              onClick={() => setActiveTab('links')}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-md text-sm transition-colors ${
                activeTab === 'links' ? 'bg-blue-500 text-white' : 'text-zinc-300 hover:bg-zinc-800 hover:text-white'
              }`}
              data-testid="tab-links"
            >
              <ExternalLink className="w-4 h-4" /> Links
            </button>
            <button
              onClick={() => setActiveTab('emails')}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-md text-sm transition-colors ${
                activeTab === 'emails' ? 'bg-blue-500 text-white' : 'text-zinc-300 hover:bg-zinc-800 hover:text-white'
              }`}
              data-testid="tab-emails"
            >
              <Mail className="w-4 h-4" /> Emails
            </button>
            <button
              onClick={() => setActiveTab('maintenance')}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-md text-sm transition-colors ${
                activeTab === 'maintenance' ? 'bg-amber-500 text-white' : 'text-zinc-300 hover:bg-zinc-800 hover:text-white'
              }`}
              data-testid="tab-maintenance"
            >
              <Wrench className="w-4 h-4" /> Maintenance
            </button>
            <button
              onClick={() => setActiveTab('security')}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-md text-sm transition-colors ${
                activeTab === 'security' ? 'bg-red-500 text-white' : 'text-zinc-300 hover:bg-zinc-800 hover:text-white'
              }`}
              data-testid="tab-security"
            >
              <Shield className="w-4 h-4" /> Security
            </button>
            
            {/* Master Admin Only Section */}
            {isMasterAdmin && (
              <>
                <div className="my-3 border-t border-zinc-700" />
                <p className="px-3 py-1 text-xs text-zinc-500 uppercase tracking-wider flex items-center gap-1">
                  <Crown className="w-3 h-3" /> Master Admin
                </p>
                <button
                  onClick={() => setActiveTab('trading')}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-md text-sm transition-colors ${
                    activeTab === 'trading' ? 'bg-emerald-500 text-white' : 'text-zinc-300 hover:bg-zinc-800 hover:text-white'
                  }`}
                  data-testid="tab-trading"
                >
                  <TreePine className="w-4 h-4" /> Global Trading
                </button>
                <button
                  onClick={() => setActiveTab('banners')}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-md text-sm transition-colors ${
                    activeTab === 'banners' ? 'bg-purple-500 text-white' : 'text-zinc-300 hover:bg-zinc-800 hover:text-white'
                  }`}
                  data-testid="tab-banners"
                >
                  <Megaphone className="w-4 h-4" /> Banners & Popups
                </button>
                <button
                  onClick={() => setActiveTab('habits')}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-md text-sm transition-colors ${
                    activeTab === 'habits' ? 'bg-teal-500 text-white' : 'text-zinc-300 hover:bg-zinc-800 hover:text-white'
                  }`}
                  data-testid="tab-habits"
                >
                  <CheckCircle2 className="w-4 h-4" /> Habit Tracker
                </button>
                <button
                  onClick={() => setActiveTab('affiliate')}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-md text-sm transition-colors ${
                    activeTab === 'affiliate' ? 'bg-cyan-500 text-white' : 'text-zinc-300 hover:bg-zinc-800 hover:text-white'
                  }`}
                  data-testid="tab-affiliate"
                >
                  <ExternalLink className="w-4 h-4" /> Affiliate Center
                </button>
                <button
                  onClick={() => setActiveTab('diagnostics')}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-md text-sm transition-colors ${
                    activeTab === 'diagnostics' ? 'bg-orange-500 text-white' : 'text-zinc-300 hover:bg-zinc-800 hover:text-white'
                  }`}
                  data-testid="tab-diagnostics"
                >
                  <Database className="w-4 h-4" /> Diagnostics
                </button>
              </>
            )}
          </div>
        </div>
        
        {/* Content Area */}
        <div className="flex-1 min-w-0">
          {/* SEO & Meta */}
          {activeTab === 'seo' && (
          <Card className="glass-card">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Globe className="w-5 h-5 text-blue-400" /> SEO & Meta Settings
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label className="text-zinc-300">Site Title (Browser Tab)</Label>
                <Input
                  value={settings.site_title || ''}
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
                  value={settings.site_description || ''}
                  onChange={(e) => setSettings({ ...settings, site_description: e.target.value })}
                  className="input-dark mt-1"
                  data-testid="site-description-input"
                />
                <p className="text-xs text-zinc-500 mt-1">Used for SEO and social sharing</p>
              </div>
              <div>
                <Label className="text-zinc-300">OG Image URL (Social Sharing)</Label>
                <Input
                  value={settings.og_image_url || ''}
                  onChange={(e) => setSettings({ ...settings, og_image_url: e.target.value })}
                  placeholder="https://example.com/og-image.png"
                  className="input-dark mt-1"
                  data-testid="og-image-input"
                />
                <p className="text-xs text-zinc-500 mt-1">Image displayed when sharing on social media</p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Branding Tab */}
        {activeTab === 'branding' && (
          <Card className="glass-card">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Image className="w-5 h-5 text-purple-400" /> Branding
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Platform Name */}
              <div>
                <Label className="text-zinc-300">Platform Name</Label>
                <Input
                  value={settings.platform_name || ''}
                  onChange={(e) => setSettings({ ...settings, platform_name: e.target.value })}
                  placeholder="CrossCurrent"
                  className="input-dark mt-1"
                />
                <p className="text-xs text-zinc-500 mt-1">Displayed in sidebar and login page</p>
              </div>

              {/* Tagline */}
              <div>
                <Label className="text-zinc-300">Tagline</Label>
                <Input
                  value={settings.tagline || ''}
                  onChange={(e) => setSettings({ ...settings, tagline: e.target.value })}
                  placeholder="Finance Center"
                  className="input-dark mt-1"
                />
                <p className="text-xs text-zinc-500 mt-1">Displayed below platform name on login page</p>
              </div>

              {/* Logo */}
              <div>
                <Label className="text-zinc-300">Logo (replaces CrossCurrent text in sidebar)</Label>
                <div className="mt-2 flex items-center gap-4">
                  {settings.logo_url ? (
                    <div className="w-32 h-16 rounded-lg bg-zinc-900 flex items-center justify-center overflow-hidden border border-zinc-700">
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
                    <div className="w-12 h-12 rounded-lg bg-zinc-900 flex items-center justify-center overflow-hidden border border-zinc-700">
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

              {/* PWA App Icon */}
              <div>
                <Label className="text-zinc-300">PWA App Icon (home screen icon)</Label>
                <p className="text-xs text-zinc-500 mt-1 mb-2">
                  This icon appears on home screens when users install the app. Recommended: 512x512px PNG.
                </p>
                <div className="mt-2 flex items-center gap-4">
                  {settings.pwa_icon_url ? (
                    <div className="w-16 h-16 rounded-xl bg-zinc-900 flex items-center justify-center overflow-hidden border border-zinc-700">
                      <img src={settings.pwa_icon_url} alt="PWA Icon" className="w-14 h-14 object-contain rounded-lg" />
                    </div>
                  ) : (
                    <div className="w-16 h-16 rounded-xl bg-zinc-900 flex items-center justify-center border-2 border-dashed border-zinc-700">
                      <Smartphone className="w-6 h-6 text-zinc-500" />
                    </div>
                  )}
                  <div className="flex-1 space-y-2">
                    <div className="flex gap-2">
                      <input
                        type="file"
                        accept="image/png,image/jpeg,image/webp"
                        onChange={handlePwaIconUpload}
                        className="hidden"
                        id="pwa-icon-upload"
                        data-testid="pwa-icon-upload-input"
                      />
                      <label htmlFor="pwa-icon-upload">
                        <Button asChild variant="outline" className="btn-secondary cursor-pointer">
                          <span>
                            <Upload className="w-4 h-4 mr-2" /> Upload
                          </span>
                        </Button>
                      </label>
                    </div>
                    <div className="flex gap-2">
                      <Input
                        value={settings.pwa_icon_url_input || ''}
                        onChange={(e) => setSettings(prev => ({ ...prev, pwa_icon_url_input: e.target.value }))}
                        placeholder="Or paste image URL here..."
                        className="input-dark text-xs h-8"
                        data-testid="pwa-icon-url-input"
                      />
                      <Button variant="outline" size="sm" className="btn-secondary h-8 px-3" onClick={handlePwaIconUrl} data-testid="pwa-icon-url-save">
                        Set
                      </Button>
                    </div>
                    {settings.pwa_icon_url && (
                      <p className="text-xs text-emerald-400">Icon set. Users need to reinstall to see changes.</p>
                    )}
                  </div>
                </div>
              </div>

              {/* Production Site URL */}
              <div>
                <Label className="text-zinc-300">Production Site URL</Label>
                <Input
                  value={settings.production_site_url || ''}
                  onChange={(e) => setSettings({ ...settings, production_site_url: e.target.value })}
                  placeholder="https://app.crosscurrent.com"
                  className="input-dark mt-1"
                />
                <p className="text-xs text-zinc-500 mt-1">All test/preview links will be replaced with this URL in emails and exports</p>
              </div>

              {/* Hide Emergent Badge Toggle - Master Admin Only */}
              {isMasterAdmin() && (
                <div className="flex items-center justify-between p-4 rounded-lg bg-zinc-900/50 border border-purple-500/20">
                  <div className="flex items-center gap-3">
                    <Crown className="w-5 h-5 text-purple-400" />
                    <div>
                      <Label className="text-zinc-300">Hide Made with Emergent Badge</Label>
                      <p className="text-xs text-zinc-500 mt-1">Master Admin only - Toggle to show/hide the Emergent branding badge</p>
                    </div>
                  </div>
                  <Switch
                    checked={settings.hide_emergent_badge}
                    onCheckedChange={(v) => setSettings({ ...settings, hide_emergent_badge: v })}
                    data-testid="hide-badge-toggle"
                  />
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* UI Customization Tab */}
        {activeTab === 'ui' && (
          <div className="space-y-6">
          {/* Login Page Settings */}
          <Card className="glass-card">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <LogIn className="w-5 h-5 text-purple-400" /> Login Page Customization
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-zinc-300">Login Title (Optional)</Label>
                  <Input
                    value={settings.login_title || ''}
                    onChange={(e) => setSettings({ ...settings, login_title: e.target.value })}
                    placeholder="e.g., Welcome Back"
                    className="input-dark mt-1"
                  />
                  <p className="text-xs text-zinc-500 mt-1">Displayed below the logo</p>
                </div>
                <div>
                  <Label className="text-zinc-300">Login Tagline</Label>
                  <Input
                    value={settings.login_tagline || ''}
                    onChange={(e) => setSettings({ ...settings, login_tagline: e.target.value })}
                    placeholder={settings.tagline || 'Finance Center'}
                    className="input-dark mt-1"
                  />
                  <p className="text-xs text-zinc-500 mt-1">Shown below the title</p>
                </div>
              </div>
              <div>
                <Label className="text-zinc-300">Login Notice Message</Label>
                <Input
                  value={settings.login_notice || ''}
                  onChange={(e) => setSettings({ ...settings, login_notice: e.target.value })}
                  placeholder="Only CrossCurrent community members can access this platform."
                  className="input-dark mt-1"
                />
                <p className="text-xs text-zinc-500 mt-1">Displayed at the bottom of the login card</p>
              </div>
              
              {/* Preview */}
              <div className="p-4 rounded-lg bg-zinc-900/50 border border-zinc-800">
                <p className="text-xs text-zinc-500 mb-3">Preview:</p>
                <div className="flex flex-col items-center text-center">
                  <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center mb-2">
                    <Settings className="w-6 h-6 text-white" />
                  </div>
                  {settings.login_title && (
                    <p className="text-lg font-bold text-white">{settings.login_title}</p>
                  )}
                  <p className="text-zinc-400 text-sm">{settings.login_tagline || settings.tagline || 'Finance Center'}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Color Scheme */}
          <Card className="glass-card">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Palette className="w-5 h-5 text-cyan-400" /> Color Scheme
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-zinc-300">Primary Color</Label>
                  <div className="flex items-center gap-3 mt-1">
                    <input
                      type="color"
                      value={settings.primary_color || '#3B82F6'}
                      onChange={(e) => setSettings({ ...settings, primary_color: e.target.value })}
                      className="w-12 h-10 rounded cursor-pointer bg-transparent border border-zinc-700"
                    />
                    <Input
                      value={settings.primary_color || ''}
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
                      value={settings.accent_color || '#10B981'}
                      onChange={(e) => setSettings({ ...settings, accent_color: e.target.value })}
                      className="w-12 h-10 rounded cursor-pointer bg-transparent border border-zinc-700"
                    />
                    <Input
                      value={settings.accent_color || ''}
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
          </div>
        )}

        {/* Integrations Tab */}
        {activeTab === 'integrations' && (
          <div className="space-y-6">
          {/* Emailit */}
          <Card className="glass-card">
            <CardHeader>
              <CardTitle className="text-white flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Mail className="w-5 h-5 text-emerald-400" /> Emailit
                </div>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={handleTestEmailit}
                  disabled={testingEmailit}
                  className={`btn-secondary ${testResults.emailit?.success ? 'border-emerald-500/30' : testResults.emailit?.success === false ? 'border-red-500/30' : ''}`}
                >
                  {testingEmailit ? (
                    <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Testing...</>
                  ) : testResults.emailit?.success ? (
                    <><CheckCircle2 className="w-4 h-4 mr-2 text-emerald-400" /> Connected</>
                  ) : testResults.emailit?.success === false ? (
                    <><XCircle className="w-4 h-4 mr-2 text-red-400" /> Failed</>
                  ) : (
                    <><Zap className="w-4 h-4 mr-2" /> Test Connection</>
                  )}
                </Button>
              </CardTitle>
              <p className="text-sm text-zinc-500">Email notification service for trade signals and alerts</p>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label className="text-zinc-300">API Key</Label>
                <div className="flex items-center gap-2 mt-1">
                  <div className="relative flex-1">
                    <Input
                      type={showKeys.emailit ? 'text' : 'password'}
                      value={settings.emailit_api_key || ''}
                      onChange={(e) => setSettings({ ...settings, emailit_api_key: e.target.value })}
                      placeholder="em_xxxxxxxxxxxx"
                      className="input-dark pr-10"
                      data-testid="emailit-api-key"
                    />
                    <button
                      type="button"
                      onClick={() => toggleKeyVisibility('emailit')}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300"
                    >
                      {showKeys.emailit ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
                <p className="text-xs text-zinc-500 mt-1">
                  Get your API key from <a href="https://emailit.com" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline">emailit.com</a>
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Cloudinary */}
          <Card className="glass-card">
            <CardHeader>
              <CardTitle className="text-white flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Cloud className="w-5 h-5 text-blue-400" /> Cloudinary
                </div>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={handleTestCloudinary}
                  disabled={testingCloudinary}
                  className={`btn-secondary ${testResults.cloudinary?.success ? 'border-emerald-500/30' : testResults.cloudinary?.success === false ? 'border-red-500/30' : ''}`}
                >
                  {testingCloudinary ? (
                    <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Testing...</>
                  ) : testResults.cloudinary?.success ? (
                    <><CheckCircle2 className="w-4 h-4 mr-2 text-emerald-400" /> Connected</>
                  ) : testResults.cloudinary?.success === false ? (
                    <><XCircle className="w-4 h-4 mr-2 text-red-400" /> Failed</>
                  ) : (
                    <><Zap className="w-4 h-4 mr-2" /> Test Connection</>
                  )}
                </Button>
              </CardTitle>
              <p className="text-sm text-zinc-500">Image and file upload service for logos and profile pictures</p>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label className="text-zinc-300">Cloud Name</Label>
                <Input
                  value={settings.cloudinary_cloud_name || ''}
                  onChange={(e) => setSettings({ ...settings, cloudinary_cloud_name: e.target.value })}
                  placeholder="your-cloud-name"
                  className="input-dark mt-1"
                  data-testid="cloudinary-cloud-name"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-zinc-300">API Key</Label>
                  <div className="relative mt-1">
                    <Input
                      type={showKeys.cloudinary_key ? 'text' : 'password'}
                      value={settings.cloudinary_api_key || ''}
                      onChange={(e) => setSettings({ ...settings, cloudinary_api_key: e.target.value })}
                      placeholder="xxxxxxxxxxxx"
                      className="input-dark pr-10"
                      data-testid="cloudinary-api-key"
                    />
                    <button
                      type="button"
                      onClick={() => toggleKeyVisibility('cloudinary_key')}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300"
                    >
                      {showKeys.cloudinary_key ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
                <div>
                  <Label className="text-zinc-300">API Secret</Label>
                  <div className="relative mt-1">
                    <Input
                      type={showKeys.cloudinary_secret ? 'text' : 'password'}
                      value={settings.cloudinary_api_secret || ''}
                      onChange={(e) => setSettings({ ...settings, cloudinary_api_secret: e.target.value })}
                      placeholder="xxxxxxxxxxxx"
                      className="input-dark pr-10"
                      data-testid="cloudinary-api-secret"
                    />
                    <button
                      type="button"
                      onClick={() => toggleKeyVisibility('cloudinary_secret')}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300"
                    >
                      {showKeys.cloudinary_secret ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
              </div>
              <p className="text-xs text-zinc-500">
                Get your credentials from <a href="https://cloudinary.com/console" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline">cloudinary.com/console</a>
              </p>
            </CardContent>
          </Card>

          {/* Heartbeat */}
          <Card className="glass-card">
            <CardHeader>
              <CardTitle className="text-white flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Heart className="w-5 h-5 text-red-400" /> Heartbeat
                </div>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={handleTestHeartbeat}
                  disabled={testingHeartbeat}
                  className={`btn-secondary ${testResults.heartbeat?.success ? 'border-emerald-500/30' : testResults.heartbeat?.success === false ? 'border-red-500/30' : ''}`}
                >
                  {testingHeartbeat ? (
                    <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Testing...</>
                  ) : testResults.heartbeat?.success ? (
                    <><CheckCircle2 className="w-4 h-4 mr-2 text-emerald-400" /> Connected</>
                  ) : testResults.heartbeat?.success === false ? (
                    <><XCircle className="w-4 h-4 mr-2 text-red-400" /> Failed</>
                  ) : (
                    <><Zap className="w-4 h-4 mr-2" /> Test Connection</>
                  )}
                </Button>
              </CardTitle>
              <p className="text-sm text-zinc-500">Community membership verification for user registration</p>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label className="text-zinc-300">API Key</Label>
                <div className="flex items-center gap-2 mt-1">
                  <div className="relative flex-1">
                    <Input
                      type={showKeys.heartbeat ? 'text' : 'password'}
                      value={settings.heartbeat_api_key || ''}
                      onChange={(e) => setSettings({ ...settings, heartbeat_api_key: e.target.value })}
                      placeholder="hb:xxxxxxxxxxxx"
                      className="input-dark pr-10"
                      data-testid="heartbeat-api-key"
                    />
                    <button
                      type="button"
                      onClick={() => toggleKeyVisibility('heartbeat')}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300"
                    >
                      {showKeys.heartbeat ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
                <p className="text-xs text-zinc-500 mt-1">
                  Get your API key from <a href="https://heartbeat.chat" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline">heartbeat.chat</a> dashboard
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Publitio */}
          <Card className="glass-card">
            <CardHeader>
              <CardTitle className="text-white flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <ImageIcon className="w-5 h-5 text-purple-400" /> Publitio
                </div>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={handleTestPublitio}
                  disabled={testingPublitio}
                  className={`btn-secondary ${testResults.publitio?.success ? 'border-emerald-500/30' : testResults.publitio?.success === false ? 'border-red-500/30' : ''}`}
                >
                  {testingPublitio ? (
                    <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Testing...</>
                  ) : testResults.publitio?.success ? (
                    <><CheckCircle2 className="w-4 h-4 mr-2 text-emerald-400" /> Connected</>
                  ) : testResults.publitio?.success === false ? (
                    <><XCircle className="w-4 h-4 mr-2 text-red-400" /> Failed</>
                  ) : (
                    <><Zap className="w-4 h-4 mr-2" /> Test Connection</>
                  )}
                </Button>
              </CardTitle>
              <p className="text-sm text-zinc-500">Image hosting service for forum posts and comments (max 2MB)</p>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-zinc-300">API Key</Label>
                  <div className="relative mt-1">
                    <Input
                      type={showKeys.publitio_key ? 'text' : 'password'}
                      value={settings.publitio_api_key || ''}
                      onChange={(e) => setSettings({ ...settings, publitio_api_key: e.target.value })}
                      placeholder="xxxxxxxxxxxx"
                      className="input-dark pr-10"
                      data-testid="publitio-api-key"
                    />
                    <button
                      type="button"
                      onClick={() => toggleKeyVisibility('publitio_key')}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300"
                    >
                      {showKeys.publitio_key ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
                <div>
                  <Label className="text-zinc-300">API Secret</Label>
                  <div className="relative mt-1">
                    <Input
                      type={showKeys.publitio_secret ? 'text' : 'password'}
                      value={settings.publitio_api_secret || ''}
                      onChange={(e) => setSettings({ ...settings, publitio_api_secret: e.target.value })}
                      placeholder="xxxxxxxxxxxx"
                      className="input-dark pr-10"
                      data-testid="publitio-api-secret"
                    />
                    <button
                      type="button"
                      onClick={() => toggleKeyVisibility('publitio_secret')}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300"
                    >
                      {showKeys.publitio_secret ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
              </div>
              <div className="p-3 rounded-lg bg-purple-500/10 border border-purple-500/20">
                <p className="text-sm text-purple-300 font-medium mb-2">How to get Publitio API credentials:</p>
                <ol className="text-xs text-zinc-400 space-y-1 list-decimal list-inside">
                  <li>Go to <a href="https://publit.io" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline">publit.io</a> and create a free account</li>
                  <li>Navigate to Dashboard → Settings → API</li>
                  <li>Copy your API Key and API Secret</li>
                  <li>Paste them here and click "Save All Changes"</li>
                </ol>
                <p className="text-xs text-zinc-500 mt-2">Free tier includes 500MB storage and 2GB bandwidth/month</p>
              </div>
            </CardContent>
          </Card>

          {/* Info Box */}
          <div className="p-4 rounded-lg bg-amber-500/10 border border-amber-500/30">
            <div className="flex items-start gap-3">
              <Key className="w-5 h-5 text-amber-400 mt-0.5" />
              <div>
                <p className="text-amber-400 font-medium">Security Note</p>
                <p className="text-sm text-zinc-400 mt-1">
                  API keys are stored securely and are only visible to admin users. 
                  Changes to integration settings will take effect after saving.
                </p>
              </div>
            </div>
          </div>
          </div>
        )}

        {/* Custom Links Tab */}
        {activeTab === 'links' && (
          <div className="space-y-6">
          {/* Registration Link */}
          <Card className="glass-card">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Link className="w-5 h-5 text-blue-400" /> Registration Link
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div>
                <Label className="text-zinc-300">External Registration Link</Label>
                <p className="text-xs text-zinc-500 mt-1 mb-2">
                  Link to external registration page (e.g., Heartbeat signup). Shown to non-members on the login page.
                </p>
                <div className="relative">
                  <ExternalLink className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                  <Input
                    value={settings.custom_registration_link || ''}
                    onChange={(e) => setSettings({ ...settings, custom_registration_link: e.target.value })}
                    placeholder="https://heartbeat.chat/join/crosscurrent"
                    className="input-dark pl-10"
                  />
                </div>
                {settings.custom_registration_link && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => window.open(settings.custom_registration_link, '_blank')}
                    className="text-blue-400 hover:text-blue-300 mt-2"
                  >
                    <ExternalLink className="w-4 h-4 mr-1" /> Test Link
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Footer Settings */}
          {(isSuperAdmin() || isMasterAdmin()) && (
            <Card className="glass-card">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Copyright className="w-5 h-5 text-amber-400" /> Footer Settings
                </CardTitle>
                <p className="text-sm text-zinc-500">Configure footer links and copyright notice</p>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Copyright Text */}
                <div>
                  <Label className="text-zinc-300">Copyright Text</Label>
                  <Input
                    value={settings.footer_copyright || ''}
                    onChange={(e) => setSettings({ ...settings, footer_copyright: e.target.value })}
                    placeholder="© 2024 CrossCurrent Finance Center. All rights reserved."
                    className="input-dark mt-1"
                  />
                </div>

                {/* Footer Links */}
                <div>
                  <Label className="text-zinc-300 mb-2 block">Footer Links</Label>
                  
                  {/* Current Links */}
                  {(settings.footer_links || []).length > 0 && (
                    <div className="space-y-2 mb-4">
                      {(settings.footer_links || []).map((link, index) => (
                        <div key={index} className="flex items-center gap-2 p-3 rounded-lg bg-zinc-900/50 border border-zinc-800">
                          <GripVertical className="w-4 h-4 text-zinc-600" />
                          <span className="text-zinc-300 flex-1">{link.label}</span>
                          <span className="text-zinc-500 text-sm truncate max-w-[200px]">{link.url}</span>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleRemoveFooterLink(index)}
                            className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Add New Link */}
                  <div className="flex gap-2">
                    <Input
                      value={newFooterLink.label}
                      onChange={(e) => setNewFooterLink({ ...newFooterLink, label: e.target.value })}
                      placeholder="Link Label (e.g., Privacy)"
                      className="input-dark flex-1"
                    />
                    <Input
                      value={newFooterLink.url}
                      onChange={(e) => setNewFooterLink({ ...newFooterLink, url: e.target.value })}
                      placeholder="URL (e.g., /privacy)"
                      className="input-dark flex-1"
                    />
                    <Button onClick={handleAddFooterLink} className="btn-primary">
                      <Plus className="w-4 h-4" />
                    </Button>
                  </div>
                </div>

                {/* Footer Preview */}
                <div className="p-4 rounded-lg bg-zinc-900/50 border border-zinc-800">
                  <p className="text-xs text-zinc-500 mb-3">Preview:</p>
                  <div className="flex flex-wrap items-center justify-between gap-4 text-sm">
                    <span className="text-zinc-500">{settings.footer_copyright}</span>
                    <div className="flex gap-4">
                      {(settings.footer_links || []).map((link, index) => (
                        <span key={index} className="text-zinc-400 hover:text-white cursor-pointer">{link.label}</span>
                      ))}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
          </div>
        )}

        {/* Email Templates Tab */}
        {activeTab === 'emails' && <EmailsTab />}

        {/* Maintenance Tab */}
        {/* Maintenance Tab */}
        {activeTab === 'maintenance' && (
          <div className="space-y-6">
          {/* Maintenance Mode Card */}
          <Card className={`glass-card ${settings.maintenance_mode ? 'border-amber-500/50' : ''}`}>
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <AlertTriangle className={`w-5 h-5 ${settings.maintenance_mode ? 'text-amber-400' : 'text-zinc-400'}`} /> 
                Maintenance Mode
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between p-4 rounded-lg bg-zinc-900/50 border border-zinc-800">
                <div>
                  <p className="text-white font-medium">Enable Maintenance Mode</p>
                  <p className="text-sm text-zinc-400 mt-1">
                    When enabled, all users except Master Admin will see a maintenance page and cannot login.
                  </p>
                </div>
                <Switch
                  checked={settings.maintenance_mode}
                  onCheckedChange={(checked) => setSettings({ ...settings, maintenance_mode: checked })}
                  data-testid="maintenance-toggle"
                />
              </div>
              
              {settings.maintenance_mode && (
                <div className="p-4 rounded-lg bg-amber-500/10 border border-amber-500/30">
                  <div className="flex items-center gap-2 text-amber-400 mb-2">
                    <AlertTriangle className="w-4 h-4" />
                    <span className="font-medium">Maintenance Mode Active</span>
                  </div>
                  <p className="text-sm text-zinc-300">
                    All users are blocked from logging in. Only Master Admin can access by clicking the hidden button.
                  </p>
                </div>
              )}
              
              <div>
                <Label className="text-zinc-300">Maintenance Message</Label>
                <Textarea
                  value={settings.maintenance_message || ''}
                  onChange={(e) => setSettings({ ...settings, maintenance_message: e.target.value })}
                  placeholder="Our services are undergoing maintenance, and will be back soon!"
                  className="input-dark mt-1 min-h-[100px]"
                  data-testid="maintenance-message"
                />
                <p className="text-xs text-zinc-500 mt-1">This message will be displayed on the maintenance page.</p>
              </div>
            </CardContent>
          </Card>

          {/* Announcements Card */}
          <Card className="glass-card">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Megaphone className="w-5 h-5 text-blue-400" /> Announcements
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-zinc-400">
                Create announcement banners that appear at the top of the dashboard for all users.
              </p>

              {/* Add New Announcement Form */}
              <div className="p-4 rounded-lg bg-zinc-900/50 border border-zinc-800 space-y-4">
                <h4 className="text-white font-medium">New Announcement</h4>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label className="text-zinc-300">Title (Optional)</Label>
                    <Input
                      value={newAnnouncement.title}
                      onChange={(e) => setNewAnnouncement({ ...newAnnouncement, title: e.target.value })}
                      placeholder="e.g., System Update"
                      className="input-dark mt-1"
                    />
                  </div>
                  <div>
                    <Label className="text-zinc-300">Type</Label>
                    <Select 
                      value={newAnnouncement.type} 
                      onValueChange={(value) => setNewAnnouncement({ ...newAnnouncement, type: value })}
                    >
                      <SelectTrigger className="bg-zinc-900/50 border-zinc-800 text-white mt-1">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-zinc-900 border-zinc-800">
                        <SelectItem value="info" className="text-white hover:bg-zinc-800">
                          <span className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-blue-500" /> Info</span>
                        </SelectItem>
                        <SelectItem value="warning" className="text-white hover:bg-zinc-800">
                          <span className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-amber-500" /> Warning</span>
                        </SelectItem>
                        <SelectItem value="success" className="text-white hover:bg-zinc-800">
                          <span className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-emerald-500" /> Success</span>
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div>
                  <Label className="text-zinc-300">Message *</Label>
                  <Textarea
                    value={newAnnouncement.message}
                    onChange={(e) => setNewAnnouncement({ ...newAnnouncement, message: e.target.value })}
                    placeholder="Enter your announcement message..."
                    className="input-dark mt-1"
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label className="text-zinc-300">Link URL (Optional)</Label>
                    <Input
                      value={newAnnouncement.link_url}
                      onChange={(e) => setNewAnnouncement({ ...newAnnouncement, link_url: e.target.value })}
                      placeholder="https://..."
                      className="input-dark mt-1"
                    />
                  </div>
                  <div>
                    <Label className="text-zinc-300">Link Text (Optional)</Label>
                    <Input
                      value={newAnnouncement.link_text}
                      onChange={(e) => setNewAnnouncement({ ...newAnnouncement, link_text: e.target.value })}
                      placeholder="Learn more"
                      className="input-dark mt-1"
                    />
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Switch
                      checked={newAnnouncement.sticky}
                      onCheckedChange={(checked) => setNewAnnouncement({ ...newAnnouncement, sticky: checked })}
                    />
                    <Label className="text-zinc-300">Sticky (stays at top)</Label>
                  </div>
                  <Button onClick={handleAddAnnouncement} className="btn-primary gap-2">
                    <Plus className="w-4 h-4" /> Add Announcement
                  </Button>
                </div>
              </div>

              {/* Active Announcements List */}
              {(settings.announcements || []).length > 0 && (
                <div className="space-y-3">
                  <h4 className="text-white font-medium">Active Announcements</h4>
                  {(settings.announcements || []).map((announcement, index) => (
                    <div 
                      key={announcement.id || index}
                      className={`p-4 rounded-lg border ${
                        announcement.type === 'warning' ? 'bg-amber-500/10 border-amber-500/30' :
                        announcement.type === 'success' ? 'bg-emerald-500/10 border-emerald-500/30' :
                        'bg-blue-500/10 border-blue-500/30'
                      } ${!announcement.active ? 'opacity-50' : ''}`}
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          {announcement.title && (
                            <p className="font-medium text-white">{announcement.title}</p>
                          )}
                          <p className={`text-sm ${
                            announcement.type === 'warning' ? 'text-amber-200' :
                            announcement.type === 'success' ? 'text-emerald-200' :
                            'text-blue-200'
                          }`}>{announcement.message}</p>
                          {announcement.link_url && (
                            <a 
                              href={announcement.link_url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="text-xs text-blue-400 hover:underline mt-1 inline-flex items-center gap-1"
                            >
                              {announcement.link_text || 'Learn more'} <ExternalLink className="w-3 h-3" />
                            </a>
                          )}
                          <div className="flex items-center gap-2 mt-2">
                            {announcement.sticky && (
                              <span className="px-2 py-0.5 bg-zinc-800 text-zinc-400 text-xs rounded">Sticky</span>
                            )}
                            <span className={`px-2 py-0.5 text-xs rounded ${
                              announcement.active ? 'bg-emerald-500/20 text-emerald-400' : 'bg-zinc-800 text-zinc-500'
                            }`}>
                              {announcement.active ? 'Active' : 'Inactive'}
                            </span>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Switch
                            checked={announcement.active}
                            onCheckedChange={() => handleToggleAnnouncement(index)}
                          />
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleRemoveAnnouncement(index)}
                            className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {(settings.announcements || []).length === 0 && (
                <div className="text-center py-8 text-zinc-500">
                  <Megaphone className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p>No announcements yet. Add one above!</p>
                </div>
              )}
            </CardContent>
          </Card>
          </div>
        )}

        {/* Security Tab - Content Protection */}
        {activeTab === 'security' && (
          <div className="space-y-6">
            {/* Content Protection Card */}
            <Card className={`glass-card ${settings.content_protection_enabled ? 'border-red-500/50' : ''}`}>
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Shield className={`w-5 h-5 ${settings.content_protection_enabled ? 'text-red-400' : 'text-zinc-400'}`} /> 
                  Content Protection
                </CardTitle>
                <p className="text-sm text-zinc-400 mt-1">
                  Prevent users from copying content or taking screenshots of the platform.
                </p>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Master Toggle */}
                <div className="flex items-center justify-between p-4 rounded-lg bg-zinc-900/50 border border-zinc-800">
                  <div>
                    <p className="text-white font-medium">Enable Content Protection</p>
                    <p className="text-sm text-zinc-500 mt-1">
                      When enabled, copy/paste and right-click will be disabled for all users.
                    </p>
                  </div>
                  <Switch 
                    checked={settings.content_protection_enabled}
                    onCheckedChange={(checked) => setSettings({ ...settings, content_protection_enabled: checked })}
                    data-testid="content-protection-toggle"
                  />
                </div>

                {settings.content_protection_enabled && (
                  <div className="space-y-4">
                    {/* Watermark Toggle */}
                    <div className="flex items-center justify-between p-4 rounded-lg bg-zinc-900/50 border border-zinc-800">
                      <div>
                        <p className="text-white font-medium">Show User Watermark</p>
                        <p className="text-sm text-zinc-500 mt-1">
                          Display user&apos;s email/name as a subtle watermark overlay on all pages.
                        </p>
                      </div>
                      <Switch 
                        checked={settings.content_protection_watermark}
                        onCheckedChange={(checked) => setSettings({ ...settings, content_protection_watermark: checked })}
                        data-testid="watermark-toggle"
                      />
                    </div>

                    {/* Custom Watermark Text (Master Admin Only) */}
                    {settings.content_protection_watermark && (
                      <div className="p-4 rounded-lg bg-zinc-900/50 border border-purple-500/30">
                        <div className="flex items-center gap-2 mb-3">
                          <Crown className="w-4 h-4 text-purple-400" />
                          <p className="text-purple-400 font-medium text-sm">Master Admin Only</p>
                        </div>
                        <Label className="text-zinc-300">Custom Watermark Text</Label>
                        <Input
                          value={settings.content_protection_watermark_custom || ''}
                          onChange={(e) => setSettings({ ...settings, content_protection_watermark_custom: e.target.value })}
                          placeholder="Leave empty to use user's name/email"
                          className="input-dark mt-2"
                          data-testid="custom-watermark-input"
                        />
                        <p className="text-xs text-zinc-500 mt-2">
                          If set, this text will be displayed instead of individual user names. 
                          Leave empty to show each user&apos;s email/name for traceability.
                        </p>
                      </div>
                    )}

                    {/* Copy Protection Toggle */}
                    <div className="flex items-center justify-between p-4 rounded-lg bg-zinc-900/50 border border-zinc-800">
                      <div>
                        <p className="text-white font-medium">Disable Text Selection & Copy</p>
                        <p className="text-sm text-zinc-500 mt-1">
                          Prevent users from selecting and copying text content.
                        </p>
                      </div>
                      <Switch 
                        checked={settings.content_protection_disable_copy}
                        onCheckedChange={(checked) => setSettings({ ...settings, content_protection_disable_copy: checked })}
                        data-testid="disable-copy-toggle"
                      />
                    </div>

                    {/* Right-Click Protection Toggle */}
                    <div className="flex items-center justify-between p-4 rounded-lg bg-zinc-900/50 border border-zinc-800">
                      <div>
                        <p className="text-white font-medium">Disable Right-Click Menu</p>
                        <p className="text-sm text-zinc-500 mt-1">
                          Block the browser context menu (right-click).
                        </p>
                      </div>
                      <Switch 
                        checked={settings.content_protection_disable_rightclick}
                        onCheckedChange={(checked) => setSettings({ ...settings, content_protection_disable_rightclick: checked })}
                        data-testid="disable-rightclick-toggle"
                      />
                    </div>

                    {/* Keyboard Shortcuts Protection Toggle */}
                    <div className="flex items-center justify-between p-4 rounded-lg bg-zinc-900/50 border border-zinc-800">
                      <div>
                        <p className="text-white font-medium">Block Keyboard Shortcuts</p>
                        <p className="text-sm text-zinc-500 mt-1">
                          Block Ctrl+C, Ctrl+A, PrintScreen, and other copy/screenshot shortcuts.
                        </p>
                      </div>
                      <Switch 
                        checked={settings.content_protection_disable_shortcuts}
                        onCheckedChange={(checked) => setSettings({ ...settings, content_protection_disable_shortcuts: checked })}
                        data-testid="disable-shortcuts-toggle"
                      />
                    </div>

                    {/* Info Box */}
                    <div className="p-4 rounded-lg bg-amber-500/10 border border-amber-500/30">
                      <div className="flex items-start gap-3">
                        <AlertTriangle className="w-5 h-5 text-amber-400 mt-0.5" />
                        <div>
                          <p className="text-amber-400 font-medium">Important Notice</p>
                          <p className="text-sm text-zinc-400 mt-1">
                            While these protections deter casual copying, they cannot prevent determined users 
                            from capturing content using external tools, screen recorders, or phone cameras. 
                            The watermark helps trace any leaked content back to the source user.
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}

          {/* Global Trading Settings (Master Admin Only) */}
          {activeTab === 'trading' && isMasterAdmin && <TradingTab />}

          {/* Banners & Popups - Master Admin Only */}
          {activeTab === 'banners' && isMasterAdmin && (
            <div className="space-y-6">
              {/* Notice Banner Card */}
              <Card className="glass-card">
                <CardHeader>
                  <CardTitle className="text-white flex items-center gap-2">
                    <Megaphone className="w-5 h-5 text-purple-400" /> Notice Banner
                  </CardTitle>
                  <p className="text-sm text-zinc-400 mt-1">
                    A sticky announcement bar shown at the top of selected pages. Members can dismiss it per session.
                  </p>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <Label className="text-zinc-300">Enable Notice Banner</Label>
                    <Switch
                      checked={settings.notice_banner_enabled || false}
                      onCheckedChange={(checked) => setSettings(prev => ({ ...prev, notice_banner_enabled: checked }))}
                      data-testid="notice-banner-toggle"
                    />
                  </div>

                  {settings.notice_banner_enabled && (
                    <div className="space-y-4 pt-2">
                      <div>
                        <Label className="text-zinc-300">Banner Text</Label>
                        <Input
                          value={settings.notice_banner_text || ''}
                          onChange={(e) => setSettings(prev => ({ ...prev, notice_banner_text: e.target.value }))}
                          placeholder="e.g., Trading hours changed to 3:00 PM starting next week"
                          className="input-dark mt-1"
                          data-testid="notice-banner-text"
                        />
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <Label className="text-zinc-300">Background Color</Label>
                          <div className="flex gap-2 mt-1">
                            <input
                              type="color"
                              value={settings.notice_banner_bg_color || '#3B82F6'}
                              onChange={(e) => setSettings(prev => ({ ...prev, notice_banner_bg_color: e.target.value }))}
                              className="w-10 h-10 rounded border border-zinc-700 cursor-pointer bg-transparent"
                            />
                            <Input
                              value={settings.notice_banner_bg_color || '#3B82F6'}
                              onChange={(e) => setSettings(prev => ({ ...prev, notice_banner_bg_color: e.target.value }))}
                              className="input-dark flex-1"
                            />
                          </div>
                        </div>
                        <div>
                          <Label className="text-zinc-300">Text Color</Label>
                          <div className="flex gap-2 mt-1">
                            <input
                              type="color"
                              value={settings.notice_banner_text_color || '#FFFFFF'}
                              onChange={(e) => setSettings(prev => ({ ...prev, notice_banner_text_color: e.target.value }))}
                              className="w-10 h-10 rounded border border-zinc-700 cursor-pointer bg-transparent"
                            />
                            <Input
                              value={settings.notice_banner_text_color || '#FFFFFF'}
                              onChange={(e) => setSettings(prev => ({ ...prev, notice_banner_text_color: e.target.value }))}
                              className="input-dark flex-1"
                            />
                          </div>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <Label className="text-zinc-300">Link Text (optional)</Label>
                          <Input
                            value={settings.notice_banner_link_text || ''}
                            onChange={(e) => setSettings(prev => ({ ...prev, notice_banner_link_text: e.target.value }))}
                            placeholder="e.g., Learn More"
                            className="input-dark mt-1"
                          />
                        </div>
                        <div>
                          <Label className="text-zinc-300">Link URL (optional)</Label>
                          <Input
                            value={settings.notice_banner_link_url || ''}
                            onChange={(e) => setSettings(prev => ({ ...prev, notice_banner_link_url: e.target.value }))}
                            placeholder="https://..."
                            className="input-dark mt-1"
                          />
                        </div>
                      </div>

                      {/* Page checkboxes */}
                      <div>
                        <Label className="text-zinc-300 mb-2 block">Show on Pages</Label>
                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                          {[
                            { key: 'dashboard', label: 'Dashboard' },
                            { key: 'profit_tracker', label: 'Profit Tracker' },
                            { key: 'trade_monitor', label: 'Trade Monitor' },
                            { key: 'habits', label: 'Daily Habits' },
                            { key: 'affiliate', label: 'Affiliate Center' },
                            { key: 'goals', label: 'Profit Planner' },
                            { key: 'debt', label: 'Debt Manager' },
                            { key: 'profile', label: 'Profile' },
                            { key: 'notifications', label: 'Notifications' },
                          ].map(page => {
                            const checked = (settings.notice_banner_pages || []).includes(page.key);
                            return (
                              <label key={page.key} className="flex items-center gap-2 p-2 rounded-lg bg-zinc-900/50 border border-zinc-800 cursor-pointer hover:border-zinc-600 transition-colors">
                                <input
                                  type="checkbox"
                                  checked={checked}
                                  onChange={(e) => {
                                    const pages = settings.notice_banner_pages || [];
                                    setSettings(prev => ({
                                      ...prev,
                                      notice_banner_pages: e.target.checked
                                        ? [...pages, page.key]
                                        : pages.filter(p => p !== page.key)
                                    }));
                                  }}
                                  className="rounded border-zinc-600 bg-zinc-800 text-blue-500"
                                  data-testid={`notice-page-${page.key}`}
                                />
                                <span className="text-sm text-zinc-300">{page.label}</span>
                              </label>
                            );
                          })}
                        </div>
                        <p className="text-xs text-zinc-500 mt-2">If no pages are selected, the banner will show on all pages.</p>
                      </div>

                      {/* Preview */}
                      {settings.notice_banner_text && (
                        <div>
                          <Label className="text-zinc-300 mb-2 block">Preview</Label>
                          <div
                            className="rounded-lg px-4 py-2.5 flex items-center justify-center gap-3 text-sm"
                            style={{ backgroundColor: settings.notice_banner_bg_color, color: settings.notice_banner_text_color }}
                          >
                            <span className="font-medium">{settings.notice_banner_text}</span>
                            {settings.notice_banner_link_text && (
                              <span className="underline font-semibold">{settings.notice_banner_link_text}</span>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Promotion Popup Card */}
              <Card className="glass-card">
                <CardHeader>
                  <CardTitle className="text-white flex items-center gap-2">
                    <Zap className="w-5 h-5 text-amber-400" /> Promotion Pop-up
                  </CardTitle>
                  <p className="text-sm text-zinc-400 mt-1">
                    A modal dialog shown to members on login. Configure with presets, images, and call-to-action buttons.
                  </p>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <Label className="text-zinc-300">Enable Promotion Pop-up</Label>
                    <Switch
                      checked={settings.promo_popup_enabled || false}
                      onCheckedChange={(checked) => setSettings(prev => ({ ...prev, promo_popup_enabled: checked }))}
                      data-testid="promo-popup-toggle"
                    />
                  </div>

                  {settings.promo_popup_enabled && (
                    <div className="space-y-4 pt-2">
                      {/* Preset */}
                      <div>
                        <Label className="text-zinc-300">Preset Style</Label>
                        <div className="grid grid-cols-3 gap-2 mt-1">
                          {[
                            { key: 'announcement', label: 'Announcement', color: 'border-blue-500/50 bg-blue-500/10 text-blue-400' },
                            { key: 'promo', label: 'Promo', color: 'border-amber-500/50 bg-amber-500/10 text-amber-400' },
                            { key: 'feature_update', label: 'Feature Update', color: 'border-emerald-500/50 bg-emerald-500/10 text-emerald-400' },
                          ].map(preset => (
                            <button
                              key={preset.key}
                              onClick={() => setSettings(prev => ({ ...prev, promo_popup_preset: preset.key }))}
                              className={`p-3 rounded-lg border text-sm font-medium transition-all ${
                                settings.promo_popup_preset === preset.key ? preset.color : 'border-zinc-700 bg-zinc-900/50 text-zinc-400'
                              }`}
                              data-testid={`promo-preset-${preset.key}`}
                            >
                              {preset.label}
                            </button>
                          ))}
                        </div>
                      </div>

                      <div>
                        <Label className="text-zinc-300">Title</Label>
                        <Input
                          value={settings.promo_popup_title || ''}
                          onChange={(e) => setSettings(prev => ({ ...prev, promo_popup_title: e.target.value }))}
                          placeholder="e.g., New Feature Available!"
                          className="input-dark mt-1"
                          data-testid="promo-popup-title-input"
                        />
                      </div>

                      <div>
                        <Label className="text-zinc-300">Body Text</Label>
                        <Textarea
                          value={settings.promo_popup_body || ''}
                          onChange={(e) => setSettings(prev => ({ ...prev, promo_popup_body: e.target.value }))}
                          placeholder="Describe your announcement or promotion..."
                          className="input-dark mt-1"
                          rows={3}
                          data-testid="promo-popup-body-input"
                        />
                      </div>

                      <div>
                        <Label className="text-zinc-300">Image URL (optional)</Label>
                        <Input
                          value={settings.promo_popup_image_url || ''}
                          onChange={(e) => setSettings(prev => ({ ...prev, promo_popup_image_url: e.target.value }))}
                          placeholder="https://example.com/image.jpg"
                          className="input-dark mt-1"
                        />
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <Label className="text-zinc-300">CTA Button Text</Label>
                          <Input
                            value={settings.promo_popup_cta_text || ''}
                            onChange={(e) => setSettings(prev => ({ ...prev, promo_popup_cta_text: e.target.value }))}
                            placeholder="Learn More"
                            className="input-dark mt-1"
                          />
                        </div>
                        <div>
                          <Label className="text-zinc-300">CTA Button URL</Label>
                          <Input
                            value={settings.promo_popup_cta_url || ''}
                            onChange={(e) => setSettings(prev => ({ ...prev, promo_popup_cta_url: e.target.value }))}
                            placeholder="https://..."
                            className="input-dark mt-1"
                          />
                        </div>
                      </div>

                      {/* Frequency */}
                      <div>
                        <Label className="text-zinc-300">Show Frequency</Label>
                        <Select
                          value={settings.promo_popup_frequency || 'once_per_session'}
                          onValueChange={(v) => setSettings(prev => ({ ...prev, promo_popup_frequency: v }))}
                        >
                          <SelectTrigger className="input-dark mt-1" data-testid="promo-frequency-select">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="once_per_session">Once per session</SelectItem>
                            <SelectItem value="once_per_day">Once per day</SelectItem>
                            <SelectItem value="always">Every page load</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Analytics Card */}
              <BannerAnalyticsCard />
            </div>
          )}

          {/* Habit Tracker - Master Admin Only */}
          {activeTab === 'habits' && isMasterAdmin && (
            <div className="space-y-6">
              <HabitManagerCard />
            </div>
          )}

          {/* Affiliate Center - Master Admin Only */}
          {activeTab === 'affiliate' && isMasterAdmin && (
            <AffiliateManagerCard />
          )}

          {/* Diagnostics - Master Admin Only */}
          {activeTab === 'diagnostics' && isMasterAdmin && <DiagnosticsTab />}
        </div>
      </div>
    </div>
  );
};

