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
    const response = await api.post('/auth/login', { email, password });
    const { access_token, user: userData } = response.data;
    
    storage.set('token', access_token);
    storage.set('user', userData);
    setUser(userData);
    
    return userData;
  }, []);

  const register = useCallback(async (email, password, fullName, heartbeatEmail, secretCode) => {
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
    
    return userData;
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

  // Master Admin: Simulate member view
  const simulateMemberView = useCallback((memberRole = 'member') => {
    if (!isMasterAdmin()) return;
    setSimulatedView({
      role: memberRole,
      allowed_dashboards: ['dashboard', 'profit_tracker', 'trade_monitor', 'profile'],
    });
  }, [isMasterAdmin]);

  const exitSimulation = useCallback(() => {
    setSimulatedView(null);
  }, []);

  // Get effective role (considering simulation)
  const getEffectiveRole = useCallback(() => {
    if (simulatedView) return simulatedView.role;
    return user?.role;
  }, [user, simulatedView]);

  // Get effective allowed dashboards (considering simulation)
  const getEffectiveAllowedDashboards = useCallback(() => {
    if (simulatedView) return simulatedView.allowed_dashboards;
    return user?.allowed_dashboards;
  }, [user, simulatedView]);

  const value = {
    user,
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
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
