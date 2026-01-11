import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { 
  LayoutDashboard, TrendingUp, Activity, Target, CreditCard, 
  Settings, Users, BarChart3, Radio, Cog, Eye, EyeOff,
  FlaskConical, Crown
} from 'lucide-react';
import { Button } from '@/components/ui/button';

export const Sidebar = ({ isOpen, onClose }) => {
  const { user, isAdmin, isSuperAdmin, isMasterAdmin, canAccessDashboard, canAccessHiddenFeatures, simulatedView, simulateMemberView, exitSimulation } = useAuth();
  const location = useLocation();

  // Member navigation items (modular access)
  const memberNavItems = [
    { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard', id: 'dashboard' },
    { path: '/profit-tracker', icon: TrendingUp, label: 'Profit Tracker', id: 'profit_tracker' },
    { path: '/trade-monitor', icon: Activity, label: 'Trade Monitor', id: 'trade_monitor' },
    { path: '/profile', icon: Settings, label: 'Profile', id: 'profile' },
  ];

  // Hidden features (only for Master Admin)
  const hiddenFeatures = [
    { path: '/profit-planner', icon: Target, label: 'Profit Planner', id: 'profit_planner' },
    { path: '/debt-management', icon: CreditCard, label: 'Debt Management', id: 'debt_management' },
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

  const handleNavClick = () => {
    if (window.innerWidth < 1024) {
      onClose();
    }
  };

  return (
    <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
      <div className="p-5 pb-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
            <TrendingUp className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white">CrossCurrent</h1>
            <p className="text-xs text-zinc-500">Finance Center</p>
          </div>
        </div>
      </div>

      {/* Master Admin Simulation Control */}
      {isMasterAdmin() && (
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

      <nav className="px-3 space-y-1">
        {getVisibleMemberItems().map((item) => (
          <NavLink 
            key={item.path} 
            to={item.path} 
            className={navLinkClass}
            onClick={handleNavClick}
            data-testid={`nav-${item.id}`}
          >
            <item.icon className="w-4 h-4" />
            <span className="text-sm">{item.label}</span>
          </NavLink>
        ))}

        {/* Hidden Features (Master Admin only) */}
        {canAccessHiddenFeatures() && !simulatedView && (
          <>
            <p className="text-xs text-purple-400 uppercase tracking-wider mt-5 mb-2 px-3 flex items-center justify-between">
              <span>Hidden Features</span>
              <Crown className="w-3.5 h-3.5" />
            </p>
            {hiddenFeatures.map((item) => (
              <NavLink 
                key={item.path} 
                to={item.path} 
                className={navLinkClass}
                onClick={handleNavClick}
                data-testid={`nav-${item.id}`}
              >
                <item.icon className="w-4 h-4" />
                <span className="text-sm">{item.label}</span>
              </NavLink>
            ))}
          </>
        )}

        {/* Admin Section */}
        {isAdmin() && !simulatedView && (
          <>
            <p className="text-xs text-zinc-500 uppercase tracking-wider mt-5 mb-2 px-3">Admin Section</p>
            {adminNavItems.map((item) => (
              <NavLink 
                key={item.path} 
                to={item.path} 
                className={navLinkClass}
                onClick={handleNavClick}
              >
                <item.icon className="w-4 h-4" />
                <span className="text-sm">{item.label}</span>
              </NavLink>
            ))}
          </>
        )}
      </nav>

      <div className="mt-auto p-3 border-t border-zinc-800">
        <div className="flex items-center gap-2.5 p-2.5 rounded-lg bg-zinc-900/50">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-sm font-bold">
            {user?.full_name?.charAt(0) || 'U'}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-white truncate">{user?.full_name}</p>
            <p className="text-xs text-zinc-500 truncate flex items-center gap-1">
              {user?.role === 'master_admin' && <Crown className="w-3 h-3 text-purple-400" />}
              {user?.role?.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </p>
          </div>
        </div>
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
