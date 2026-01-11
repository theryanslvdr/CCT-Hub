import React, { useState, useEffect } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { settingsAPI } from '@/lib/api';
import { 
  LayoutDashboard, TrendingUp, Activity, Target, CreditCard, 
  Settings, Users, BarChart3, Radio, Cog, Eye, EyeOff,
  FlaskConical, Crown, LogOut, User, ChevronUp
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

export const Sidebar = ({ isOpen, onClose, collapsed = false }) => {
  const { user, isAdmin, isMasterAdmin, canAccessHiddenFeatures, simulatedView, simulateMemberView, exitSimulation, logout } = useAuth();
  const [platformSettings, setPlatformSettings] = useState(null);
  const navigate = useNavigate();

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

  // Member navigation items (modular access)
  const memberNavItems = [
    { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard', id: 'dashboard' },
    { path: '/profit-tracker', icon: TrendingUp, label: 'Profit Tracker', id: 'profit_tracker' },
    { path: '/trade-monitor', icon: Activity, label: 'Trade Monitor', id: 'trade_monitor' },
  ];

  // Hidden features (only for Master Admin) - with crown indicator
  const hiddenFeatures = [
    { path: '/profit-planner', icon: Target, label: 'Profit Planner', id: 'profit_planner', hidden: true },
    { path: '/debt-management', icon: CreditCard, label: 'Debt Management', id: 'debt_management', hidden: true },
  ];

  // Admin navigation items
  const adminNavItems = [
    { path: '/admin/members', icon: Users, label: 'Members' },
    { path: '/admin/signals', icon: Radio, label: 'Trading Signals' },
    { path: '/admin/analytics', icon: BarChart3, label: 'Team Analytics' },
    { path: '/admin/settings', icon: Cog, label: 'Settings' },
    { path: '/admin/api-center', icon: FlaskConical, label: 'API Center' },
  ];

  // Filter nav items based on user's allowed dashboards (if member)
  const getVisibleMemberItems = () => {
    if (isAdmin() && !simulatedView) {
      return memberNavItems;
    }
    
    // For members or simulated view, filter based on allowed dashboards
    const effectiveDashboards = simulatedView?.allowed_dashboards || user?.allowed_dashboards || ['dashboard', 'profit_tracker', 'trade_monitor', 'profile'];
    return memberNavItems.filter(item => effectiveDashboards.includes(item.id));
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
                <span>Simulating Member View</span>
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
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => simulateMemberView('member')}
              className="w-full h-8 text-xs text-zinc-400 border-zinc-700 hover:bg-zinc-800"
            >
              <Eye className="w-3.5 h-3.5 mr-1.5" /> Simulate Member View
            </Button>
          )}
        </div>
      )}

      {/* Navigation - Scrollable */}
      <nav className="px-3 space-y-1 flex-1 overflow-y-auto">
        {/* Regular menu items */}
        {getVisibleMemberItems().map((item) => (
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

        {/* Hidden Features (Master Admin only) - No section title, just crown icons */}
        {canAccessHiddenFeatures() && !simulatedView && (
          <>
            {/* Divider */}
            <div className="my-3 border-t border-zinc-800/50" />
            
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

        {/* Admin Section */}
        {isAdmin() && !simulatedView && (
          <>
            <p className="text-xs text-zinc-500 uppercase tracking-wider mt-5 mb-2 px-3">
              {!collapsed && 'Admin Section'}
            </p>
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
          </>
        )}
      </nav>

      {/* User Profile Section - Fixed at Bottom */}
      <div className="p-3 border-t border-zinc-800 mt-auto">
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
    </aside>
  );
};
