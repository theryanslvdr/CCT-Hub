import React, { useState, useEffect, createContext, useContext } from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { settingsAPI } from '@/lib/api';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { Footer } from './Footer';
import { MobileBottomNav } from './MobileBottomNav';
import { MobileMenu } from './MobileMenu';
import { cn } from '@/lib/utils';
import { Toaster } from '@/components/ui/sonner';
import { OnboardingTour, useOnboarding } from '@/components/OnboardingTour';
import { ContentProtection } from '@/components/ContentProtection';
import { NoticeBanner } from '@/components/NoticeBanner';
import { PromotionPopup } from '@/components/PromotionPopup';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { AlertTriangle, Settings, ExternalLink, X, Info, CheckCircle, Bell } from 'lucide-react';

// API Key Status Context - to share missing keys info across the app
export const ApiKeyStatusContext = createContext({ missingKeys: [], hasMissingKeys: false });
export const useApiKeyStatus = () => useContext(ApiKeyStatusContext);

// Announcement Banner Component
const AnnouncementBanner = ({ announcements, onDismiss }) => {
  if (!announcements || announcements.length === 0) return null;
  
  const activeAnnouncements = announcements.filter(a => a.active);
  if (activeAnnouncements.length === 0) return null;

  // Sort: sticky first, then by created_at
  const sortedAnnouncements = [...activeAnnouncements].sort((a, b) => {
    if (a.sticky && !b.sticky) return -1;
    if (!a.sticky && b.sticky) return 1;
    return new Date(b.created_at) - new Date(a.created_at);
  });

  const getTypeStyles = (type) => {
    switch (type) {
      case 'warning':
        return 'bg-amber-500/20 border-amber-500/50 text-amber-200';
      case 'success':
        return 'bg-emerald-500/20 border-emerald-500/50 text-emerald-200';
      default:
        return 'bg-orange-500/10 border-orange-500/30 text-orange-200';
    }
  };

  const getIcon = (type) => {
    switch (type) {
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-amber-400" />;
      case 'success':
        return <CheckCircle className="w-4 h-4 text-emerald-400" />;
      default:
        return <Info className="w-4 h-4 text-orange-400" />;
    }
  };

  return (
    <div className="space-y-2 mb-4">
      {sortedAnnouncements.map((announcement) => (
        <div
          key={announcement.id}
          className={`px-4 py-3 rounded-lg border ${getTypeStyles(announcement.type)} flex items-start justify-between gap-3`}
          data-testid={`announcement-${announcement.id}`}
        >
          <div className="flex items-start gap-3 flex-1">
            {getIcon(announcement.type)}
            <div className="flex-1">
              {announcement.title && (
                <p className="font-medium text-white text-sm">{announcement.title}</p>
              )}
              <p className="text-sm">{announcement.message}</p>
              {announcement.link_url && (
                <a
                  href={announcement.link_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-xs mt-1 text-orange-400 hover:text-orange-300 hover:underline"
                >
                  {announcement.link_text || 'Learn more'} <ExternalLink className="w-3 h-3" />
                </a>
              )}
            </div>
          </div>
          {!announcement.sticky && (
            <button
              onClick={() => onDismiss(announcement.id)}
              className="text-zinc-400 hover:text-white transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      ))}
    </div>
  );
};

const pagesTitles = {
  '/dashboard': 'Dashboard',
  '/profit-tracker': 'Profit Tracker',
  '/trade-monitor': 'Trade Monitor',
  '/goals': 'Profit Planner',
  '/debt': 'Debt Management',
  '/profile': 'Profile Settings',
  '/admin/signals': 'Trading Signals',
  '/admin/members': 'Member Management',
  '/admin/api-center': 'API Center',
  '/admin/settings': 'Platform Settings',
  '/admin/analytics': 'Team Analytics',
  '/admin/transactions': 'Team Transactions',
  '/admin/referrals': 'Referral Network',
  '/admin/quizzes': 'Quiz Manager',
  '/admin/ai-training': 'AI Training Center',
  '/admin/dashboard': 'Admin Dashboard',
  '/ai-assistant': 'AI Assistant',
  '/member': 'Member Profile',
  '/profit-planner': 'Profit Planner',
  '/debt-management': 'Debt Management',
};

export const DashboardLayout = () => {
  const { isAuthenticated, loading, isMasterAdmin, user } = useAuth();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [platformSettings, setPlatformSettings] = useState(null);
  const [missingKeys, setMissingKeys] = useState([]);
  const [showMissingKeysModal, setShowMissingKeysModal] = useState(false);
  const [announcements, setAnnouncements] = useState([]);
  const [dismissedAnnouncements, setDismissedAnnouncements] = useState(() => {
    // Load dismissed announcements from localStorage
    const saved = localStorage.getItem('dismissedAnnouncements');
    return saved ? JSON.parse(saved) : [];
  });
  const location = useLocation();
  const { showTour, completeTour, resetTour } = useOnboarding();

  const handleDismissAnnouncement = (id) => {
    const newDismissed = [...dismissedAnnouncements, id];
    setDismissedAnnouncements(newDismissed);
    localStorage.setItem('dismissedAnnouncements', JSON.stringify(newDismissed));
  };

  const visibleAnnouncements = announcements.filter(
    a => a.active && !dismissedAnnouncements.includes(a.id)
  );

  // Load platform settings and check for missing API keys
  useEffect(() => {
    const loadSettings = async () => {
      try {
        const res = await settingsAPI.getPlatform();
        setPlatformSettings(res.data);
        
        // Load announcements
        if (res.data?.announcements) {
          setAnnouncements(res.data.announcements);
        }
        
        // Apply favicon
        if (res.data?.favicon_url) {
          const favicon = document.querySelector("link[rel~='icon']") || document.createElement('link');
          favicon.rel = 'icon';
          favicon.href = res.data.favicon_url;
          document.head.appendChild(favicon);
        }
        
        // Apply title
        if (res.data?.site_title) {
          document.title = res.data.site_title;
        }
        
        // Check for missing API keys (only show modal for Master Admin)
        const missing = [];
        if (!res.data?.heartbeat_api_key) missing.push({ name: 'Heartbeat', description: 'Required for community member verification' });
        if (!res.data?.emailit_api_key) missing.push({ name: 'Emailit', description: 'Required for sending notification emails' });
        if (!res.data?.cloudinary_cloud_name || !res.data?.cloudinary_api_key || !res.data?.cloudinary_api_secret) {
          missing.push({ name: 'Cloudinary', description: 'Required for file uploads and image storage' });
        }
        
        setMissingKeys(missing);
        
        // Show modal if there are missing keys and user is Master Admin
        if (missing.length > 0 && isMasterAdmin()) {
          setShowMissingKeysModal(true);
        }
      } catch (error) {
        console.error('Failed to load platform settings');
      }
    };
    
    if (isAuthenticated) {
      loadSettings();
    }
  }, [isAuthenticated, isMasterAdmin]);

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-orange-500/20 border-t-orange-500 rounded-full animate-spin" />
          <p className="text-zinc-400">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  const currentTitle = pagesTitles[location.pathname] || 'CrossCurrent Finance';
  const hideEmergentBadge = platformSettings?.hide_emergent_badge === true;

  return (
    <ApiKeyStatusContext.Provider value={{ missingKeys, hasMissingKeys: missingKeys.length > 0 }}>
      <div className="min-h-screen flex flex-col relative" style={{ background: '#080808' }}>
        {/* Ambient glow blobs */}
        <div className="fixed top-0 right-0 w-64 h-64 rounded-full bg-orange-500/10 blur-[120px] pointer-events-none z-0" />
        <div className="fixed bottom-0 left-0 w-64 h-64 rounded-full bg-white/5 blur-[100px] pointer-events-none z-0" />
        {/* Desktop Sidebar */}
        <div className="hidden md:block">
          <Sidebar
            isOpen={false}
            onClose={() => {}}
            collapsed={sidebarCollapsed}
            onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
            onShowTour={resetTour}
          />
        </div>
        
        {/* Mobile Full-Screen Menu */}
        <MobileMenu 
          isOpen={mobileMenuOpen} 
          onClose={() => setMobileMenuOpen(false)} 
        />
        
        <main className={cn(
          "flex-1 flex flex-col transition-all duration-300",
          "ml-0 lg:ml-16",
          !sidebarCollapsed && "lg:ml-64"
        )}>
          <Header
            title={currentTitle}
            onMenuClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          />
          
          <div className="flex-1 p-3 sm:p-4 md:p-6 overflow-x-hidden pb-20 md:pb-6">
            {/* Notice Banner (page-aware, admin-configurable) */}
            <NoticeBanner />
            
            {/* Announcements Banner */}
            <AnnouncementBanner 
              announcements={visibleAnnouncements} 
              onDismiss={handleDismissAnnouncement}
            />
            
            <Outlet />
          </div>
          
          {/* Persistent Footer - hidden on mobile when bottom nav is visible */}
          <div className="hidden md:block">
            <Footer />
          </div>
        </main>

        {/* Mobile Bottom Navigation */}
        <MobileBottomNav />

        <Toaster position="top-right" richColors />
        
        {/* Content Protection (copy/screenshot prevention) */}
        <ContentProtection
          enabled={platformSettings?.content_protection_enabled || false}
          userEmail={user?.email || ''}
          userName={user?.full_name || ''}
          customWatermark={platformSettings?.content_protection_watermark_custom || ''}
          showWatermark={platformSettings?.content_protection_watermark !== false}
          disableCopy={platformSettings?.content_protection_disable_copy !== false}
          disableRightClick={platformSettings?.content_protection_disable_rightclick !== false}
          disableShortcuts={platformSettings?.content_protection_disable_shortcuts !== false}
        />

        {/* Promotion Popup (admin-configurable, session/day frequency) */}
        <PromotionPopup />
        
        {/* Onboarding Tour */}
        <OnboardingTour isOpen={showTour} onClose={completeTour} />

        {/* Missing API Keys Modal - Only for Master Admin */}
        <Dialog open={showMissingKeysModal} onOpenChange={setShowMissingKeysModal}>
          <DialogContent className="bg-[#111111] border-amber-500/20 max-w-md">
            <DialogHeader>
              <DialogTitle className="text-amber-400 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5" /> Missing API Keys
              </DialogTitle>
              <DialogDescription className="text-zinc-500">
                Some integrations are not configured. The application may not work correctly without these API keys.
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-3 my-4">
              {missingKeys.map((key, index) => (
                <div key={index} className="p-3 rounded-lg bg-amber-500/5 border border-amber-500/15">
                  <p className="text-white font-medium">{key.name}</p>
                  <p className="text-xs text-zinc-500 mt-1">{key.description}</p>
                </div>
              ))}
            </div>
            
            <div className="flex gap-3">
              <Button 
                variant="outline" 
                onClick={() => setShowMissingKeysModal(false)}
                className="flex-1 btn-secondary"
              >
                Remind Me Later
              </Button>
              <Button 
                onClick={() => {
                  setShowMissingKeysModal(false);
                  window.location.href = '/admin/settings';
                }}
                className="flex-1 btn-primary gap-2"
              >
                <Settings className="w-4 h-4" /> Configure Now
              </Button>
            </div>
          </DialogContent>
        </Dialog>

        {/* Made with Emergent Badge - can be hidden via settings */}
        {!hideEmergentBadge && (
          <a
            href="https://emergentagent.com"
            target="_blank"
            rel="noopener noreferrer"
            className="fixed bottom-4 right-4 z-50 flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#111111]/90 border border-white/[0.06] text-xs text-zinc-500 hover:text-white hover:border-white/[0.12] transition-all backdrop-blur-sm"
            data-testid="emergent-badge"
          >
            <span>Made with</span>
            <span className="font-semibold text-orange-400">Emergent</span>
          </a>
        )}
      </div>
    </ApiKeyStatusContext.Provider>
  );
};
