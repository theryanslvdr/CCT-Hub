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
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
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
};

// User APIs
export const userAPI = {
  updateProfile: (data) => api.put('/users/profile', data),
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
  getActiveSignal: () => api.get('/trade/active-signal'),
  getDailySummary: () => api.get('/trade/daily-summary'),
  forwardToProfit: (tradeId) => api.post('/trade/forward-to-profit', null, { params: { trade_id: tradeId } }),
};

// Admin APIs
export const adminAPI = {
  createSignal: (data) => api.post('/admin/signals', data),
  getSignals: () => api.get('/admin/signals'),
  deleteSignal: (id) => api.delete(`/admin/signals/${id}`),
  getMembers: () => api.get('/admin/members'),
  upgradeRole: (data) => api.post('/admin/upgrade-role', data),
  downgradeRole: (userId) => api.post(`/admin/downgrade-role/${userId}`),
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
