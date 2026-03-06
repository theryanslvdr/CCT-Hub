import React, { useState, useEffect } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { settingsAPI, adminAPI } from '@/lib/api';
import { PWAInstallInstructions } from '@/lib/pwa';
import { 
  LayoutDashboard, TrendingUp, Activity, Target, CreditCard, 
  Settings, Users, BarChart3, Radio, Cog, Eye, EyeOff,
  FlaskConical, Crown, LogOut, User, ChevronUp, Wallet, Plug, Award,
  ChevronDown, UserCheck, Shield, ShieldCheck, Star, Sparkles, Loader2, Download, CheckSquare, Share2, Trophy, MessageSquare, Gauge
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuLabel,
} from '@/components/ui/dropdown-menu';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

export const Sidebar = ({ isOpen, onClose, collapsed = false }) => {
  const { user, isAdmin, isMasterAdmin, isSuperAdmin, canAccessHiddenFeatures, simulatedView, simulateMemberView, exitSimulation, logout } = useAuth();
  const [platformSettings, setPlatformSettings] = useState(null);
  const navigate = useNavigate();
  
  // Licensee simulation dialog state
  const [licenseeDialogOpen, setLicenseeDialogOpen] = useState(false);
  const [pwaInstructionsOpen, setPwaInstructionsOpen] = useState(false);
  const [selectedLicenseType, setSelectedLicenseType] = useState(null);
  const [licensees, setLicensees] = useState([]);
  const [loadingLicensees, setLoadingLicensees] = useState(false);
  const [selectedLicenseeId, setSelectedLicenseeId] = useState('');
  const [adminExpanded, setAdminExpanded] = useState(false);

  // Load platform settings for logo
  useEffect(() => {
    const loadSettings = async () => {
      try {
        const res = await settingsAPI.getPlatform();
        setPlatformSettings(res.data);
      } catch (error) {
        console.error('Failed to load platform settings');
      }
    };
    loadSettings();
  }, []);
  
  // Load licensees when dialog opens
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
      
      // Filter licensees by type
      const activeLicenses = licensesRes.data.licenses?.filter(
        l => l.is_active && l.license_type === licenseType
      ) || [];
      
      // Get members array from response
      const members = membersRes.data.members || membersRes.data || [];
      
      // Match with member details - licenses already have user_name from backend
      const licenseesWithDetails = activeLicenses.map(license => {
        const member = members.find(m => m.id === license.user_id);
        // For licensees, total_profit = current_amount - starting_amount
        // This represents the accumulated projected profits from days when Master Admin traded
        const licenseeProfit = (license.current_amount || 0) - (license.starting_amount || 0);
        return {
          ...license,
          // Use user_name from license (already enriched by backend), fallback to member.full_name
          full_name: license.user_name || member?.full_name || 'Unknown User',
          email: license.user_email || member?.email || 'N/A',
          account_value: license.current_amount || member?.account_value || 0,
          lot_size: member?.lot_size || 0.01,
          total_deposits: license.starting_amount || member?.total_deposits || 0,
          total_profit: licenseeProfit, // Calculated as current_amount - starting_amount
          allowed_dashboards: member?.allowed_dashboards
        };
      });
      
      setLicensees(licenseesWithDetails);
    } catch (error) {
      console.error('Failed to load licensees:', error);
      setLicensees([]);
    } finally {
      setLoadingLicensees(false);
    }
  };
  
  const handleSimulateLicensee = () => {
    if (selectedLicenseeId === 'dummy') {
      // Simulate with dummy values
      simulateMemberView({ 
        role: 'member', 
        license_type: selectedLicenseType, 
        displayName: `${selectedLicenseType === 'honorary' ? 'Honorary' : selectedLicenseType === 'honorary_fa' ? 'Honorary FA' : 'Extended'} Licensee (Demo)`,
        accountValue: 5000,
        lotSize: 0.05,
        totalDeposits: 5000,
        totalProfit: 0,
        starting_amount: 5000, // Add starting amount for demo
        effective_start_date: new Date().toISOString().split('T')[0] // Default to today for demo
      });
    } else {
      // Simulate specific licensee
      const licensee = licensees.find(l => l.user_id === selectedLicenseeId);
      if (licensee) {
        simulateMemberView({
          id: licensee.user_id,
          memberId: licensee.user_id,
          licenseId: licensee.id, // Include license ID for trade override API calls
          full_name: licensee.full_name,
          account_value: licensee.account_value,
          lot_size: licensee.lot_size,
          total_deposits: licensee.total_deposits,
          total_profit: licensee.total_profit,
          starting_amount: licensee.starting_amount, // Add starting amount for growth calculation
          allowed_dashboards: licensee.allowed_dashboards,
          license_type: selectedLicenseType,
          displayName: licensee.full_name,
          effective_start_date: licensee.effective_start_date || licensee.start_date // Include effective start date
        });
      }
    }
    setLicenseeDialogOpen(false);
  };

  // Member navigation items (modular access)
  const memberNavItems = [
    { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard', id: 'dashboard' },
    { path: '/profit-tracker', icon: TrendingUp, label: 'Profit Tracker', id: 'profit_tracker' },
    { path: '/trade-monitor', icon: Activity, label: 'Trade Monitor', id: 'trade_monitor', hideForLicensee: true },
    { path: '/habits', icon: CheckSquare, label: 'Daily Habits', id: 'habits', hideForLicensee: true },
    { path: '/affiliate', icon: Share2, label: 'Affiliate Center', id: 'affiliate', hideForLicensee: true },
    { path: '/licensee-account', icon: Award, label: 'Deposit/Withdrawal', id: 'licensee_account', licenseeOnly: true },
    { path: '/family-accounts', icon: Users, label: 'Family Accounts', id: 'family_accounts', honoraryFaOnly: true },
    { path: '/my-rewards', icon: Star, label: 'My Rewards', id: 'my_rewards', hideForLicensee: true },
    { path: '/leaderboard', icon: Trophy, label: 'Leaderboard', id: 'leaderboard', hideForLicensee: true },
    { path: '/forum', icon: MessageSquare, label: 'Community Forum', id: 'forum', hideForLicensee: true },
  ];

  // Hidden features (only for Master Admin) - with crown indicator
  const hiddenFeatures = [
    { path: '/profit-planner', icon: Target, label: 'Profit Planner', id: 'profit_planner', hidden: true },
    { path: '/debt-management', icon: CreditCard, label: 'Debt Management', id: 'debt_management', hidden: true },
  ];

  // Admin navigation items - kept in sidebar (removed Settings & API Center - moved to profile popover)
  const adminNavItems = [
    { path: '/admin/members', icon: Users, label: 'Members' },
    { path: '/admin/signals', icon: Radio, label: 'Trading Signals' },
    { path: '/admin/analytics', icon: BarChart3, label: 'Team Analytics' },
  ];

  // Super/Master Admin only items
  const superAdminItems = [
    { path: '/admin/transactions', icon: Wallet, label: 'Transactions' },
    { path: '/admin/rewards', icon: Star, label: 'Rewards Admin' },
  ];

  // Master Admin only items
  const masterAdminItems = [
    { path: '/admin/licenses', icon: Award, label: 'Licenses' },
    { path: '/admin/system-check', icon: Shield, label: 'System Check' },
    { path: '/admin/system-health', icon: Gauge, label: 'System Health' },
  ];

  // Check if user or simulated view is a licensee
  const isLicenseeView = simulatedView?.license_type || user?.license_type;

  // Check if user is honorary_fa licensee
  const isHonoraryFa = (simulatedView?.license_type || user?.license_type) === 'honorary_fa';

  // Filter nav items based on user's allowed dashboards (if member)
  const getVisibleMemberItems = () => {
    // For members or simulated view, filter based on allowed dashboards
    const baseDashboards = simulatedView?.allowed_dashboards || user?.allowed_dashboards || [];
    // For licensees, only include dashboard and profile (no habits/affiliate)
    const alwaysInclude = isLicenseeView
      ? ['dashboard', 'profile', 'my_rewards']
      : ['dashboard', 'profile', 'habits', 'affiliate', 'my_rewards', 'leaderboard', 'forum'];
    const effectiveDashboards = [...new Set([...baseDashboards, ...alwaysInclude])];
    
    return memberNavItems.filter(item => {
      // Hide items flagged for licensees (Trade Monitor, Habits, Affiliate)
      if (item.hideForLicensee && isLicenseeView) {
        return false;
      }
      // Deposit/Withdrawal only for licensees
      if (item.licenseeOnly && !isLicenseeView) {
        return false;
      }
      // Family Accounts only for honorary_fa licensees
      if (item.honoraryFaOnly && !isHonoraryFa) {
        return false;
      }
      // For admins NOT in simulation, show all items except licensee-only/family-only
      if (isAdmin() && !simulatedView) {
        return !item.licenseeOnly && !item.honoraryFaOnly;
      }
      return effectiveDashboards.includes(item.id) || (item.licenseeOnly && isLicenseeView) || (item.honoraryFaOnly && isHonoraryFa);
    });
  };

  const navLinkClass = ({ isActive }) => 
    `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 ${
      isActive 
        ? 'bg-gradient-to-r from-blue-600/20 to-purple-600/20 text-white border border-blue-500/30' 
        : 'text-zinc-400 hover:text-white hover:bg-zinc-800/50'
    }`;

  // Special class for hidden features - purple text on hover
  const hiddenNavLinkClass = ({ isActive }) => 
    `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 ${
      isActive 
        ? 'bg-gradient-to-r from-purple-600/20 to-pink-600/20 text-purple-300 border border-purple-500/30' 
        : 'text-zinc-400 hover:text-purple-400 hover:bg-purple-500/10'
    }`;

  const handleNavClick = () => {
    if (window.innerWidth < 1024) {
      onClose();
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleProfileClick = () => {
    navigate('/profile');
    handleNavClick();
  };

  const handleSettingsClick = () => {
    navigate('/admin/settings');
    handleNavClick();
  };

  const handleApiCenterClick = () => {
    navigate('/admin/api-center');
    handleNavClick();
  };

  const handleLicensesClick = () => {
    navigate('/admin/licenses');
    handleNavClick();
  };

  // Determine logo display
  const hasLogo = platformSettings?.logo_url;
  const hasFavicon = platformSettings?.favicon_url;

  return (
    <aside className={`sidebar ${isOpen ? 'open' : ''} ${collapsed ? 'sidebar-collapsed' : ''} flex flex-col`}>
      {/* Logo Section */}
      <div className="p-5 pb-4">
        <div className="flex items-center gap-3">
          {collapsed ? (
            // Collapsed: Show favicon or icon
            hasFavicon ? (
              <img src={platformSettings.favicon_url} alt="Logo" className="w-9 h-9 rounded-lg object-contain" />
            ) : (
              <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                <TrendingUp className="w-5 h-5 text-white" />
              </div>
            )
          ) : (
            // Expanded: Show full logo or text
            hasLogo ? (
              <img src={platformSettings.logo_url} alt="CrossCurrent" className="h-10 max-w-[180px] object-contain" />
            ) : (
              <>
                <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
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

      {/* Master Admin Simulation Control */}
      {isMasterAdmin() && !collapsed && (
        <div className="px-3 mb-3">
          {simulatedView ? (
            <div className="p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/30">
              <div className="flex items-center gap-2 text-amber-400 text-xs mb-2">
                <Eye className="w-3.5 h-3.5" />
                <span>Simulating: {simulatedView.displayName || simulatedView.role}</span>
              </div>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={exitSimulation}
                className="w-full h-8 text-xs text-amber-400 border-amber-500/30 hover:bg-amber-500/10"
              >
                <EyeOff className="w-3.5 h-3.5 mr-1.5" /> Exit Simulation
              </Button>
            </div>
          ) : (
            <>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="w-full h-8 text-xs text-zinc-400 border-zinc-700 hover:bg-zinc-800 justify-between"
                >
                  <span className="flex items-center gap-1.5">
                    <Eye className="w-3.5 h-3.5" /> Simulate View
                  </span>
                  <ChevronDown className="w-3.5 h-3.5" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start" className="w-56 bg-zinc-900 border-zinc-700">
                <DropdownMenuLabel className="text-zinc-500 text-xs">Role Simulation</DropdownMenuLabel>
                <DropdownMenuItem 
                  onClick={() => simulateMemberView({ role: 'member', displayName: 'Member' })}
                  className="text-zinc-300 hover:bg-zinc-800 cursor-pointer"
                >
                  <User className="w-4 h-4 mr-2 text-blue-400" />
                  Member View
                </DropdownMenuItem>
                <DropdownMenuItem 
                  onClick={() => simulateMemberView({ role: 'basic_admin', displayName: 'Basic Admin' })}
                  className="text-zinc-300 hover:bg-zinc-800 cursor-pointer"
                >
                  <UserCheck className="w-4 h-4 mr-2 text-green-400" />
                  Basic Admin View
                </DropdownMenuItem>
                <DropdownMenuItem 
                  onClick={() => simulateMemberView({ role: 'super_admin', displayName: 'Super Admin' })}
                  className="text-zinc-300 hover:bg-zinc-800 cursor-pointer"
                >
                  <ShieldCheck className="w-4 h-4 mr-2 text-purple-400" />
                  Super Admin View
                </DropdownMenuItem>
                <DropdownMenuSeparator className="bg-zinc-700" />
                <DropdownMenuLabel className="text-zinc-500 text-xs">Licensee Simulation</DropdownMenuLabel>
                <DropdownMenuItem 
                  onClick={() => handleLicenseeSimulationClick('honorary')}
                  className="text-zinc-300 hover:bg-zinc-800 cursor-pointer"
                >
                  <Star className="w-4 h-4 mr-2 text-amber-400" />
                  Honorary Licensee View
                </DropdownMenuItem>
                <DropdownMenuItem 
                  onClick={() => handleLicenseeSimulationClick('honorary_fa')}
                  className="text-zinc-300 hover:bg-zinc-800 cursor-pointer"
                >
                  <Users className="w-4 h-4 mr-2 text-blue-400" />
                  Honorary FA (Family) View
                </DropdownMenuItem>
                <DropdownMenuItem 
                  onClick={() => handleLicenseeSimulationClick('extended')}
                  className="text-zinc-300 hover:bg-zinc-800 cursor-pointer"
                >
                  <Sparkles className="w-4 h-4 mr-2 text-purple-400" />
                  Extended Licensee View
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
            
            {/* Licensee Simulation Dialog */}
            <Dialog open={licenseeDialogOpen} onOpenChange={setLicenseeDialogOpen}>
              <DialogContent className="bg-zinc-900 border-zinc-700 max-w-md">
                <DialogHeader>
                  <DialogTitle className="text-white flex items-center gap-2">
                    {selectedLicenseType === 'honorary' ? (
                      <Star className="w-5 h-5 text-amber-400" />
                    ) : selectedLicenseType === 'honorary_fa' ? (
                      <Users className="w-5 h-5 text-blue-400" />
                    ) : (
                      <Sparkles className="w-5 h-5 text-purple-400" />
                    )}
                    Simulate {selectedLicenseType === 'honorary' ? 'Honorary' : selectedLicenseType === 'honorary_fa' ? 'Honorary FA' : 'Extended'} Licensee
                  </DialogTitle>
                  <DialogDescription className="text-zinc-400">
                    Choose how you want to simulate this licensee view.
                  </DialogDescription>
                </DialogHeader>
                
                <div className="space-y-4 py-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-zinc-300">Simulation Mode</label>
                    <Select value={selectedLicenseeId} onValueChange={setSelectedLicenseeId}>
                      <SelectTrigger className="w-full bg-zinc-800 border-zinc-700 text-zinc-300">
                        <SelectValue placeholder="Select simulation mode..." />
                      </SelectTrigger>
                      <SelectContent className="bg-zinc-800 border-zinc-700">
                        <SelectItem value="dummy" className="text-zinc-300 hover:bg-zinc-700">
                          <div className="flex flex-col">
                            <span className="font-medium">Demo Mode (Dummy Values)</span>
                            <span className="text-xs text-zinc-500">Use placeholder data ($5,000 balance)</span>
                          </div>
                        </SelectItem>
                        {loadingLicensees ? (
                          <div className="flex items-center justify-center py-4">
                            <Loader2 className="w-4 h-4 animate-spin text-zinc-500" />
                          </div>
                        ) : licensees.length === 0 ? (
                          <div className="px-2 py-3 text-sm text-zinc-500 text-center">
                            No {selectedLicenseType} licensees found
                          </div>
                        ) : (
                          licensees.map(licensee => (
                            <SelectItem 
                              key={licensee.user_id} 
                              value={licensee.user_id}
                              className="text-zinc-300 hover:bg-zinc-700"
                            >
                              <div className="flex flex-col">
                                <span className="font-medium">{licensee.full_name}</span>
                                <span className="text-xs text-zinc-500">
                                  {licensee.email} • Balance: ${(licensee.account_value || 0).toLocaleString()}
                                </span>
                              </div>
                            </SelectItem>
                          ))
                        )}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  {selectedLicenseeId && selectedLicenseeId !== 'dummy' && (
                    <div className="p-3 rounded-lg bg-zinc-800/50 border border-zinc-700">
                      {(() => {
                        const selected = licensees.find(l => l.user_id === selectedLicenseeId);
                        return selected ? (
                          <div className="space-y-1 text-sm">
                            <div className="flex justify-between">
                              <span className="text-zinc-500">Account Value:</span>
                              <span className="text-white font-mono">${(selected.account_value || 0).toLocaleString()}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-zinc-500">Total Deposits:</span>
                              <span className="text-white font-mono">${(selected.total_deposits || 0).toLocaleString()}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-zinc-500">Total Profit:</span>
                              <span className="text-white font-mono">${(selected.total_profit || 0).toLocaleString()}</span>
                            </div>
                          </div>
                        ) : null;
                      })()}
                    </div>
                  )}
                </div>
                
                <div className="flex gap-3">
                  <Button
                    variant="outline"
                    className="flex-1 border-zinc-700"
                    onClick={() => setLicenseeDialogOpen(false)}
                  >
                    Cancel
                  </Button>
                  <Button
                    className="flex-1 btn-primary"
                    onClick={handleSimulateLicensee}
                    disabled={!selectedLicenseeId}
                  >
                    <Eye className="w-4 h-4 mr-2" />
                    Start Simulation
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
            </>
          )}
        </div>
      )}

      {/* Navigation - Main Member Items */}
      <nav className="px-3 space-y-1 flex-1 overflow-y-auto">
        {/* Core section */}
        {!collapsed && <p className="text-[10px] text-zinc-600 uppercase tracking-widest px-3 pt-2 pb-1">Core</p>}
        {getVisibleMemberItems().filter(i => ['dashboard', 'profit_tracker', 'trade_monitor'].includes(i.id)).map((item) => (
          <NavLink 
            key={item.path} 
            to={item.path} 
            className={navLinkClass}
            onClick={handleNavClick}
            data-testid={`nav-${item.id}`}
            title={collapsed ? item.label : undefined}
          >
            <item.icon className="w-4 h-4" />
            {!collapsed && <span className="text-sm">{item.label}</span>}
          </NavLink>
        ))}

        {/* Growth section */}
        {(() => {
          const growthItems = getVisibleMemberItems().filter(i => 
            ['habits', 'affiliate', 'my_rewards', 'leaderboard', 'licensee_account', 'family_accounts'].includes(i.id)
          );
          if (growthItems.length === 0) return null;
          return (
            <>
              {!collapsed && <p className="text-[10px] text-zinc-600 uppercase tracking-widest px-3 pt-4 pb-1">Growth</p>}
              {growthItems.map((item) => (
                <NavLink 
                  key={item.path} 
                  to={item.path} 
                  className={navLinkClass}
                  onClick={handleNavClick}
                  data-testid={`nav-${item.id}`}
                  title={collapsed ? item.label : undefined}
                >
                  <item.icon className="w-4 h-4" />
                  {!collapsed && <span className="text-sm">{item.label}</span>}
                </NavLink>
              ))}
            </>
          );
        })()}

        {/* Community section */}
        {(() => {
          const communityItems = getVisibleMemberItems().filter(i => ['forum'].includes(i.id));
          if (communityItems.length === 0) return null;
          return (
            <>
              {!collapsed && <p className="text-[10px] text-zinc-600 uppercase tracking-widest px-3 pt-4 pb-1">Community</p>}
              {communityItems.map((item) => (
                <NavLink 
                  key={item.path} 
                  to={item.path} 
                  className={navLinkClass}
                  onClick={handleNavClick}
                  data-testid={`nav-${item.id}`}
                  title={collapsed ? item.label : undefined}
                >
                  <item.icon className="w-4 h-4" />
                  {!collapsed && <span className="text-sm">{item.label}</span>}
                </NavLink>
              ))}
            </>
          );
        })()}

        {/* Hidden Features (Master Admin only) - No section title, just crown icons */}
        {canAccessHiddenFeatures() && !simulatedView && (
          <>
            {!collapsed && <p className="text-[10px] text-zinc-600 uppercase tracking-widest px-3 pt-4 pb-1">Tools</p>}
            
            {hiddenFeatures.map((item) => (
              <NavLink 
                key={item.path} 
                to={item.path} 
                className={hiddenNavLinkClass}
                onClick={handleNavClick}
                data-testid={`nav-${item.id}`}
                title={collapsed ? item.label : undefined}
              >
                <item.icon className="w-4 h-4" />
                {!collapsed && (
                  <>
                    <span className="text-sm flex-1">{item.label}</span>
                    <Crown className="w-3.5 h-3.5 text-purple-400" />
                  </>
                )}
              </NavLink>
            ))}
          </>
        )}
      </nav>

      {/* Admin Section - Collapsible, anchored at bottom */}
      {((isAdmin() && !simulatedView) || (simulatedView && ['basic_admin', 'super_admin', 'master_admin'].includes(simulatedView.role))) && (
        <div className="px-3 pb-2 border-t border-zinc-800/50 pt-2">
          <button
            onClick={() => setAdminExpanded(!adminExpanded)}
            className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-800/50 transition-colors"
            data-testid="admin-section-toggle"
          >
            {!collapsed && <span className="text-xs uppercase tracking-wider font-medium">Admin</span>}
            {collapsed ? (
              <Shield className="w-4 h-4 mx-auto" />
            ) : (
              <ChevronDown className={`w-3.5 h-3.5 transition-transform duration-200 ${adminExpanded ? 'rotate-180' : ''}`} />
            )}
          </button>
          
          <div className={`space-y-1 overflow-hidden transition-all duration-200 ${adminExpanded ? 'max-h-[500px] opacity-100 mt-1' : 'max-h-0 opacity-0'}`}>
            {adminNavItems.map((item) => (
              <NavLink 
                key={item.path} 
                to={item.path} 
                className={navLinkClass}
                onClick={handleNavClick}
                title={collapsed ? item.label : undefined}
              >
                <item.icon className="w-4 h-4" />
                {!collapsed && <span className="text-sm">{item.label}</span>}
              </NavLink>
            ))}
            
            {/* Super/Master Admin only items */}
            {((!simulatedView && (isSuperAdmin() || isMasterAdmin())) || (simulatedView && ['super_admin', 'master_admin'].includes(simulatedView.role))) && superAdminItems.map((item) => (
              <NavLink 
                key={item.path} 
                to={item.path} 
                className={navLinkClass}
                onClick={handleNavClick}
                title={collapsed ? item.label : undefined}
              >
                <item.icon className="w-4 h-4" />
                {!collapsed && <span className="text-sm">{item.label}</span>}
              </NavLink>
            ))}

            {/* Master Admin only items */}
            {((!simulatedView && isMasterAdmin()) || (simulatedView && simulatedView.role === 'master_admin')) && masterAdminItems.map((item) => (
              <NavLink 
                key={item.path} 
                to={item.path} 
                className={navLinkClass}
                onClick={handleNavClick}
                title={collapsed ? item.label : undefined}
              >
                <item.icon className="w-4 h-4" />
                {!collapsed && <span className="text-sm">{item.label}</span>}
              </NavLink>
            ))}
          </div>
        </div>
      )}

      {/* User Profile Section - Fixed at Bottom */}
      <div className="p-3 border-t border-zinc-800">
        {!collapsed ? (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button className="w-full flex items-center gap-2.5 p-2.5 rounded-lg bg-zinc-900/50 hover:bg-zinc-800/50 transition-colors cursor-pointer">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-sm font-bold">
                  {user?.full_name?.charAt(0) || 'U'}
                </div>
                <div className="flex-1 min-w-0 text-left">
                  <p className="text-sm font-medium text-white truncate">{user?.full_name}</p>
                  <p className="text-xs text-zinc-500 truncate flex items-center gap-1">
                    {user?.role === 'master_admin' && <Crown className="w-3 h-3 text-purple-400" />}
                    {user?.role?.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </p>
                </div>
                <ChevronUp className="w-4 h-4 text-zinc-500" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent 
              align="end" 
              side="top" 
              className="w-56 bg-zinc-900 border-zinc-800"
            >
              <DropdownMenuItem 
                onClick={handleProfileClick}
                className="cursor-pointer text-zinc-300 hover:text-white hover:bg-zinc-800 focus:bg-zinc-800"
              >
                <User className="w-4 h-4 mr-2" />
                Profile Settings
              </DropdownMenuItem>
              
              {/* Master Admin only: Platform Settings & API Center - hide during non-master simulation */}
              {isMasterAdmin() && (!simulatedView || simulatedView.role === 'master_admin') && (
                <>
                  <DropdownMenuSeparator className="bg-zinc-800" />
                  <DropdownMenuItem 
                    onClick={handleSettingsClick}
                    className="cursor-pointer text-zinc-300 hover:text-white hover:bg-zinc-800 focus:bg-zinc-800"
                  >
                    <Cog className="w-4 h-4 mr-2" />
                    Platform Settings
                  </DropdownMenuItem>
                  <DropdownMenuItem 
                    onClick={handleApiCenterClick}
                    className="cursor-pointer text-zinc-300 hover:text-white hover:bg-zinc-800 focus:bg-zinc-800"
                  >
                    <Plug className="w-4 h-4 mr-2" />
                    API Center
                  </DropdownMenuItem>
                </>
              )}
              
              {!window.matchMedia('(display-mode: standalone)').matches && (
                <>
                  <DropdownMenuSeparator className="bg-zinc-800" />
                  <DropdownMenuItem 
                    onClick={() => setPwaInstructionsOpen(true)}
                    className="cursor-pointer text-blue-400 hover:text-blue-300 hover:bg-blue-500/10 focus:bg-blue-500/10"
                    data-testid="install-app-menu-item"
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Install App
                  </DropdownMenuItem>
                </>
              )}

              <DropdownMenuSeparator className="bg-zinc-800" />
              <DropdownMenuItem 
                onClick={handleLogout}
                className="cursor-pointer text-red-400 hover:text-red-300 hover:bg-red-500/10 focus:bg-red-500/10"
              >
                <LogOut className="w-4 h-4 mr-2" />
                Log Out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        ) : (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button className="w-full flex items-center justify-center p-2 rounded-lg bg-zinc-900/50 hover:bg-zinc-800/50 transition-colors cursor-pointer">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-sm font-bold">
                  {user?.full_name?.charAt(0) || 'U'}
                </div>
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent 
              align="center" 
              side="right" 
              className="w-56 bg-zinc-900 border-zinc-800"
            >
              <div className="px-2 py-1.5 text-sm text-zinc-400">
                {user?.full_name}
              </div>
              <DropdownMenuSeparator className="bg-zinc-800" />
              <DropdownMenuItem 
                onClick={handleProfileClick}
                className="cursor-pointer text-zinc-300 hover:text-white hover:bg-zinc-800 focus:bg-zinc-800"
              >
                <User className="w-4 h-4 mr-2" />
                Profile Settings
              </DropdownMenuItem>
              
              {/* Master Admin only: Platform Settings & API Center - hide during non-master simulation */}
              {isMasterAdmin() && (!simulatedView || simulatedView.role === 'master_admin') && (
                <>
                  <DropdownMenuSeparator className="bg-zinc-800" />
                  <DropdownMenuItem 
                    onClick={handleSettingsClick}
                    className="cursor-pointer text-zinc-300 hover:text-white hover:bg-zinc-800 focus:bg-zinc-800"
                  >
                    <Cog className="w-4 h-4 mr-2" />
                    Platform Settings
                  </DropdownMenuItem>
                  <DropdownMenuItem 
                    onClick={handleApiCenterClick}
                    className="cursor-pointer text-zinc-300 hover:text-white hover:bg-zinc-800 focus:bg-zinc-800"
                  >
                    <Plug className="w-4 h-4 mr-2" />
                    API Center
                  </DropdownMenuItem>
                </>
              )}
              
              {!window.matchMedia('(display-mode: standalone)').matches && (
                <>
                  <DropdownMenuSeparator className="bg-zinc-800" />
                  <DropdownMenuItem 
                    onClick={() => setPwaInstructionsOpen(true)}
                    className="cursor-pointer text-blue-400 hover:text-blue-300 hover:bg-blue-500/10 focus:bg-blue-500/10"
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Install App
                  </DropdownMenuItem>
                </>
              )}

              <DropdownMenuSeparator className="bg-zinc-800" />
              <DropdownMenuItem 
                onClick={handleLogout}
                className="cursor-pointer text-red-400 hover:text-red-300 hover:bg-red-500/10 focus:bg-red-500/10"
              >
                <LogOut className="w-4 h-4 mr-2" />
                Log Out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )}
        
        {/* Mobile close button */}
        <button 
          onClick={() => onClose()}
          className="w-full mt-2 text-xs text-zinc-500 hover:text-white transition-colors lg:hidden"
        >
          Close Menu
        </button>
      </div>
      <PWAInstallInstructions open={pwaInstructionsOpen} onOpenChange={setPwaInstructionsOpen} />
    </aside>
  );
};
