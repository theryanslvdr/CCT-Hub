import React, { useState, useEffect } from 'react';
import { settingsAPI, adminAPI } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
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
  TreePine, Calendar as CalendarIcon
} from 'lucide-react';

export const AdminSettingsPage = () => {
  const { user, isMasterAdmin, isSuperAdmin } = useAuth();
  const [settings, setSettings] = useState({
    platform_name: 'CrossCurrent',
    tagline: 'Finance Center',
    site_title: 'CrossCurrent Finance Center',
    site_description: 'Trading profit management platform',
    favicon_url: '',
    logo_url: '',
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
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('seo');
  
  // Email templates state
  const [emailTemplates, setEmailTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [savingTemplate, setSavingTemplate] = useState(false);
  const [editorMode, setEditorMode] = useState('code'); // 'code' or 'preview'
  const [testEmailDialogOpen, setTestEmailDialogOpen] = useState(false);
  const [testEmailAddress, setTestEmailAddress] = useState('');
  const [sendingTestEmail, setSendingTestEmail] = useState(false);
  const [testVariableValues, setTestVariableValues] = useState({});
  
  // Footer links management
  const [newFooterLink, setNewFooterLink] = useState({ label: '', url: '' });
  // Integration test states
  const [testingEmailit, setTestingEmailit] = useState(false);
  const [testingCloudinary, setTestingCloudinary] = useState(false);
  const [testingHeartbeat, setTestingHeartbeat] = useState(false);
  const [testResults, setTestResults] = useState({});
  
  // Email history state
  const [emailHistory, setEmailHistory] = useState([]);
  const [emailHistoryPage, setEmailHistoryPage] = useState(1);
  const [emailHistoryTotal, setEmailHistoryTotal] = useState(0);
  const [emailHistoryLoading, setEmailHistoryLoading] = useState(false);
  const [clearingHistory, setClearingHistory] = useState(false);
  
  // Visibility toggles for sensitive fields
  const [showKeys, setShowKeys] = useState({
    emailit: false,
    cloudinary_key: false,
    cloudinary_secret: false,
    heartbeat: false
  });

  useEffect(() => {
    loadSettings();
    loadEmailTemplates();
    loadEmailHistory();
  }, []);

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

  const loadEmailTemplates = async () => {
    try {
      const res = await settingsAPI.getEmailTemplates();
      setEmailTemplates(res.data.templates || []);
    } catch (error) {
      console.error('Failed to load email templates:', error);
    }
  };

  const loadEmailHistory = async (page = 1) => {
    setEmailHistoryLoading(true);
    try {
      const res = await settingsAPI.getEmailHistory(page);
      setEmailHistory(res.data.emails || []);
      setEmailHistoryTotal(res.data.total || 0);
      setEmailHistoryPage(page);
    } catch (error) {
      console.error('Failed to load email history:', error);
    } finally {
      setEmailHistoryLoading(false);
    }
  };

  const handleClearEmailHistory = async () => {
    if (!window.confirm('Are you sure you want to clear all email history? This cannot be undone.')) return;
    
    setClearingHistory(true);
    try {
      await settingsAPI.clearEmailHistory();
      toast.success('Email history cleared');
      loadEmailHistory();
    } catch (error) {
      toast.error('Failed to clear email history');
    } finally {
      setClearingHistory(false);
    }
  };

  const handleSaveTemplate = async () => {
    if (!editingTemplate) return;
    
    setSavingTemplate(true);
    try {
      await settingsAPI.updateEmailTemplate(editingTemplate.type, {
        subject: editingTemplate.subject,
        body: editingTemplate.body,
        variables: editingTemplate.variables
      });
      toast.success('Email template saved!');
      setEditingTemplate(null);
      loadEmailTemplates();
    } catch (error) {
      toast.error('Failed to save template');
    } finally {
      setSavingTemplate(false);
    }
  };

  // Open test email dialog and initialize sample values
  const handleOpenTestEmail = () => {
    if (!editingTemplate) return;
    
    // Initialize test variable values with sample data
    const sampleValues = {};
    (editingTemplate.variables || []).forEach(v => {
      // Provide intelligent sample values based on variable name
      if (v.includes('name')) sampleValues[v] = 'John Doe';
      else if (v.includes('email')) sampleValues[v] = 'john@example.com';
      else if (v.includes('amount') || v.includes('balance')) sampleValues[v] = '$1,250.00';
      else if (v.includes('date')) sampleValues[v] = new Date().toLocaleDateString();
      else if (v.includes('link') || v.includes('url')) sampleValues[v] = 'https://example.com/action';
      else if (v.includes('code')) sampleValues[v] = 'ABC123';
      else if (v.includes('profit')) sampleValues[v] = '$150.00';
      else if (v.includes('product')) sampleValues[v] = 'MOIL10';
      else if (v.includes('direction')) sampleValues[v] = 'BUY';
      else if (v.includes('time')) sampleValues[v] = '14:00 PHT';
      else sampleValues[v] = `Sample ${v}`;
    });
    setTestVariableValues(sampleValues);
    setTestEmailAddress(user?.email || '');
    setTestEmailDialogOpen(true);
  };

  // Replace variables in template with actual values
  const getPreviewContent = (content, variables = {}) => {
    let result = content;
    Object.entries(variables).forEach(([key, value]) => {
      result = result.replace(new RegExp(`\\{\\{${key}\\}\\}`, 'g'), value);
    });
    return result;
  };

  // Send test email
  const handleSendTestEmail = async () => {
    if (!editingTemplate || !testEmailAddress) return;
    
    setSendingTestEmail(true);
    try {
      const processedSubject = getPreviewContent(editingTemplate.subject, testVariableValues);
      const processedBody = getPreviewContent(editingTemplate.body, testVariableValues);
      
      await settingsAPI.sendTestEmail({
        to: testEmailAddress,
        subject: processedSubject,
        body: processedBody,
        template_type: editingTemplate.type
      });
      toast.success('Test email sent successfully!');
      setTestEmailDialogOpen(false);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to send test email');
    } finally {
      setSendingTestEmail(false);
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

  const toggleKeyVisibility = (key) => {
    setShowKeys(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const maskValue = (value) => {
    if (!value) return '';
    if (value.length <= 8) return '••••••••';
    return value.slice(0, 4) + '••••••••' + value.slice(-4);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Settings className="w-6 h-6" /> Platform Settings
        </h1>
        <Button onClick={handleSave} className="btn-primary gap-2" disabled={saving} data-testid="save-settings-button">
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

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-8 bg-zinc-900/50 border border-zinc-800 rounded-lg p-1">
          <TabsTrigger 
            value="seo" 
            className="data-[state=active]:bg-blue-500 data-[state=active]:text-white rounded-md text-xs sm:text-sm"
            data-testid="tab-seo"
          >
            <Globe className="w-4 h-4 mr-1 sm:mr-2" /> <span className="hidden sm:inline">SEO</span>
          </TabsTrigger>
          <TabsTrigger 
            value="branding" 
            className="data-[state=active]:bg-blue-500 data-[state=active]:text-white rounded-md text-xs sm:text-sm"
            data-testid="tab-branding"
          >
            <Image className="w-4 h-4 mr-1 sm:mr-2" /> <span className="hidden sm:inline">Branding</span>
          </TabsTrigger>
          <TabsTrigger 
            value="ui" 
            className="data-[state=active]:bg-blue-500 data-[state=active]:text-white rounded-md text-xs sm:text-sm"
            data-testid="tab-ui"
          >
            <Palette className="w-4 h-4 mr-1 sm:mr-2" /> <span className="hidden sm:inline">UI</span>
          </TabsTrigger>
          <TabsTrigger 
            value="integrations" 
            className="data-[state=active]:bg-blue-500 data-[state=active]:text-white rounded-md text-xs sm:text-sm"
            data-testid="tab-integrations"
          >
            <Plug className="w-4 h-4 mr-1 sm:mr-2" /> <span className="hidden sm:inline">API</span>
          </TabsTrigger>
          <TabsTrigger 
            value="links" 
            className="data-[state=active]:bg-blue-500 data-[state=active]:text-white rounded-md text-xs sm:text-sm"
            data-testid="tab-links"
          >
            <ExternalLink className="w-4 h-4 mr-1 sm:mr-2" /> <span className="hidden sm:inline">Links</span>
          </TabsTrigger>
          <TabsTrigger 
            value="emails" 
            className="data-[state=active]:bg-blue-500 data-[state=active]:text-white rounded-md text-xs sm:text-sm"
            data-testid="tab-emails"
          >
            <Mail className="w-4 h-4 mr-1 sm:mr-2" /> <span className="hidden sm:inline">Emails</span>
          </TabsTrigger>
          <TabsTrigger 
            value="holidays" 
            className="data-[state=active]:bg-emerald-500 data-[state=active]:text-white rounded-md text-xs sm:text-sm"
            data-testid="tab-holidays"
          >
            <TreePine className="w-4 h-4 mr-1 sm:mr-2" /> <span className="hidden sm:inline">Holidays</span>
          </TabsTrigger>
          <TabsTrigger 
            value="maintenance" 
            className="data-[state=active]:bg-amber-500 data-[state=active]:text-white rounded-md text-xs sm:text-sm"
            data-testid="tab-maintenance"
          >
            <Wrench className="w-4 h-4 mr-1 sm:mr-2" /> <span className="hidden sm:inline">Maint.</span>
          </TabsTrigger>
        </TabsList>

        {/* SEO & Meta Tab */}
        <TabsContent value="seo" className="mt-6">
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
                <p className="text-xs text-zinc-500 mt-1">Used for SEO and social sharing</p>
              </div>
              <div>
                <Label className="text-zinc-300">OG Image URL (Social Sharing)</Label>
                <Input
                  value={settings.og_image_url}
                  onChange={(e) => setSettings({ ...settings, og_image_url: e.target.value })}
                  placeholder="https://example.com/og-image.png"
                  className="input-dark mt-1"
                  data-testid="og-image-input"
                />
                <p className="text-xs text-zinc-500 mt-1">Image displayed when sharing on social media</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Branding Tab */}
        <TabsContent value="branding" className="mt-6">
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
        </TabsContent>

        {/* UI Customization Tab */}
        <TabsContent value="ui" className="mt-6 space-y-6">
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
                      value={settings.primary_color}
                      onChange={(e) => setSettings({ ...settings, primary_color: e.target.value })}
                      className="w-12 h-10 rounded cursor-pointer bg-transparent border border-zinc-700"
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
                      className="w-12 h-10 rounded cursor-pointer bg-transparent border border-zinc-700"
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
        </TabsContent>

        {/* Integrations Tab */}
        <TabsContent value="integrations" className="mt-6 space-y-6">
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
        </TabsContent>

        {/* Custom Links Tab */}
        <TabsContent value="links" className="mt-6 space-y-6">
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
        </TabsContent>

        {/* Email Templates Tab */}
        <TabsContent value="emails" className="mt-6">
          <Card className="glass-card">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <FileText className="w-5 h-5 text-cyan-400" /> Email Templates
              </CardTitle>
              <p className="text-sm text-zinc-500">Customize email templates for notifications and communications</p>
            </CardHeader>
            <CardContent>
              {emailTemplates.length === 0 ? (
                <div className="text-center py-8">
                  <Mail className="w-12 h-12 text-zinc-600 mx-auto mb-3" />
                  <p className="text-zinc-500">No email templates configured</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Template List */}
                  <div className="space-y-3 max-h-[500px] overflow-y-auto">
                    {emailTemplates.map((template) => (
                      <div 
                        key={template.type}
                        className={`p-4 rounded-lg border transition-all cursor-pointer ${
                          selectedTemplate?.type === template.type 
                            ? 'bg-blue-500/10 border-blue-500/30' 
                            : 'bg-zinc-900/50 border-zinc-800 hover:border-zinc-700'
                        }`}
                        onClick={() => {
                          setSelectedTemplate(template);
                          setEditingTemplate({ ...template });
                        }}
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-white font-medium capitalize">
                              {template.type.replace(/_/g, ' ')}
                            </p>
                            <p className="text-xs text-zinc-500 mt-0.5 truncate max-w-[200px]">{template.subject}</p>
                          </div>
                          <Button 
                            variant="ghost" 
                            size="sm"
                            className="text-blue-400 hover:text-blue-300 shrink-0"
                          >
                            Edit
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Edit Template Panel */}
                  <div className="lg:border-l lg:border-zinc-800 lg:pl-6">
                    {editingTemplate ? (
                      <div className="space-y-4">
                        <div className="flex items-center justify-between">
                          <h3 className="text-white font-medium capitalize">
                            Edit: {editingTemplate.type.replace(/_/g, ' ')}
                          </h3>
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            onClick={() => {
                              setEditingTemplate(null);
                              setSelectedTemplate(null);
                            }}
                            className="text-zinc-400"
                          >
                            Close
                          </Button>
                        </div>

                        <div>
                          <Label className="text-zinc-300">Subject Line</Label>
                          <Input
                            value={editingTemplate.subject}
                            onChange={(e) => setEditingTemplate({ ...editingTemplate, subject: e.target.value })}
                            className="input-dark mt-1"
                          />
                        </div>

                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <Label className="text-zinc-300">Email Body</Label>
                            <div className="flex items-center gap-1 bg-zinc-800 rounded-lg p-0.5">
                              <button
                                type="button"
                                onClick={() => setEditorMode('code')}
                                className={`px-2 py-1 text-xs rounded transition-colors flex items-center gap-1 ${
                                  editorMode === 'code' 
                                    ? 'bg-blue-500 text-white' 
                                    : 'text-zinc-400 hover:text-white'
                                }`}
                              >
                                <Code className="w-3 h-3" /> Edit
                              </button>
                              <button
                                type="button"
                                onClick={() => setEditorMode('preview')}
                                className={`px-2 py-1 text-xs rounded transition-colors flex items-center gap-1 ${
                                  editorMode === 'preview' 
                                    ? 'bg-blue-500 text-white' 
                                    : 'text-zinc-400 hover:text-white'
                                }`}
                              >
                                <EyePreview className="w-3 h-3" /> Preview
                              </button>
                            </div>
                          </div>
                          
                          {editorMode === 'preview' ? (
                            <div className="p-4 rounded-lg bg-white text-black min-h-[250px] overflow-auto border border-zinc-700">
                              <div 
                                className="prose prose-sm max-w-none"
                                style={{ whiteSpace: 'pre-wrap', fontFamily: 'system-ui, -apple-system, sans-serif' }}
                              >
                                {getPreviewContent(editingTemplate.body, testVariableValues).split('\n').map((line, i) => (
                                  <p key={i} className="mb-2">{line || '\u00A0'}</p>
                                ))}
                              </div>
                              <p className="text-xs text-zinc-500 mt-3 italic">Variables are replaced with sample values. Click &quot;Test&quot; to customize values.</p>
                            </div>
                          ) : (
                            <Textarea
                              value={editingTemplate.body}
                              onChange={(e) => setEditingTemplate({ ...editingTemplate, body: e.target.value })}
                              className="input-dark min-h-[250px] font-mono text-sm"
                              rows={12}
                            />
                          )}
                          <p className="text-xs text-zinc-500 mt-1">Use {`{{variable}}`} syntax for dynamic content</p>
                        </div>

                        {editingTemplate.variables?.length > 0 && (
                          <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20">
                            <p className="text-xs text-blue-400 mb-2">Available Variables:</p>
                            <div className="flex flex-wrap gap-2">
                              {editingTemplate.variables.map((v) => (
                                <code key={v} className="px-2 py-1 rounded bg-zinc-800 text-xs text-zinc-300 cursor-pointer hover:bg-zinc-700" onClick={() => {
                                  // Insert variable at cursor or append
                                  setEditingTemplate({
                                    ...editingTemplate,
                                    body: editingTemplate.body + `{{${v}}}`
                                  });
                                }}>
                                  {`{{${v}}}`}
                                </code>
                              ))}
                            </div>
                          </div>
                        )}

                        <div className="flex gap-2">
                          <Button 
                            onClick={handleSaveTemplate}
                            disabled={savingTemplate}
                            className="btn-primary flex-1"
                          >
                            {savingTemplate ? (
                              <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Saving...</>
                            ) : (
                              <><CheckCircle2 className="w-4 h-4 mr-2" /> Save Template</>
                            )}
                          </Button>
                          <Button 
                            onClick={handleOpenTestEmail}
                            variant="outline"
                            className="border-cyan-500/30 text-cyan-400 hover:bg-cyan-500/10"
                            data-testid="send-test-email-btn"
                          >
                            <Send className="w-4 h-4 mr-2" /> Test
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <div className="flex items-center justify-center h-full min-h-[300px] text-center">
                        <div>
                          <FileText className="w-12 h-12 text-zinc-700 mx-auto mb-3" />
                          <p className="text-zinc-500">Select a template to edit</p>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
          
          {/* Test Email Dialog */}
          <Dialog open={testEmailDialogOpen} onOpenChange={setTestEmailDialogOpen}>
            <DialogContent className="bg-zinc-900 border-zinc-800 max-w-lg">
              <DialogHeader>
                <DialogTitle className="text-white flex items-center gap-2">
                  <Send className="w-5 h-5 text-cyan-400" /> Send Test Email
                </DialogTitle>
              </DialogHeader>
              
              <div className="space-y-4 py-4">
                <div>
                  <Label className="text-zinc-300">Recipient Email</Label>
                  <Input
                    type="email"
                    value={testEmailAddress}
                    onChange={(e) => setTestEmailAddress(e.target.value)}
                    placeholder="Enter email address"
                    className="input-dark mt-1"
                    data-testid="test-email-address-input"
                  />
                </div>
                
                {editingTemplate?.variables?.length > 0 && (
                  <div className="space-y-3">
                    <Label className="text-zinc-300">Variable Values</Label>
                    <p className="text-xs text-zinc-500">Customize the sample values for variables:</p>
                    <div className="max-h-[200px] overflow-y-auto space-y-2 pr-2">
                      {editingTemplate.variables.map((v) => (
                        <div key={v} className="flex items-center gap-2">
                          <code className="px-2 py-1 bg-zinc-800 rounded text-xs text-cyan-400 min-w-[100px]">{`{{${v}}}`}</code>
                          <Input
                            value={testVariableValues[v] || ''}
                            onChange={(e) => setTestVariableValues(prev => ({ ...prev, [v]: e.target.value }))}
                            className="input-dark text-sm"
                            placeholder={`Value for ${v}`}
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                <div>
                  <Label className="text-zinc-300 mb-2 block">Preview</Label>
                  <div className="p-3 rounded-lg bg-zinc-800/50 border border-zinc-700">
                    <p className="text-sm text-white font-medium mb-2">
                      Subject: {editingTemplate ? getPreviewContent(editingTemplate.subject, testVariableValues) : ''}
                    </p>
                    <div className="text-xs text-zinc-400 whitespace-pre-wrap max-h-[150px] overflow-y-auto">
                      {editingTemplate ? getPreviewContent(editingTemplate.body, testVariableValues) : ''}
                    </div>
                  </div>
                </div>
              </div>
              
              <DialogFooter>
                <Button 
                  variant="outline" 
                  onClick={() => setTestEmailDialogOpen(false)}
                  className="border-zinc-700 text-zinc-300"
                >
                  Cancel
                </Button>
                <Button 
                  onClick={handleSendTestEmail}
                  disabled={sendingTestEmail || !testEmailAddress}
                  className="btn-primary"
                  data-testid="confirm-send-test-email-btn"
                >
                  {sendingTestEmail ? (
                    <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Sending...</>
                  ) : (
                    <><Send className="w-4 h-4 mr-2" /> Send Test Email</>
                  )}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
          
          {/* Email History Card */}
          <Card className="glass-card mt-6">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-white flex items-center gap-2">
                    <Mail className="w-5 h-5 text-blue-400" /> Email History
                  </CardTitle>
                  <p className="text-sm text-zinc-500">View sent email status and delivery logs</p>
                </div>
                {isMasterAdmin() && emailHistory.length > 0 && (
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={handleClearEmailHistory}
                    disabled={clearingHistory}
                    className="text-red-400 border-red-400/30 hover:bg-red-400/10"
                    data-testid="clear-email-history"
                  >
                    {clearingHistory ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <><Trash2 className="w-4 h-4 mr-1" /> Clear History</>
                    )}
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {emailHistoryLoading ? (
                <div className="flex justify-center py-8">
                  <Loader2 className="w-8 h-8 animate-spin text-blue-400" />
                </div>
              ) : emailHistory.length === 0 ? (
                <div className="text-center py-8">
                  <Mail className="w-12 h-12 text-zinc-600 mx-auto mb-3" />
                  <p className="text-zinc-500">No emails sent yet</p>
                </div>
              ) : (
                <>
                  <div className="overflow-x-auto">
                    <table className="w-full data-table text-sm">
                      <thead>
                        <tr>
                          <th>Status</th>
                          <th>Recipient</th>
                          <th>Subject</th>
                          <th>Type</th>
                          <th>Sent At</th>
                        </tr>
                      </thead>
                      <tbody>
                        {emailHistory.map((email) => (
                          <tr key={email.id || email.email_id}>
                            <td>
                              <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs ${
                                email.status === 'sent' || email.status === 'success' 
                                  ? 'bg-emerald-500/20 text-emerald-400' 
                                  : email.status === 'failed' || email.status === 'error'
                                  ? 'bg-red-500/20 text-red-400'
                                  : 'bg-amber-500/20 text-amber-400'
                              }`}>
                                {email.status === 'sent' || email.status === 'success' ? (
                                  <CheckCircle2 className="w-3 h-3" />
                                ) : email.status === 'failed' || email.status === 'error' ? (
                                  <XCircle className="w-3 h-3" />
                                ) : (
                                  <Loader2 className="w-3 h-3" />
                                )}
                                {email.status}
                              </span>
                            </td>
                            <td className="font-mono text-xs text-zinc-400 max-w-[150px] truncate">
                              {email.recipient || email.to_email}
                            </td>
                            <td className="max-w-[200px] truncate">
                              {email.subject}
                            </td>
                            <td className="text-zinc-500 text-xs capitalize">
                              {(email.template_type || email.type || 'general').replace(/_/g, ' ')}
                            </td>
                            <td className="font-mono text-xs text-zinc-500">
                              {new Date(email.sent_at || email.created_at).toLocaleString()}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  
                  {/* Pagination */}
                  {emailHistoryTotal > 20 && (
                    <div className="flex justify-between items-center mt-4 pt-4 border-t border-zinc-800">
                      <p className="text-sm text-zinc-500">
                        Showing {((emailHistoryPage - 1) * 20) + 1} - {Math.min(emailHistoryPage * 20, emailHistoryTotal)} of {emailHistoryTotal}
                      </p>
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          disabled={emailHistoryPage <= 1}
                          onClick={() => loadEmailHistory(emailHistoryPage - 1)}
                        >
                          Previous
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          disabled={emailHistoryPage * 20 >= emailHistoryTotal}
                          onClick={() => loadEmailHistory(emailHistoryPage + 1)}
                        >
                          Next
                        </Button>
                      </div>
                    </div>
                  )}
                </>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Maintenance Tab */}
        <TabsContent value="maintenance" className="mt-6 space-y-6">
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
                  value={settings.maintenance_message}
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
        </TabsContent>
      </Tabs>
    </div>
  );
};
