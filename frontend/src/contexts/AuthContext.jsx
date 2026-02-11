import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api from '@/lib/api';
import { storage } from '@/lib/utils';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Role hierarchy
const ROLE_HIERARCHY = {
  'member': 1,
  'user': 1,           // Legacy support
  'basic_admin': 2,
  'admin': 2,          // Legacy support
  'super_admin': 3,
  'master_admin': 4,
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [simulatedView, setSimulatedView] = useState(null); // For Master Admin to simulate member view

  // Initialize auth state from storage
  useEffect(() => {
    const initAuth = async () => {
      try {
        const token = storage.get('token');
        const savedUser = storage.get('user');
        
        if (token && savedUser) {
          // Verify token is still valid by fetching user data
          try {
            const response = await api.get('/auth/me');
            const freshUser = response.data;
            setUser(freshUser);
            storage.set('user', freshUser);
          } catch (error) {
            // Token is invalid, clear storage
            storage.remove('token');
            storage.remove('user');
            setUser(null);
          }
        }
      } catch (error) {
        console.error('Auth initialization error:', error);
      } finally {
        setLoading(false);
      }
    };

    initAuth();
  }, []);

  const login = useCallback(async (email, password) => {
    try {
      const response = await api.post('/auth/login', { email, password });
      const { access_token, user: userData } = response.data;
      
      storage.set('token', access_token);
      storage.set('user', userData);
      setUser(userData);
      
      return { success: true, user: userData };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Login failed. Please check your credentials.' 
      };
    }
  }, []);

  const register = useCallback(async (email, password, fullName, heartbeatEmail, secretCode) => {
    try {
      const response = await api.post('/auth/register', {
        email,
        password,
        full_name: fullName,
        heartbeat_email: heartbeatEmail,
        secret_code: secretCode,
      });
      const { access_token, user: userData } = response.data;
      
      storage.set('token', access_token);
      storage.set('user', userData);
      setUser(userData);
      
      return { success: true, user: userData };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Registration failed. Please try again.' 
      };
    }
  }, []);

  const logout = useCallback(() => {
    storage.remove('token');
    storage.remove('user');
    setUser(null);
    setSimulatedView(null);
  }, []);

  const updateUser = useCallback((userData) => {
    setUser(prev => ({ ...prev, ...userData }));
    storage.set('user', { ...user, ...userData });
  }, [user]);

  // Refresh user data from server (useful after profile updates or onboarding)
  const refreshUser = useCallback(async () => {
    try {
      const response = await api.get('/auth/me');
      const freshUser = response.data;
      setUser(freshUser);
      storage.set('user', freshUser);
      return { success: true, user: freshUser };
    } catch (error) {
      console.error('Failed to refresh user data:', error);
      return { success: false, error: error.message };
    }
  }, []);

  // Role-based access helpers
  const hasRole = useCallback((requiredRole) => {
    if (!user) return false;
    const userLevel = ROLE_HIERARCHY[user.role] || 0;
    const requiredLevel = ROLE_HIERARCHY[requiredRole] || 0;
    return userLevel >= requiredLevel;
  }, [user]);

  const isAdmin = useCallback(() => {
    return hasRole('basic_admin');
  }, [hasRole]);

  const isSuperAdmin = useCallback(() => {
    return hasRole('super_admin');
  }, [hasRole]);

  const isMasterAdmin = useCallback(() => {
    return user?.role === 'master_admin';
  }, [user]);

  const isMember = useCallback(() => {
    return user?.role === 'member' || user?.role === 'user';
  }, [user]);

  // Check if user can access a specific dashboard (for modular member access)
  const canAccessDashboard = useCallback((dashboardId) => {
    if (!user) return false;
    
    // Admin and above can access everything (except hidden for non-master)
    if (hasRole('basic_admin')) return true;
    
    // For normal members, check allowed_dashboards
    const allowedDashboards = user.allowed_dashboards || ['dashboard', 'profit_tracker', 'trade_monitor', 'profile'];
    return allowedDashboards.includes(dashboardId);
  }, [user, hasRole]);

  // Check if user can access hidden features (only master_admin)
  const canAccessHiddenFeatures = useCallback(() => {
    return user?.role === 'master_admin';
  }, [user]);

  // Master Admin: Simulate member view with their actual data
  const simulateMemberView = useCallback((memberData) => {
    if (!isMasterAdmin()) return;
    
    // If just a string (role), use basic simulation
    if (typeof memberData === 'string') {
      setSimulatedView({
        role: memberData,
        displayName: memberData.charAt(0).toUpperCase() + memberData.slice(1),
        allowed_dashboards: ['dashboard', 'profit_tracker', 'trade_monitor', 'profile'],
      });
    } else if (memberData.role && !memberData.id) {
      // Role-based simulation (no specific member)
      const roleBasedDashboards = {
        'member': ['dashboard', 'profit_tracker', 'trade_monitor', 'profile'],
        'basic_admin': ['dashboard', 'profit_tracker', 'trade_monitor', 'profile'],
        'super_admin': ['dashboard', 'profit_tracker', 'trade_monitor', 'profile'],
      };
      
      setSimulatedView({
        role: memberData.role,
        displayName: memberData.displayName || memberData.role,
        license_type: memberData.license_type || null,
        allowed_dashboards: roleBasedDashboards[memberData.role] || ['dashboard', 'profit_tracker', 'trade_monitor', 'profile'],
      });
    } else {
      // If object with member data, use full simulation
      setSimulatedView({
        role: 'member',
        memberId: memberData.id || memberData.memberId,
        memberName: memberData.full_name,
        displayName: memberData.full_name || memberData.displayName,
        accountValue: memberData.account_value,
        lotSize: memberData.lot_size,
        totalDeposits: memberData.total_deposits,
        totalProfit: memberData.total_profit,
        starting_amount: memberData.starting_amount, // Include starting amount for growth calculation
        license_type: memberData.license_type || null,
        allowed_dashboards: memberData.allowed_dashboards || ['dashboard', 'profit_tracker', 'trade_monitor', 'profile'],
        // Include licenseId for trade override API calls (P0 feature)
        licenseId: memberData.licenseId || null,
        // Include effective_start_date for Daily Projection filtering (P0 feature)
        effective_start_date: memberData.effective_start_date || null,
        // Include trading_type and trading_start_date for "New Trader" filtering
        trading_type: memberData.trading_type || null,
        trading_start_date: memberData.trading_start_date || null,
      });
    }
  }, [isMasterAdmin]);

  const exitSimulation = useCallback(() => {
    setSimulatedView(null);
  }, []);

  // Get effective role (considering simulation)
  const getEffectiveRole = useCallback(() => {
    if (simulatedView) return simulatedView.role;
    return user?.role;
  }, [user, simulatedView]);

  // Get simulated account value (for Trade Monitor/Profit Tracker)
  const getSimulatedAccountValue = useCallback(() => {
    if (simulatedView && simulatedView.accountValue !== undefined) {
      return simulatedView.accountValue;
    }
    return null; // Return null to use real data
  }, [simulatedView]);

  // Get simulated LOT size
  const getSimulatedLotSize = useCallback(() => {
    if (simulatedView && simulatedView.lotSize !== undefined) {
      return simulatedView.lotSize;
    }
    return null;
  }, [simulatedView]);

  // Get simulated total deposits
  const getSimulatedTotalDeposits = useCallback(() => {
    if (simulatedView && simulatedView.totalDeposits !== undefined) {
      return simulatedView.totalDeposits;
    }
    return null;
  }, [simulatedView]);

  // Get simulated total profit
  const getSimulatedTotalProfit = useCallback(() => {
    if (simulatedView && simulatedView.totalProfit !== undefined) {
      return simulatedView.totalProfit;
    }
    return null;
  }, [simulatedView]);

  // Get simulated member name
  const getSimulatedMemberName = useCallback(() => {
    return simulatedView?.memberName || null;
  }, [simulatedView]);

  // Get simulated member ID
  const getSimulatedMemberId = useCallback(() => {
    return simulatedView?.memberId || null;
  }, [simulatedView]);

  // Get effective allowed dashboards (considering simulation)
  const getEffectiveAllowedDashboards = useCallback(() => {
    if (simulatedView) return simulatedView.allowed_dashboards;
    return user?.allowed_dashboards;
  }, [user, simulatedView]);

  // Get token from storage
  const token = storage.get('token');

  const value = {
    user,
    token,
    loading,
    login,
    register,
    logout,
    updateUser,
    isAuthenticated: !!user,
    // Role helpers
    hasRole,
    isAdmin,
    isSuperAdmin,
    isMasterAdmin,
    isMember,
    canAccessDashboard,
    canAccessHiddenFeatures,
    // Simulation (Master Admin only)
    simulatedView,
    simulateMemberView,
    exitSimulation,
    getEffectiveRole,
    getEffectiveAllowedDashboards,
    getSimulatedAccountValue,
    getSimulatedLotSize,
    getSimulatedTotalDeposits,
    getSimulatedTotalProfit,
    getSimulatedMemberName,
    getSimulatedMemberId,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
