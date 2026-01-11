import React, { useState, useEffect } from 'react';
import { settingsAPI } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import { 
  Settings, Upload, Globe, Image, Palette, RefreshCw, Crown, 
  Plug, Eye, EyeOff, Mail, Cloud, Heart, Key, CheckCircle2,
  FileText, Zap, XCircle, Loader2, Code, Type
} from 'lucide-react';
import ReactQuill from 'react-quill';
import 'react-quill/dist/quill.snow.css';

export const AdminSettingsPage = () => {
  const { isMasterAdmin, isSuperAdmin } = useAuth();
  const [settings, setSettings] = useState({
    site_title: 'CrossCurrent Finance Center',
    site_description: 'Trading profit management platform',
    favicon_url: '',
    logo_url: '',
    og_image_url: '',
    primary_color: '#3B82F6',
    accent_color: '#06B6D4',
    hide_emergent_badge: false,
    // Integration API Keys
    emailit_api_key: '',
    cloudinary_cloud_name: '',
    cloudinary_api_key: '',
    cloudinary_api_secret: '',
    heartbeat_api_key: '',
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('seo');
  
  // Email templates state
  const [emailTemplates, setEmailTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [savingTemplate, setSavingTemplate] = useState(false);
  const [editorMode, setEditorMode] = useState('wysiwyg'); // 'wysiwyg' or 'code'
  
  // Integration test states
  const [testingEmailit, setTestingEmailit] = useState(false);
  const [testingCloudinary, setTestingCloudinary] = useState(false);
  const [testingHeartbeat, setTestingHeartbeat] = useState(false);
  const [testResults, setTestResults] = useState({});
  
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
        <TabsList className="grid w-full grid-cols-5 bg-zinc-900/50 border border-zinc-800 rounded-lg p-1">
          <TabsTrigger 
            value="seo" 
            className="data-[state=active]:bg-blue-500 data-[state=active]:text-white rounded-md"
            data-testid="tab-seo"
          >
            <Globe className="w-4 h-4 mr-2" /> SEO & Meta
          </TabsTrigger>
          <TabsTrigger 
            value="branding" 
            className="data-[state=active]:bg-blue-500 data-[state=active]:text-white rounded-md"
            data-testid="tab-branding"
          >
            <Image className="w-4 h-4 mr-2" /> Branding
          </TabsTrigger>
          <TabsTrigger 
            value="ui" 
            className="data-[state=active]:bg-blue-500 data-[state=active]:text-white rounded-md"
            data-testid="tab-ui"
          >
            <Palette className="w-4 h-4 mr-2" /> UI
          </TabsTrigger>
          <TabsTrigger 
            value="integrations" 
            className="data-[state=active]:bg-blue-500 data-[state=active]:text-white rounded-md"
            data-testid="tab-integrations"
          >
            <Plug className="w-4 h-4 mr-2" /> Integrations
          </TabsTrigger>
          <TabsTrigger 
            value="emails" 
            className="data-[state=active]:bg-blue-500 data-[state=active]:text-white rounded-md"
            data-testid="tab-emails"
          >
            <Mail className="w-4 h-4 mr-2" /> Emails
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
        <TabsContent value="ui" className="mt-6">
          <Card className="glass-card">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Palette className="w-5 h-5 text-cyan-400" /> UI Customization
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
                                onClick={() => setEditorMode('wysiwyg')}
                                className={`px-2 py-1 text-xs rounded transition-colors flex items-center gap-1 ${
                                  editorMode === 'wysiwyg' 
                                    ? 'bg-blue-500 text-white' 
                                    : 'text-zinc-400 hover:text-white'
                                }`}
                              >
                                <Type className="w-3 h-3" /> Visual
                              </button>
                              <button
                                type="button"
                                onClick={() => setEditorMode('code')}
                                className={`px-2 py-1 text-xs rounded transition-colors flex items-center gap-1 ${
                                  editorMode === 'code' 
                                    ? 'bg-blue-500 text-white' 
                                    : 'text-zinc-400 hover:text-white'
                                }`}
                              >
                                <Code className="w-3 h-3" /> Code
                              </button>
                            </div>
                          </div>
                          
                          {editorMode === 'wysiwyg' ? (
                            <div className="email-editor-wrapper">
                              <ReactQuill
                                theme="snow"
                                value={editingTemplate.body}
                                onChange={(content) => setEditingTemplate({ ...editingTemplate, body: content })}
                                modules={{
                                  toolbar: [
                                    [{ 'header': [1, 2, 3, false] }],
                                    ['bold', 'italic', 'underline', 'strike'],
                                    [{ 'color': [] }, { 'background': [] }],
                                    [{ 'list': 'ordered'}, { 'list': 'bullet' }],
                                    [{ 'align': [] }],
                                    ['link'],
                                    ['clean']
                                  ]
                                }}
                                className="bg-zinc-900 rounded-lg border border-zinc-700"
                                style={{ minHeight: '250px' }}
                              />
                              <style>{`
                                .email-editor-wrapper .ql-toolbar {
                                  background: #27272a;
                                  border-color: #3f3f46;
                                  border-radius: 8px 8px 0 0;
                                }
                                .email-editor-wrapper .ql-container {
                                  background: #18181b;
                                  border-color: #3f3f46;
                                  border-radius: 0 0 8px 8px;
                                  font-size: 14px;
                                  min-height: 200px;
                                }
                                .email-editor-wrapper .ql-editor {
                                  color: #e4e4e7;
                                  min-height: 200px;
                                }
                                .email-editor-wrapper .ql-editor.ql-blank::before {
                                  color: #71717a;
                                }
                                .email-editor-wrapper .ql-stroke {
                                  stroke: #a1a1aa;
                                }
                                .email-editor-wrapper .ql-fill {
                                  fill: #a1a1aa;
                                }
                                .email-editor-wrapper .ql-picker {
                                  color: #a1a1aa;
                                }
                                .email-editor-wrapper .ql-picker-options {
                                  background: #27272a;
                                  border-color: #3f3f46;
                                }
                                .email-editor-wrapper button:hover .ql-stroke,
                                .email-editor-wrapper .ql-picker:hover .ql-stroke {
                                  stroke: #fff;
                                }
                                .email-editor-wrapper button:hover .ql-fill,
                                .email-editor-wrapper .ql-picker:hover .ql-fill {
                                  fill: #fff;
                                }
                                .email-editor-wrapper .ql-active .ql-stroke {
                                  stroke: #3b82f6;
                                }
                                .email-editor-wrapper .ql-active .ql-fill {
                                  fill: #3b82f6;
                                }
                              `}</style>
                            </div>
                          ) : (
                            <Textarea
                              value={editingTemplate.body}
                              onChange={(e) => setEditingTemplate({ ...editingTemplate, body: e.target.value })}
                              className="input-dark mt-1 min-h-[250px] font-mono text-sm"
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

                        <Button 
                          onClick={handleSaveTemplate}
                          disabled={savingTemplate}
                          className="btn-primary w-full"
                        >
                          {savingTemplate ? (
                            <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Saving...</>
                          ) : (
                            <><CheckCircle2 className="w-4 h-4 mr-2" /> Save Template</>
                          )}
                        </Button>
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
        </TabsContent>
      </Tabs>
    </div>
  );
};
