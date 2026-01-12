import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { useAuth } from './AuthContext';
import api from '@/lib/api';
import { toast } from 'sonner';

const BVEContext = createContext(null);

export const useBVE = () => {
  const context = useContext(BVEContext);
  if (!context) {
    throw new Error('useBVE must be used within BVEProvider');
  }
  return context;
};

export const BVEProvider = ({ children }) => {
  const { user, isSuperAdmin, isMasterAdmin } = useAuth();
  const [isInBVE, setIsInBVE] = useState(false);
  const [bveSnapshot, setBveSnapshot] = useState(null);
  const [bveSessionId, setBveSessionId] = useState(null);
  const [loading, setLoading] = useState(false);

  // Check if user can access BVE
  const canAccessBVE = isSuperAdmin() || isMasterAdmin();

  // Enter Beta Virtual Environment
  const enterBVE = useCallback(async () => {
    if (!canAccessBVE) {
      toast.error('You do not have permission to access Beta Virtual Environment');
      return false;
    }

    setLoading(true);
    try {
      // Create a BVE session on the backend
      const res = await api.post('/bve/enter');
      setBveSessionId(res.data.session_id);
      setBveSnapshot(res.data.snapshot);
      setIsInBVE(true);
      localStorage.setItem('bve_session', JSON.stringify({
        session_id: res.data.session_id,
        entered_at: new Date().toISOString()
      }));
      toast.success('Entered Beta Virtual Environment');
      return true;
    } catch (error) {
      toast.error('Failed to enter BVE: ' + (error.response?.data?.detail || error.message));
      return false;
    } finally {
      setLoading(false);
    }
  }, [canAccessBVE]);

  // Exit Beta Virtual Environment
  const exitBVE = useCallback(async () => {
    setLoading(true);
    try {
      if (bveSessionId) {
        await api.post('/bve/exit', { session_id: bveSessionId });
      }
      setIsInBVE(false);
      setBveSessionId(null);
      setBveSnapshot(null);
      localStorage.removeItem('bve_session');
      toast.success('Exited Beta Virtual Environment');
      return true;
    } catch (error) {
      toast.error('Failed to exit BVE');
      return false;
    } finally {
      setLoading(false);
    }
  }, [bveSessionId]);

  // Rewind to snapshot state
  const rewindBVE = useCallback(async () => {
    if (!bveSessionId) {
      toast.error('No active BVE session');
      return false;
    }

    setLoading(true);
    try {
      await api.post('/bve/rewind', { session_id: bveSessionId });
      toast.success('BVE state rewound to entry point');
      // Trigger a page refresh to reload data
      window.location.reload();
      return true;
    } catch (error) {
      toast.error('Failed to rewind BVE state');
      return false;
    } finally {
      setLoading(false);
    }
  }, [bveSessionId]);

  // Restore BVE session from localStorage on mount
  useEffect(() => {
    const savedSession = localStorage.getItem('bve_session');
    if (savedSession && canAccessBVE) {
      try {
        const session = JSON.parse(savedSession);
        // Check if session is still valid (less than 24 hours old)
        const enteredAt = new Date(session.entered_at);
        const now = new Date();
        const hoursSinceEntry = (now - enteredAt) / (1000 * 60 * 60);
        
        if (hoursSinceEntry < 24) {
          setBveSessionId(session.session_id);
          setIsInBVE(true);
        } else {
          localStorage.removeItem('bve_session');
        }
      } catch (e) {
        localStorage.removeItem('bve_session');
      }
    }
  }, [canAccessBVE]);

  // Get the API prefix for BVE mode
  const getApiPrefix = useCallback(() => {
    return isInBVE ? '/bve' : '';
  }, [isInBVE]);

  return (
    <BVEContext.Provider value={{
      isInBVE,
      bveSessionId,
      bveSnapshot,
      canAccessBVE,
      loading,
      enterBVE,
      exitBVE,
      rewindBVE,
      getApiPrefix
    }}>
      {children}
    </BVEContext.Provider>
  );
};

export default BVEProvider;
