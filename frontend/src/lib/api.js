import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API_BASE = `${BACKEND_URL}/api`;

// Create axios instance
const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const tokenRaw = localStorage.getItem('token');
  if (tokenRaw) {
    // Token is stored as JSON string, so parse it
    try {
      const token = JSON.parse(tokenRaw);
      config.headers.Authorization = `Bearer ${token}`;
    } catch {
      // If not JSON, use as-is (backwards compatibility)
      config.headers.Authorization = `Bearer ${tokenRaw}`;
    }
  }
  return config;
});

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth APIs
export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  getMe: () => api.get('/auth/me'),
  verifyPassword: (password) => api.post('/auth/verify-password', { password }),
  secretUpgrade: (data) => api.post('/auth/secret-upgrade', data),
};

// User APIs
export const userAPI = {
  updateProfile: (data) => api.put('/users/profile', data),
  changePassword: (data) => api.post('/users/change-password', data),
  uploadProfilePicture: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/users/profile-picture', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};

// Profit Tracker APIs
export const profitAPI = {
  createDeposit: (data) => api.post('/profit/deposits', data),
  getDeposits: () => api.get('/profit/deposits'),
  getSummary: () => api.get('/profit/summary'),
  calculateExit: (lotSize) => api.post('/profit/calculate-exit', null, { params: { lot_size: lotSize } }),
  simulateWithdrawal: (data) => api.post('/profit/simulate-withdrawal', data),
};

// Trade Monitor APIs
export const tradeAPI = {
  logTrade: (data) => api.post('/trade/log', data),
  getLogs: (limit = 50) => api.get('/trade/logs', { params: { limit } }),
  getHistory: (page = 1, pageSize = 10) => api.get('/trade/history', { params: { page, page_size: pageSize } }),
  updateTimeEntered: (tradeId, timeEntered) => api.put(`/trade/logs/${tradeId}/time-entered`, { time_entered: timeEntered }),
  getStreak: () => api.get('/trade/streak'),
  getActiveSignal: () => api.get('/trade/active-signal'),
  getDailySummary: () => api.get('/trade/daily-summary'),
  forwardToProfit: (tradeId) => api.post('/trade/forward-to-profit', null, { params: { trade_id: tradeId } }),
};

// Admin APIs
export const adminAPI = {
  createSignal: (data) => api.post('/admin/signals', data),
  getSignals: () => api.get('/admin/signals'),
  getSignalsHistory: (page = 1, pageSize = 20) => api.get('/admin/signals/history', { params: { page, page_size: pageSize } }),
  getSignalsArchive: () => api.get('/admin/signals/archive'),
  archiveMonth: () => api.post('/admin/signals/archive-month'),
  deleteSignal: (id) => api.delete(`/admin/signals/${id}`),
  getMembers: () => api.get('/admin/members'),
  getMemberSimulation: (userId) => api.get(`/admin/members/${userId}/simulate`),
  upgradeRole: (data) => api.post('/admin/upgrade-role', data),
  downgradeRole: (userId) => api.post(`/admin/downgrade-role/${userId}`),
  // Analytics
  getTeamAnalytics: () => api.get('/admin/analytics/team'),
  getMissedTrades: () => api.get('/admin/analytics/missed-trades'),
  notifyMissedTrade: (userId) => api.post('/admin/analytics/notify-missed', { user_id: userId }),
  getGrowthData: (startDate, endDate) => api.get('/admin/analytics/growth-data', { 
    params: { start_date: startDate, end_date: endDate } 
  }),
  getMemberAnalytics: (userId) => api.get(`/admin/analytics/member/${userId}`),
  getRecentTeamTrades: (page = 1, pageSize = 20) => api.get('/admin/analytics/recent-trades', { params: { page, page_size: pageSize } }),
  archiveTrades: () => api.post('/admin/analytics/archive-trades'),
};

// Debt Management APIs
export const debtAPI = {
  create: (data) => api.post('/debt', data),
  getAll: () => api.get('/debt'),
  makePayment: (debtId, amount) => api.post(`/debt/${debtId}/payment`, null, { params: { amount } }),
  getPlan: () => api.get('/debt/plan'),
};

// Goals (Profit Planner) APIs
export const goalsAPI = {
  create: (data) => api.post('/goals', data),
  getAll: () => api.get('/goals'),
  contribute: (goalId, amount) => api.post(`/goals/${goalId}/contribute`, null, { params: { amount } }),
  getPlan: (goalId) => api.get(`/goals/${goalId}/plan`),
};

// Currency APIs
export const currencyAPI = {
  getRates: (base = 'USD') => api.get('/currency/rates', { params: { base } }),
  convert: (amount, from, to) => api.post('/currency/convert', null, { params: { amount, from_currency: from, to_currency: to } }),
};

// Settings APIs
export const settingsAPI = {
  getPlatform: () => api.get('/settings/platform'),
  updatePlatform: (data) => api.put('/settings/platform', data),
  uploadLogo: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/settings/upload-logo', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  uploadFavicon: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/settings/upload-favicon', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};

// API Center APIs
export const apiCenterAPI = {
  createConnection: (data) => api.post('/api-center/connections', data),
  getConnections: () => api.get('/api-center/connections'),
  deleteConnection: (id) => api.delete(`/api-center/connections/${id}`),
  sendToConnection: (id, payload) => api.post(`/api-center/connections/${id}/send`, payload),
};

// Email API
export const emailAPI = {
  send: (to, subject, body) => api.post('/send-email', null, { params: { to, subject, body } }),
};

export default api;
