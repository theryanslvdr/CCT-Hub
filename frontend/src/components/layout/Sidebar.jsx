import React, { useState, useEffect, useMemo } from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { settingsAPI, adminAPI, forumAPI } from '@/lib/api';
import { PWAInstallInstructions } from '@/lib/pwa';
import { 
  LayoutDashboard, TrendingUp, Activity, Target, CreditCard, 
  Settings, Users, BarChart3, Radio, Cog, Eye, EyeOff,
  FlaskConical, Crown, LogOut, User, ChevronUp, Wallet, Plug, Award,
  ChevronDown, UserCheck, Shield, ShieldCheck, Star, Sparkles, Loader2, Download, CheckSquare, Share2, Trophy, MessageSquare, Gauge, RotateCcw, GitBranch, HelpCircle, UserPlus, Bell, ShoppingBag, ChevronRight, Store
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger, DropdownMenuLabel,
} from '@/components/ui/dropdown-menu';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription,
} from '@/components/ui/dialog';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select';

export const Sidebar = ({ isOpen, onClose, collapsed = false }) => {
  const { user, isAdmin, isMasterAdmin, isSuperAdmin, canAccessHiddenFeatures, simulatedView, simulateMemberView, exitSimulation, logout } = useAuth();
  const [platformSettings, setPlatformSettings] = useState(null);
  const navigate = useNavigate();
  const location = useLocation();
  
  const [licenseeDialogOpen, setLicenseeDialogOpen] = useState(false);
  const [pwaInstructionsOpen, setPwaInstructionsOpen] = useState(false);
  const [selectedLicenseType, setSelectedLicenseType] = useState(null);
  const [licensees, setLicensees] = useState([]);
  const [loadingLicensees, setLoadingLicensees] = useState(false);
  const [selectedLicenseeId, setSelectedLicenseeId] = useState('');
  const [expandedCategory, setExpandedCategory] = useState(null);
  const [badgeCounts, setBadgeCounts] = useState({});

  useEffect(() => {
    const loadSettings = async () => {
      try {
        const res = await settingsAPI.getPlatform();
        setPlatformSettings(res.data);
      } catch {}
    };
    loadSettings();
  }, []);

  // Load badge counts periodically
  useEffect(() => {
    const loadBadges = async () => {
      try {
        const counts = {};
        if (isAdmin() && !simulatedView) {
          try {
            const cleanup = await adminAPI.getCleanupOverview();
            const d = cleanup.data;
            const adminTotal = (d?.pending_proofs || 0) + (d?.pending_registrations || 0);
            if (adminTotal > 0) counts.admin = adminTotal;
          } catch {}
        }
        // Forum new posts — count from last 24h
        try {
          const forum = await forumAPI.getPosts({ page: 1, limit: 1 });
          // Use total as a rough indicator; if > 0, show a dot
          if (forum.data?.total > 0) counts.forum = null; // dot only
        } catch {}
        setBadgeCounts(counts);
      } catch {}
    };
    loadBadges();
    const interval = setInterval(loadBadges, 120000); // every 2 min
    return () => clearInterval(interval);
  }, [isAdmin, simulatedView]);

  // Auto-expand category based on current route
  useEffect(() => {
    const path = location.pathname;
    if (['/', '/dashboard', '/profit-tracker', '/trade-monitor'].some(p => path.startsWith(p) && (p === path || p !== '/'))) {
      setExpandedCategory('core');
    } else if (['/habits', '/affiliate', '/my-team'].some(p => path.startsWith(p))) {
      setExpandedCategory('growth');
    } else if (['/my-rewards', '/store'].some(p => path.startsWith(p))) {
      setExpandedCategory('rewards');
    } else if (['/forum', '/ai-assistant'].some(p => path.startsWith(p))) {
      setExpandedCategory('community');
    } else if (['/profit-planner', '/debt-management'].some(p => path.startsWith(p))) {
      setExpandedCategory('tools');
    } else if (path.startsWith('/admin')) {
      setExpandedCategory('admin');
    } else if (['/licensee-account', '/family-accounts'].some(p => path.startsWith(p))) {
      setExpandedCategory('growth');
    }
  }, [location.pathname]);

  const handleLicenseeSimulationClick = async (licenseType) => {
    setSelectedLicenseType(licenseType);
    setLicenseeDialogOpen(true);
    setLoadingLicensees(true);
    setSelectedLicenseeId('');
    try {
      const [licensesRes, membersRes] = await Promise.all([
        adminAPI.getLicenses(),
        adminAPI.getMembers()
      ]);
      const activeLicenses = licensesRes.data.licenses?.filter(l => l.is_active && l.license_type === licenseType) || [];
      const members = membersRes.data.members || membersRes.data || [];
      const licenseesWithDetails = activeLicenses.map(license => {
        const member = members.find(m => m.id === license.user_id);
        const licenseeProfit = (license.current_amount || 0) - (license.starting_amount || 0);
        return {
          ...license,
          full_name: license.user_name || member?.full_name || 'Unknown User',
          email: license.user_email || member?.email || 'N/A',
          account_value: license.current_amount || member?.account_value || 0,
          lot_size: member?.lot_size || 0.01,
          total_deposits: license.starting_amount || member?.total_deposits || 0,
          total_profit: licenseeProfit,
          allowed_dashboards: member?.allowed_dashboards
        };
      });
      setLicensees(licenseesWithDetails);
    } catch { setLicensees([]); }
    setLoadingLicensees(false);
  };
  
  const handleSimulateLicensee = () => {
    if (selectedLicenseeId === 'dummy') {
      simulateMemberView({ role: 'member', license_type: selectedLicenseType, displayName: `${selectedLicenseType === 'honorary' ? 'Honorary' : selectedLicenseType === 'honorary_fa' ? 'Honorary FA' : 'Extended'} Licensee (Demo)`, accountValue: 5000, lotSize: 0.05, totalDeposits: 5000, totalProfit: 0, starting_amount: 5000, effective_start_date: new Date().toISOString().split('T')[0] });
    } else {
      const licensee = licensees.find(l => l.user_id === selectedLicenseeId);
      if (licensee) {
        simulateMemberView({ id: licensee.user_id, memberId: licensee.user_id, licenseId: licensee.id, full_name: licensee.full_name, account_value: licensee.account_value, lot_size: licensee.lot_size, total_deposits: licensee.total_deposits, total_profit: licensee.total_profit, starting_amount: licensee.starting_amount, allowed_dashboards: licensee.allowed_dashboards, license_type: selectedLicenseType, displayName: licensee.full_name, effective_start_date: licensee.effective_start_date || licensee.start_date });
      }
    }
    setLicenseeDialogOpen(false);
  };

  const isLicenseeView = simulatedView?.license_type || user?.license_type;
  const isHonoraryFa = (simulatedView?.license_type || user?.license_type) === 'honorary_fa';

  // Nav items definitions
  const allNavItems = useMemo(() => [
    { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard', id: 'dashboard', category: 'core' },
    { path: '/profit-tracker', icon: TrendingUp, label: 'Profit Tracker', id: 'profit_tracker', category: 'core' },
    { path: '/trade-monitor', icon: Activity, label: 'Trade Monitor', id: 'trade_monitor', category: 'core', hideForLicensee: true },
    { path: '/habits', icon: CheckSquare, label: 'Daily Habits', id: 'habits', category: 'growth', hideForLicensee: true },
    { path: '/affiliate', icon: Share2, label: 'Affiliate Center', id: 'affiliate', category: 'growth', hideForLicensee: true },
    { path: '/my-team', icon: Users, label: 'My Team', id: 'my_team', category: 'growth', hideForLicensee: true },
    { path: '/licensee-account', icon: Award, label: 'Deposit/Withdrawal', id: 'licensee_account', category: 'growth', licenseeOnly: true },
    { path: '/family-accounts', icon: Users, label: 'Family Accounts', id: 'family_accounts', category: 'growth', honoraryFaOnly: true },
    { path: '/my-rewards', icon: Star, label: 'My Rewards', id: 'my_rewards', category: 'rewards', hideForLicensee: true },
    { path: '/store', icon: ShoppingBag, label: 'Hub Store', id: 'store', category: 'rewards', hideForLicensee: true },
    { path: '/forum', icon: MessageSquare, label: 'Community Forum', id: 'forum', category: 'community', hideForLicensee: true },
    { path: '/ai-assistant', icon: Sparkles, label: 'AI Assistant', id: 'ai_assistant', category: 'community', hideForLicensee: true },
  ], []);

  const hiddenFeatures = [
    { path: '/profit-planner', icon: Target, label: 'Profit Planner', id: 'profit_planner' },
    { path: '/debt-management', icon: CreditCard, label: 'Debt Management', id: 'debt_management' },
  ];

  const adminNavItems = [
    { path: '/admin/dashboard', icon: BarChart3, label: 'Admin Dashboard' },
    { path: '/admin/members', icon: Users, label: 'Members' },
    { path: '/admin/signals', icon: Radio, label: 'Trading Signals' },
    { path: '/admin/analytics', icon: TrendingUp, label: 'Team Analytics' },
  ];

  const superAdminItems = [
    { path: '/admin/transactions', icon: Wallet, label: 'Transactions' },
    { path: '/admin/rewards', icon: Star, label: 'Rewards Admin' },
    { path: '/admin/referrals', icon: GitBranch, label: 'Referral Tree' },
    { path: '/admin/quizzes', icon: HelpCircle, label: 'Quiz Manager' },
    { path: '/admin/ai-training', icon: Sparkles, label: 'AI Training' },
  ];

  const masterAdminItems = [
    { path: '/admin/cleanup', icon: Shield, label: 'Admin Cleanup' },
    { path: '/admin/licenses', icon: Award, label: 'Licenses' },
    { path: '/admin/system-check', icon: Shield, label: 'System Check' },
    { path: '/admin/system-health', icon: Gauge, label: 'System Health' },
  ];

  const getVisibleItems = (category) => {
    const baseDashboards = simulatedView?.allowed_dashboards || user?.allowed_dashboards || [];
    const alwaysInclude = isLicenseeView
      ? ['dashboard', 'profile', 'my_rewards']
      : ['dashboard', 'profile', 'habits', 'affiliate', 'my_team', 'store', 'my_rewards', 'forum', 'ai_assistant'];
    const effectiveDashboards = [...new Set([...baseDashboards, ...alwaysInclude])];

    return allNavItems.filter(item => {
      if (item.category !== category) return false;
      if (item.hideForLicensee && isLicenseeView) return false;
      if (item.licenseeOnly && !isLicenseeView) return false;
      if (item.honoraryFaOnly && !isHonoraryFa) return false;
      if (isAdmin() && !simulatedView) return !item.licenseeOnly && !item.honoraryFaOnly;
      return effectiveDashboards.includes(item.id) || (item.licenseeOnly && isLicenseeView) || (item.honoraryFaOnly && isHonoraryFa);
    });
  };

  const categories = [
    { key: 'core', label: 'Core', icon: LayoutDashboard },
    { key: 'growth', label: 'Growth', icon: TrendingUp },
    { key: 'rewards', label: 'Rewards', icon: Star },
    { key: 'community', label: 'Community', icon: MessageSquare },
  ];

  const navLinkClass = ({ isActive }) => 
    `flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-200 ${
      isActive 
        ? 'text-white font-medium bg-[#1a1a1a] border border-orange-500/20' 
        : 'text-gray-500 hover:text-gray-300 hover:bg-white/[0.03] border border-transparent'
    }`;

  const hiddenNavLinkClass = ({ isActive }) => 
    `flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-200 ${
      isActive 
        ? 'bg-purple-500/10 text-purple-300 border border-purple-500/20' 
        : 'text-zinc-500 hover:text-purple-400 hover:bg-purple-500/5'
    }`;

  const handleNavClick = () => {
    if (window.innerWidth < 1024) onClose();
  };

  const handleLogout = () => { logout(); navigate('/login'); };
  const handleProfileClick = () => { navigate('/profile'); handleNavClick(); };
  const handleSettingsClick = () => { navigate('/admin/settings'); handleNavClick(); };
  const handleApiCenterClick = () => { navigate('/admin/api-center'); handleNavClick(); };

  const handlePurgeCache = async () => {
    try {
      if ('serviceWorker' in navigator) {
        const regs = await navigator.serviceWorker.getRegistrations();
        for (const r of regs) await r.unregister();
      }
      if ('caches' in window) {
        const names = await caches.keys();
        for (const n of names) await caches.delete(n);
      }
      const token = localStorage.getItem('access_token');
      const userStr = localStorage.getItem('user');
      localStorage.clear();
      sessionStorage.clear();
      if (token) localStorage.setItem('access_token', token);
      if (userStr) localStorage.setItem('user', userStr);
      window.location.reload(true);
    } catch { window.location.reload(true); }
  };

  const hasLogo = platformSettings?.logo_url;
  const hasFavicon = platformSettings?.favicon_url;

  const toggleCategory = (key) => {
    setExpandedCategory(prev => prev === key ? null : key);
  };

  const BadgeCount = ({ count }) => {
    if (count === undefined) return null;
    if (count === null) return <span className="w-2 h-2 rounded-full bg-orange-500 shrink-0" />;
    return (
      <span className="min-w-[18px] h-[18px] rounded-full bg-orange-500 text-[10px] text-white font-bold flex items-center justify-center px-1 shrink-0">
        {count > 99 ? '99+' : count}
      </span>
    );
  };

  const renderCategorySection = (cat) => {
    const items = getVisibleItems(cat.key);
    if (items.length === 0) return null;
    const isExpanded = expandedCategory === cat.key;
    const hasActivePath = items.some(i => location.pathname === i.path);

    return (
      <div key={cat.key} className="mb-0.5" data-testid={`nav-category-${cat.key}`}>
        <button
          onClick={() => toggleCategory(cat.key)}
          className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-left transition-all duration-200 ${
            hasActivePath && !isExpanded
              ? 'text-orange-400 bg-orange-500/[0.06]'
              : 'text-zinc-500 hover:text-zinc-300 hover:bg-white/[0.02]'
          }`}
          data-testid={`nav-toggle-${cat.key}`}
        >
          <cat.icon className="w-3.5 h-3.5" />
          {!collapsed && (
            <>
              <span className="text-[10px] uppercase tracking-[0.15em] font-semibold flex-1">{cat.label}</span>
              <ChevronRight className={`w-3 h-3 transition-transform duration-200 ${isExpanded ? 'rotate-90' : ''}`} />
            </>
          )}
        </button>
        <div className={`overflow-hidden transition-all duration-200 ${isExpanded ? 'max-h-[500px] opacity-100' : 'max-h-0 opacity-0'}`}>
          <div className="pl-1 space-y-0.5 py-0.5">
            {items.map(item => (
              <NavLink
                key={item.path}
                to={item.path}
                className={navLinkClass}
                onClick={handleNavClick}
                data-testid={`nav-${item.id}`}
                title={collapsed ? item.label : undefined}
              >
                <item.icon className="w-4 h-4" />
                {!collapsed && (
                  <>
                    <span className="text-sm flex-1">{item.label}</span>
                    {item.id === 'forum' && badgeCounts.forum !== undefined && <BadgeCount count={badgeCounts.forum} />}
                  </>
                )}
              </NavLink>
            ))}
          </div>
        </div>
      </div>
    );
  };

  return (
    <aside className={`sidebar ${isOpen ? 'open' : ''} ${collapsed ? 'sidebar-collapsed' : ''} flex flex-col bg-[#0d0d0d] border-r border-[#1f1f1f]`}>
      {/* Logo */}
      <div className="p-5 pb-4">
        <div className="flex items-center gap-3">
          {collapsed ? (
            hasFavicon ? (
              <img src={platformSettings.favicon_url} alt="Logo" className="w-9 h-9 rounded-lg object-contain" />
            ) : (
              <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-orange-500 to-amber-600 flex items-center justify-center">
                <TrendingUp className="w-5 h-5 text-white" />
              </div>
            )
          ) : (
            hasLogo ? (
              <img src={platformSettings.logo_url} alt="CrossCurrent" className="h-10 max-w-[180px] object-contain" />
            ) : (
              <>
                <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-orange-500 to-amber-600 flex items-center justify-center">
                  <TrendingUp className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h1 className="text-lg font-bold text-white">CrossCurrent</h1>
                  <p className="text-xs text-zinc-500">Finance Center</p>
                </div>
              </>
            )
          )}
        </div>
      </div>

      {/* Master Admin Simulation */}
      {isMasterAdmin() && !collapsed && (
        <div className="px-3 mb-3">
          {simulatedView ? (
            <div className="p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/30">
              <div className="flex items-center gap-2 text-amber-400 text-xs mb-2">
                <Eye className="w-3.5 h-3.5" />
                <span>Simulating: {simulatedView.displayName || simulatedView.role}</span>
              </div>
              <Button variant="outline" size="sm" onClick={exitSimulation} className="w-full h-8 text-xs text-amber-400 border-amber-500/30 hover:bg-amber-500/10">
                <EyeOff className="w-3.5 h-3.5 mr-1.5" /> Exit Simulation
              </Button>
            </div>
          ) : (
            <>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm" className="w-full h-8 text-xs text-zinc-400 border-white/[0.08] hover:bg-[#1a1a1a] justify-between">
                  <span className="flex items-center gap-1.5"><Eye className="w-3.5 h-3.5" /> Simulate View</span>
                  <ChevronDown className="w-3.5 h-3.5" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start" className="w-56 bg-[#0d0d0d] border-white/[0.08]">
                <DropdownMenuLabel className="text-zinc-500 text-xs">Role Simulation</DropdownMenuLabel>
                <DropdownMenuItem onClick={() => simulateMemberView({ role: 'member', displayName: 'Member' })} className="text-zinc-300 hover:bg-[#1a1a1a] cursor-pointer">
                  <User className="w-4 h-4 mr-2 text-orange-400" /> Member View
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => simulateMemberView({ role: 'basic_admin', displayName: 'Basic Admin' })} className="text-zinc-300 hover:bg-[#1a1a1a] cursor-pointer">
                  <UserCheck className="w-4 h-4 mr-2 text-green-400" /> Basic Admin View
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => simulateMemberView({ role: 'super_admin', displayName: 'Super Admin' })} className="text-zinc-300 hover:bg-[#1a1a1a] cursor-pointer">
                  <ShieldCheck className="w-4 h-4 mr-2 text-purple-400" /> Super Admin View
                </DropdownMenuItem>
                <DropdownMenuSeparator className="bg-zinc-700" />
                <DropdownMenuLabel className="text-zinc-500 text-xs">Licensee Simulation</DropdownMenuLabel>
                <DropdownMenuItem onClick={() => handleLicenseeSimulationClick('honorary')} className="text-zinc-300 hover:bg-[#1a1a1a] cursor-pointer">
                  <Star className="w-4 h-4 mr-2 text-amber-400" /> Honorary Licensee
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => handleLicenseeSimulationClick('honorary_fa')} className="text-zinc-300 hover:bg-[#1a1a1a] cursor-pointer">
                  <Users className="w-4 h-4 mr-2 text-orange-400" /> Honorary FA (Family)
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => handleLicenseeSimulationClick('extended')} className="text-zinc-300 hover:bg-[#1a1a1a] cursor-pointer">
                  <Sparkles className="w-4 h-4 mr-2 text-purple-400" /> Extended Licensee
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
            <Dialog open={licenseeDialogOpen} onOpenChange={setLicenseeDialogOpen}>
              <DialogContent className="bg-[#0d0d0d] border-white/[0.08] max-w-md">
                <DialogHeader>
                  <DialogTitle className="text-white flex items-center gap-2">
                    {selectedLicenseType === 'honorary' ? <Star className="w-5 h-5 text-amber-400" /> : selectedLicenseType === 'honorary_fa' ? <Users className="w-5 h-5 text-orange-400" /> : <Sparkles className="w-5 h-5 text-purple-400" />}
                    Simulate {selectedLicenseType === 'honorary' ? 'Honorary' : selectedLicenseType === 'honorary_fa' ? 'Honorary FA' : 'Extended'} Licensee
                  </DialogTitle>
                  <DialogDescription className="text-zinc-400">Choose how you want to simulate this licensee view.</DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-zinc-300">Simulation Mode</label>
                    <Select value={selectedLicenseeId} onValueChange={setSelectedLicenseeId}>
                      <SelectTrigger className="w-full bg-[#1a1a1a] border-white/[0.08] text-zinc-300"><SelectValue placeholder="Select simulation mode..." /></SelectTrigger>
                      <SelectContent className="bg-[#1a1a1a] border-white/[0.08]">
                        <SelectItem value="dummy" className="text-zinc-300 hover:bg-white/[0.08]">
                          <div className="flex flex-col"><span className="font-medium">Demo Mode (Dummy Values)</span><span className="text-xs text-zinc-500">Use placeholder data ($5,000 balance)</span></div>
                        </SelectItem>
                        {loadingLicensees ? (
                          <div className="flex items-center justify-center py-4"><Loader2 className="w-4 h-4 animate-spin text-zinc-500" /></div>
                        ) : licensees.length === 0 ? (
                          <div className="px-2 py-3 text-sm text-zinc-500 text-center">No {selectedLicenseType} licensees found</div>
                        ) : licensees.map(l => (
                          <SelectItem key={l.user_id} value={l.user_id} className="text-zinc-300 hover:bg-white/[0.08]">
                            <div className="flex flex-col"><span className="font-medium">{l.full_name}</span><span className="text-xs text-zinc-500">{l.email} - ${(l.account_value || 0).toLocaleString()}</span></div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  {selectedLicenseeId && selectedLicenseeId !== 'dummy' && (() => {
                    const sel = licensees.find(l => l.user_id === selectedLicenseeId);
                    return sel ? (
                      <div className="p-3 rounded-lg bg-white/[0.04] border border-white/[0.08] space-y-1 text-sm">
                        <div className="flex justify-between"><span className="text-zinc-500">Account Value:</span><span className="text-white font-mono">${(sel.account_value || 0).toLocaleString()}</span></div>
                        <div className="flex justify-between"><span className="text-zinc-500">Total Deposits:</span><span className="text-white font-mono">${(sel.total_deposits || 0).toLocaleString()}</span></div>
                        <div className="flex justify-between"><span className="text-zinc-500">Total Profit:</span><span className="text-white font-mono">${(sel.total_profit || 0).toLocaleString()}</span></div>
                      </div>
                    ) : null;
                  })()}
                </div>
                <div className="flex gap-3">
                  <Button variant="outline" className="flex-1 border-white/[0.08]" onClick={() => setLicenseeDialogOpen(false)}>Cancel</Button>
                  <Button className="flex-1 btn-primary" onClick={handleSimulateLicensee} disabled={!selectedLicenseeId}><Eye className="w-4 h-4 mr-2" />Start Simulation</Button>
                </div>
              </DialogContent>
            </Dialog>
            </>
          )}
        </div>
      )}

      {/* Navigation */}
      <nav className="px-3 space-y-0.5 flex-1 overflow-y-auto scrollbar-dark">
        {categories.map(cat => renderCategorySection(cat))}

        {/* Tools - Master Admin Hidden Features */}
        {canAccessHiddenFeatures() && !simulatedView && (
          <div className="mb-0.5" data-testid="nav-category-tools">
            <button
              onClick={() => toggleCategory('tools')}
              className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-left transition-all duration-200 text-zinc-500 hover:text-purple-400 hover:bg-purple-500/[0.04]`}
              data-testid="nav-toggle-tools"
            >
              <FlaskConical className="w-3.5 h-3.5" />
              {!collapsed && (
                <>
                  <span className="text-[10px] uppercase tracking-[0.15em] font-semibold flex-1">Tools</span>
                  <Crown className="w-3 h-3 text-purple-400" />
                  <ChevronRight className={`w-3 h-3 transition-transform duration-200 ${expandedCategory === 'tools' ? 'rotate-90' : ''}`} />
                </>
              )}
            </button>
            <div className={`overflow-hidden transition-all duration-200 ${expandedCategory === 'tools' ? 'max-h-[200px] opacity-100' : 'max-h-0 opacity-0'}`}>
              <div className="pl-1 space-y-0.5 py-0.5">
                {hiddenFeatures.map(item => (
                  <NavLink key={item.path} to={item.path} className={hiddenNavLinkClass} onClick={handleNavClick} data-testid={`nav-${item.id}`} title={collapsed ? item.label : undefined}>
                    <item.icon className="w-4 h-4" />
                    {!collapsed && <span className="text-sm flex-1">{item.label}</span>}
                  </NavLink>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Admin Section */}
        {((isAdmin() && !simulatedView) || (simulatedView && ['basic_admin', 'super_admin', 'master_admin'].includes(simulatedView.role))) && (
          <div className="mb-0.5" data-testid="nav-category-admin">
            <button
              onClick={() => toggleCategory('admin')}
              className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-left transition-all duration-200 ${
                location.pathname.startsWith('/admin') && expandedCategory !== 'admin'
                  ? 'text-orange-400 bg-orange-500/[0.06]'
                  : 'text-zinc-500 hover:text-zinc-300 hover:bg-white/[0.02]'
              }`}
              data-testid="nav-toggle-admin"
            >
              <Shield className="w-3.5 h-3.5" />
              {!collapsed && (
                <>
                  <span className="text-[10px] uppercase tracking-[0.15em] font-semibold flex-1">Admin</span>
                  {badgeCounts.admin > 0 && <BadgeCount count={badgeCounts.admin} />}
                  <ChevronRight className={`w-3 h-3 transition-transform duration-200 ${expandedCategory === 'admin' ? 'rotate-90' : ''}`} />
                </>
              )}
            </button>
            <div className={`overflow-hidden transition-all duration-200 ${expandedCategory === 'admin' ? 'max-h-[600px] opacity-100' : 'max-h-0 opacity-0'}`}>
              <div className="pl-1 space-y-0.5 py-0.5">
                {adminNavItems.map(item => (
                  <NavLink key={item.path} to={item.path} className={navLinkClass} onClick={handleNavClick} data-testid={`nav-admin-${item.label.toLowerCase().replace(/\s/g, '-')}`}>
                    <item.icon className="w-4 h-4" />
                    {!collapsed && <span className="text-sm">{item.label}</span>}
                  </NavLink>
                ))}
                {(isSuperAdmin() || isMasterAdmin()) && !simulatedView && superAdminItems.map(item => (
                  <NavLink key={item.path} to={item.path} className={navLinkClass} onClick={handleNavClick}>
                    <item.icon className="w-4 h-4" />
                    {!collapsed && <span className="text-sm">{item.label}</span>}
                  </NavLink>
                ))}
                {isMasterAdmin() && !simulatedView && masterAdminItems.map(item => (
                  <NavLink key={item.path} to={item.path} className={navLinkClass} onClick={handleNavClick}>
                    <item.icon className="w-4 h-4" />
                    {!collapsed && (
                      <>
                        <span className="text-sm flex-1">{item.label}</span>
                        {item.path === '/admin/cleanup' && badgeCounts.admin > 0 && <BadgeCount count={badgeCounts.admin} />}
                      </>
                    )}
                  </NavLink>
                ))}
              </div>
            </div>
          </div>
        )}
      </nav>

      {/* User Profile - Bottom */}
      <div className="p-3 border-t border-white/[0.03]">
        {!collapsed ? (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button className="w-full flex items-center gap-2.5 p-2.5 rounded-lg bg-[#0d0d0d]/50 hover:bg-white/[0.04] transition-colors cursor-pointer">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-orange-500 to-amber-600 flex items-center justify-center text-white text-sm font-bold">
                  {user?.full_name?.charAt(0) || 'U'}
                </div>
                <div className="flex-1 min-w-0 text-left">
                  <p className="text-sm font-medium text-white truncate">{user?.full_name}</p>
                  <p className="text-xs text-zinc-500 truncate flex items-center gap-1">
                    {user?.role === 'master_admin' && <Crown className="w-3 h-3 text-orange-400" />}
                    {user?.role?.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </p>
                </div>
                <ChevronUp className="w-4 h-4 text-zinc-500" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" side="top" className="w-56 bg-[#0d0d0d] border-white/[0.06]">
              <DropdownMenuItem onClick={handleProfileClick} className="cursor-pointer text-zinc-300 hover:text-white hover:bg-[#1a1a1a] focus:bg-[#1a1a1a]">
                <User className="w-4 h-4 mr-2" /> Profile Settings
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => { navigate('/affiliate'); handleNavClick(); }} className="cursor-pointer text-orange-400 hover:text-orange-300 hover:bg-orange-500/10 focus:bg-orange-500/10" data-testid="sidebar-affiliate-center-link">
                <Share2 className="w-4 h-4 mr-2" /> Affiliate Center
              </DropdownMenuItem>
              {isMasterAdmin() && (!simulatedView || simulatedView.role === 'master_admin') && (
                <>
                  <DropdownMenuSeparator className="bg-[#1a1a1a]" />
                  <DropdownMenuItem onClick={handleSettingsClick} className="cursor-pointer text-zinc-300 hover:text-white hover:bg-[#1a1a1a] focus:bg-[#1a1a1a]">
                    <Cog className="w-4 h-4 mr-2" /> Platform Settings
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={handleApiCenterClick} className="cursor-pointer text-zinc-300 hover:text-white hover:bg-[#1a1a1a] focus:bg-[#1a1a1a]">
                    <Plug className="w-4 h-4 mr-2" /> API Center
                  </DropdownMenuItem>
                </>
              )}
              {!window.matchMedia('(display-mode: standalone)').matches && (
                <>
                  <DropdownMenuSeparator className="bg-[#1a1a1a]" />
                  <DropdownMenuItem onClick={() => setPwaInstructionsOpen(true)} className="cursor-pointer text-orange-400 hover:text-orange-300 hover:bg-orange-500/10 focus:bg-orange-500/10" data-testid="install-app-menu-item">
                    <Download className="w-4 h-4 mr-2" /> Install App
                  </DropdownMenuItem>
                </>
              )}
              <DropdownMenuSeparator className="bg-[#1a1a1a]" />
              <DropdownMenuItem onClick={handlePurgeCache} className="cursor-pointer text-amber-400 hover:text-amber-300 hover:bg-amber-500/10 focus:bg-amber-500/10" data-testid="purge-cache-menu-item">
                <RotateCcw className="w-4 h-4 mr-2" /> Clear Cache &amp; Reload
              </DropdownMenuItem>
              <DropdownMenuSeparator className="bg-[#1a1a1a]" />
              <DropdownMenuItem onClick={handleLogout} className="cursor-pointer text-red-400 hover:text-red-300 hover:bg-red-500/10 focus:bg-red-500/10">
                <LogOut className="w-4 h-4 mr-2" /> Log Out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        ) : (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button className="w-full flex items-center justify-center p-2 rounded-lg bg-[#0d0d0d]/50 hover:bg-white/[0.04] transition-colors cursor-pointer">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-orange-500 to-amber-600 flex items-center justify-center text-white text-sm font-bold">
                  {user?.full_name?.charAt(0) || 'U'}
                </div>
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="center" side="right" className="w-56 bg-[#0d0d0d] border-white/[0.06]">
              <div className="px-2 py-1.5 text-sm text-zinc-400">{user?.full_name}</div>
              <DropdownMenuSeparator className="bg-[#1a1a1a]" />
              <DropdownMenuItem onClick={handleProfileClick} className="cursor-pointer text-zinc-300 hover:text-white hover:bg-[#1a1a1a]"><User className="w-4 h-4 mr-2" /> Profile</DropdownMenuItem>
              <DropdownMenuItem onClick={handleLogout} className="cursor-pointer text-red-400 hover:text-red-300 hover:bg-red-500/10"><LogOut className="w-4 h-4 mr-2" /> Log Out</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )}
        <button onClick={() => onClose()} className="w-full mt-2 text-xs text-zinc-500 hover:text-white transition-colors lg:hidden">Close Menu</button>
      </div>
      <PWAInstallInstructions open={pwaInstructionsOpen} onOpenChange={setPwaInstructionsOpen} />
    </aside>
  );
};
