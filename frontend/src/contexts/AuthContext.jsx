import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authAPI } from '@/lib/api';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

// Storage helpers that work with localStorage directly
const getStoredToken = () => {
  try {
    return localStorage.getItem('crosscurrent_token');
  } catch {
    return null;
  }
};

const setStoredToken = (token) => {
  try {
    if (token) {
      localStorage.setItem('crosscurrent_token', token);
      localStorage.setItem('token', token); // Keep for API
    } else {
      localStorage.removeItem('crosscurrent_token');
      localStorage.removeItem('token');
    }
  } catch (e) {
    console.error('Failed to store token:', e);
  }
};

const getStoredUser = () => {
  try {
    const user = localStorage.getItem('crosscurrent_user');
    return user ? JSON.parse(user) : null;
  } catch {
    return null;
  }
};

const setStoredUser = (user) => {
  try {
    if (user) {
      localStorage.setItem('crosscurrent_user', JSON.stringify(user));
    } else {
      localStorage.removeItem('crosscurrent_user');
    }
  } catch (e) {
    console.error('Failed to store user:', e);
  }
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => getStoredUser());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const checkAuth = useCallback(async () => {
    try {
      const token = getStoredToken();
      if (!token) {
        setLoading(false);
        return;
      }

      // Set token for API calls
      localStorage.setItem('token', token);
      
      const response = await authAPI.getMe();
      setUser(response.data);
      setStoredUser(response.data);
    } catch (err) {
      console.error('Auth check failed:', err);
      // Clear stored data on auth failure
      setStoredToken(null);
      setStoredUser(null);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const login = async (email, password) => {
    try {
      setError(null);
      const response = await authAPI.login({ email, password });
      const { access_token, user: userData } = response.data;
      
      // Store token and user
      setStoredToken(access_token);
      setStoredUser(userData);
      setUser(userData);
      
      return { success: true };
    } catch (err) {
      const message = err.response?.data?.detail || 'Login failed';
      setError(message);
      return { success: false, error: message };
    }
  };

  const register = async (data) => {
    try {
      setError(null);
      const response = await authAPI.register(data);
      const { access_token, user: userData } = response.data;
      
      // Store token and user
      setStoredToken(access_token);
      setStoredUser(userData);
      setUser(userData);
      
      return { success: true };
    } catch (err) {
      const message = err.response?.data?.detail || 'Registration failed';
      setError(message);
      return { success: false, error: message };
    }
  };

  const logout = () => {
    setStoredToken(null);
    setStoredUser(null);
    setUser(null);
  };

  const updateUser = (updates) => {
    const updatedUser = { ...user, ...updates };
    setUser(updatedUser);
    setStoredUser(updatedUser);
  };

  // Impersonation for super admins
  const impersonateUser = async (targetUserId, targetUserData) => {
    // Store original admin data
    localStorage.setItem('original_admin_token', getStoredToken());
    localStorage.setItem('original_admin_user', JSON.stringify(user));
    
    // Set impersonated user (in real impl, would get a token from backend)
    setUser({ ...targetUserData, impersonating: true });
    setStoredUser({ ...targetUserData, impersonating: true });
  };

  const stopImpersonation = () => {
    const originalToken = localStorage.getItem('original_admin_token');
    const originalUser = JSON.parse(localStorage.getItem('original_admin_user') || 'null');
    
    if (originalToken && originalUser) {
      setStoredToken(originalToken);
      setStoredUser(originalUser);
      setUser(originalUser);
      
      localStorage.removeItem('original_admin_token');
      localStorage.removeItem('original_admin_user');
    }
  };

  const isAdmin = user?.role === 'admin' || user?.role === 'super_admin';
  const isSuperAdmin = user?.role === 'super_admin';
  const isImpersonating = user?.impersonating === true;

  return (
    <AuthContext.Provider value={{
      user,
      loading,
      error,
      login,
      register,
      logout,
      updateUser,
      impersonateUser,
      stopImpersonation,
      isAdmin,
      isSuperAdmin,
      isImpersonating,
      isAuthenticated: !!user,
    }}>
      {children}
    </AuthContext.Provider>
  );
};
