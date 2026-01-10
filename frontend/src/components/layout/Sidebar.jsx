import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import {
  LayoutDashboard,
  TrendingUp,
  Activity,
  Target,
  CreditCard,
  Users,
  Radio,
  Settings,
  Link2,
  LogOut,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
} from 'lucide-react';
import { cn } from '../../lib/utils';

const navItems = [
  { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard', roles: ['user', 'admin', 'super_admin'] },
  { path: '/profit-tracker', icon: TrendingUp, label: 'Profit Tracker', roles: ['user', 'admin', 'super_admin'] },
  { path: '/trade-monitor', icon: Activity, label: 'Trade Monitor', roles: ['user', 'admin', 'super_admin'] },
  { path: '/goals', icon: Target, label: 'Profit Planner', roles: ['user', 'admin', 'super_admin'] },
  { path: '/debt', icon: CreditCard, label: 'Debt Management', roles: ['user', 'admin', 'super_admin'] },
  { divider: true },
  { path: '/admin/signals', icon: Radio, label: 'Trading Signals', roles: ['admin', 'super_admin'] },
  { path: '/admin/members', icon: Users, label: 'Members', roles: ['admin', 'super_admin'] },
  { path: '/admin/api-center', icon: Link2, label: 'API Center', roles: ['admin', 'super_admin'] },
  { path: '/admin/settings', icon: Settings, label: 'Platform Settings', roles: ['super_admin'] },
];

export const Sidebar = ({ collapsed, onToggle }) => {
  const { user, logout, isAdmin } = useAuth();
  const location = useLocation();

  const filteredItems = navItems.filter(item => {
    if (item.divider) return isAdmin;
    return item.roles.includes(user?.role || 'user');
  });

  return (
    <aside className={cn(
      "fixed left-0 top-0 h-full bg-zinc-950 border-r border-zinc-800/50 z-40 transition-all duration-300",
      collapsed ? "w-16" : "w-64"
    )}>
      {/* Logo */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-zinc-800/50">
        {!collapsed && (
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
              <TrendingUp className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-white text-lg">CrossCurrent</span>
          </div>
        )}
        <button
          onClick={onToggle}
          className="p-2 hover:bg-white/5 rounded-lg transition-colors text-zinc-400 hover:text-white"
          data-testid="sidebar-toggle"
        >
          {collapsed ? <ChevronRight className="w-5 h-5" /> : <ChevronLeft className="w-5 h-5" />}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 overflow-y-auto scrollbar-dark">
        {filteredItems.map((item, index) => {
          if (item.divider) {
            return (
              <div key={`divider-${index}`} className="my-2 mx-4 border-t border-zinc-800/50" />
            );
          }

          const Icon = item.icon;
          const isActive = location.pathname === item.path || location.pathname.startsWith(item.path + '/');

          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={cn(
                "flex items-center gap-3 mx-2 px-3 py-2.5 rounded-lg transition-all",
                isActive
                  ? "bg-blue-600/10 text-blue-400 border border-blue-500/20"
                  : "text-zinc-400 hover:text-white hover:bg-white/5"
              )}
              data-testid={`nav-${item.path.replace(/\//g, '-')}`}
            >
              <Icon className={cn("w-5 h-5 flex-shrink-0", collapsed && "mx-auto")} />
              {!collapsed && <span className="font-medium">{item.label}</span>}
            </NavLink>
          );
        })}
      </nav>

      {/* User section */}
      <div className="border-t border-zinc-800/50 p-4">
        {!collapsed && (
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center text-white font-medium">
              {user?.full_name?.charAt(0) || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">{user?.full_name}</p>
              <div className="flex items-center gap-1">
                {user?.role !== 'user' && <ShieldCheck className="w-3 h-3 text-blue-400" />}
                <p className="text-xs text-zinc-500 capitalize">{user?.role}</p>
              </div>
            </div>
          </div>
        )}
        <button
          onClick={logout}
          className={cn(
            "flex items-center gap-3 w-full px-3 py-2 rounded-lg text-zinc-400 hover:text-red-400 hover:bg-red-500/10 transition-all",
            collapsed && "justify-center"
          )}
          data-testid="logout-button"
        >
          <LogOut className="w-5 h-5" />
          {!collapsed && <span>Logout</span>}
        </button>
      </div>
    </aside>
  );
};
