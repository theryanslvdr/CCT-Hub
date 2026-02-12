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
  // License registration
  validateLicenseInvite: (code) => api.get(`/auth/license-invite/${code}`),
  registerWithLicense: (data) => {
    const formData = new FormData();
    Object.keys(data).forEach(key => {
      formData.append(key, data[key]);
    });
    return api.post('/auth/register-with-license', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
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
  getSummary: () => api.get('/profit/summary'),
  getDeposits: () => api.get('/profit/deposits'),
  createDeposit: (data) => api.post('/profit/deposits', data),
  addDeposit: (data) => api.post('/profit/deposits', data),
  deleteDeposit: (id) => api.delete(`/profit/deposits/${id}`),
  getWithdrawals: () => api.get('/profit/withdrawals'),
  recordWithdrawal: (data) => api.post('/profit/withdrawal', data),
  confirmWithdrawal: (id, data) => api.post(`/profit/withdrawal/${id}/confirm`, data),
  getTrades: () => api.get('/profit/trades'),
  recordTrade: (data) => api.post('/profit/trades', data),
  calculateExit: (lotSize) => api.post('/profit/calculate-exit', null, { params: { lot_size: lotSize } }),
  simulateWithdrawal: (data) => api.post('/profit/simulate-withdrawal', data),
  getRates: () => api.get('/profit/rates'),
  getLicenseProjections: () => api.get('/profit/license-projections'),
  getMasterAdminTrades: (startDate, endDate) => api.get('/profit/master-admin-trades', { params: { start_date: startDate, end_date: endDate } }),
  getReportImage: (period = 'monthly', userId = null) => api.get(`/admin/analytics/report/image`, { params: { period, user_id: userId }, responseType: 'blob' }),
  getReportBase64: (period = 'monthly', userId = null) => api.get('/admin/analytics/report/base64', { params: { period, user_id: userId } }),
  // Virtual Share Distribution (VSD) - Master Admin only
  getVSD: () => api.get('/profit/vsd'),
  // Balance calculation endpoints (authoritative backend calculation)
  getBalanceOnDate: (date, userId = null) => api.get('/profit/balance-on-date', { params: { date, user_id: userId } }),
  getDailyBalances: (startDate, endDate, userId = null) => api.get('/profit/daily-balances', { params: { start_date: startDate, end_date: endDate, user_id: userId } }),
  // Onboarding
  completeOnboarding: (data) => api.post('/profit/complete-onboarding', data),
  getOnboardingStatus: () => api.get('/profit/onboarding-status'),
  // Licensee
  getLicenseeWelcomeInfo: () => api.get('/profit/licensee/welcome-info'),
  markLicenseeWelcomeSeen: () => api.post('/profit/licensee/mark-welcome-seen'),
  getLicenseeDailyProjection: () => api.get('/profit/licensee/daily-projection'),
  // Admin: Get licensee projections for a specific license (used when simulating)
  getLicenseeProjectionsForLicense: (licenseId) => api.get(`/admin/licenses/${licenseId}/projections`),
};

// Trade Monitor APIs
export const tradeAPI = {
  logTrade: (data) => api.post('/trade/log', data),
  getLogs: (limit = 50, userId = null) => {
    const params = { limit };
    if (userId) params.user_id = userId;
    return api.get('/trade/logs', { params });
  },
  getHistory: (page = 1, pageSize = 10, userId = null) => {
    const params = { page, page_size: pageSize };
    if (userId) params.user_id = userId;
    return api.get('/trade/history', { params });
  },
  updateTimeEntered: (tradeId, timeEntered) => api.put(`/trade/logs/${tradeId}/time-entered`, { time_entered: timeEntered }),
  getStreak: (userId = null) => {
    const params = userId ? { user_id: userId } : {};
    return api.get('/trade/streak', { params });
  },
  getActiveSignal: () => api.get('/trade/active-signal'),
  getDailySummary: (userId = null) => {
    const params = userId ? { user_id: userId } : {};
    return api.get('/trade/daily-summary', { params });
  },
  forwardToProfit: (tradeId, isBve = false) => api.post('/trade/forward-to-profit', null, { params: { trade_id: tradeId, is_bve: isBve } }),
  getMissedTradeStatus: () => api.get('/trade/missed-trade-status'),
  logMissedTrade: (data) => api.post('/trade/log-missed-trade', null, { params: data }),
  resetTrade: (tradeId) => api.delete(`/trade/reset/${tradeId}`),
  requestTradeChange: (data) => api.post('/trade/request-change', data),
  // Undo trade by date
  undoTradeByDate: (date) => api.delete(`/trade/undo-by-date/${date}`),
  // User holidays
  getHolidays: () => api.get('/trade/holidays'),
  addHoliday: (date, reason) => api.post('/trade/holidays', null, { params: { date, reason } }),
  removeHoliday: (date) => api.delete(`/trade/holidays/${date}`),
  // Global holidays (read-only for users)
  getGlobalHolidays: () => api.get('/trade/global-holidays'),
  // Trading products (read-only for users)
  getTradingProducts: () => api.get('/trade/trading-products'),
};

// Admin APIs
export const adminAPI = {
  createSignal: (data) => api.post('/admin/signals', data),
  getSignals: () => api.get('/admin/signals'),
  getSignalsHistory: (page = 1, pageSize = 20) => api.get('/admin/signals/history', { params: { page, page_size: pageSize } }),
  getSignalsArchive: () => api.get('/admin/signals/archive'),
  archiveMonth: () => api.post('/admin/signals/archive-month'),
  deleteSignal: (id) => api.delete(`/admin/signals/${id}`),
  updateSignal: (id, data) => api.put(`/admin/signals/${id}`, data),
  getMembers: () => api.get('/admin/members'),
  getMemberDetails: (userId) => api.get(`/admin/members/${userId}`),
  getMemberSimulation: (userId) => api.get(`/admin/members/${userId}/simulate`),
  updateMember: (userId, data) => api.put(`/admin/members/${userId}`, data),
  upgradeRole: (data) => api.post('/admin/upgrade-role', data),
  downgradeRole: (userId) => api.post(`/admin/downgrade-role/${userId}`),
  // Global holidays (Master Admin)
  getGlobalHolidays: () => api.get('/admin/global-holidays'),
  addGlobalHoliday: (date, reason) => api.post('/admin/global-holidays', null, { params: { date, reason } }),
  removeGlobalHoliday: (date) => api.delete(`/admin/global-holidays/${date}`),
  // Trading products (Master Admin)
  getTradingProducts: () => api.get('/admin/trading-products'),
  addTradingProduct: (name) => api.post('/admin/trading-products', null, { params: { name } }),
  removeTradingProduct: (productId) => api.delete(`/admin/trading-products/${productId}`),
  updateTradingProduct: (productId, data) => api.put(`/admin/trading-products/${productId}`, null, { params: data }),
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
  // Notifications
  getNotifications: (limit = 50, unreadOnly = false) => api.get('/admin/notifications', { params: { limit, unread_only: unreadOnly } }),
  getTopPerformers: (limit = 10, excludeNonTraders = true) => api.get('/admin/top-performers', { params: { limit, exclude_non_traders: excludeNonTraders } }),
  markNotificationRead: (notificationId) => api.put(`/admin/notifications/${notificationId}/read`),
  markAllNotificationsRead: () => api.put('/admin/notifications/read-all'),
  // Team Transactions
  getTeamTransactions: (page = 1, pageSize = 20, type = null) => api.get('/admin/transactions', { 
    params: { page, page_size: pageSize, transaction_type: type } 
  }),
  getTransactionStats: () => api.get('/admin/transactions/stats'),
  // Licenses
  getLicenses: () => api.get('/admin/licenses'),
  createLicense: (data) => api.post('/admin/licenses', data),
  getLicenseDetails: (licenseId) => api.get(`/admin/licenses/${licenseId}`),
  updateLicense: (licenseId, data) => api.put(`/admin/licenses/${licenseId}`, null, { params: data }),
  deleteLicense: (licenseId) => api.delete(`/admin/licenses/${licenseId}`),
  changeLicenseType: (licenseId, data) => api.post(`/admin/licenses/${licenseId}/change-type`, data),
  updateLicenseEffectiveStartDate: (licenseId, effective_start_date) => api.put(`/admin/licenses/${licenseId}/effective-start-date`, { effective_start_date }),
  // License Invites
  getLicenseInvites: () => api.get('/admin/license-invites'),
  createLicenseInvite: (data) => api.post('/admin/license-invites', data),
  getLicenseInviteDetails: (inviteId) => api.get(`/admin/license-invites/${inviteId}`),
  updateLicenseInvite: (inviteId, data) => api.put(`/admin/license-invites/${inviteId}`, data),
  revokeLicenseInvite: (inviteId) => api.post(`/admin/license-invites/${inviteId}/revoke`),
  renewLicenseInvite: (inviteId, duration) => api.post(`/admin/license-invites/${inviteId}/renew`, null, { params: { new_duration: duration } }),
  resendLicenseInvite: (inviteId) => api.post(`/admin/license-invites/${inviteId}/resend`),
  deleteLicenseInvite: (inviteId) => api.delete(`/admin/license-invites/${inviteId}`),
  resetLicenseBalance: (licenseId, data) => api.post(`/admin/licenses/${licenseId}/reset-balance`, data),
  // License Trade Overrides
  getLicenseTradeOverrides: (licenseId) => api.get(`/admin/licenses/${licenseId}/trade-overrides`),
  setLicenseTradeOverride: (licenseId, data) => api.post(`/admin/licenses/${licenseId}/trade-overrides`, data),
  deleteLicenseTradeOverride: (licenseId, date) => api.delete(`/admin/licenses/${licenseId}/trade-overrides/${date}`),
  // Licensee Transactions
  getLicenseeTransactions: () => api.get('/admin/licensee-transactions'),
  addTransactionFeedback: (txId, formData) => api.post(`/admin/licensee-transactions/${txId}/feedback`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  approveTransaction: (txId) => api.post(`/admin/licensee-transactions/${txId}/approve`),
  completeTransaction: (txId, formData) => api.post(`/admin/licensee-transactions/${txId}/complete`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  updateLicenseeTransaction: (txId, data) => api.put(`/admin/licensee-transactions/${txId}`, data),
  deleteLicenseeTransaction: (txId) => api.delete(`/admin/licensee-transactions/${txId}`),
};

// Licensee APIs (for licensed users)
export const licenseeAPI = {
  getMyTransactions: () => api.get('/profit/licensee/transactions'),
  submitDeposit: (formData) => api.post('/profit/licensee/deposit', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  submitWithdrawal: (formData) => api.post('/profit/licensee/withdrawal', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  confirmTransaction: (txId) => api.post(`/profit/licensee/transactions/${txId}/confirm`),
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
  get: () => api.get('/settings/platform'),
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
  uploadPwaIcon: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/settings/upload-pwa-icon', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  // Email Templates
  getEmailTemplates: () => api.get('/settings/email-templates'),
  updateEmailTemplate: (type, data) => api.put(`/settings/email-templates/${type}`, data),
  sendTestEmail: (data) => api.post('/settings/email-templates/test', data),
  // Email History
  getEmailHistory: (page = 1, pageSize = 20) => api.get('/settings/email-history', { params: { page, page_size: pageSize } }),
  clearEmailHistory: () => api.delete('/settings/email-history'),
  // Integration Tests
  testEmailit: () => api.post('/settings/test-emailit'),
  testCloudinary: () => api.post('/settings/test-cloudinary'),
  testHeartbeat: () => api.post('/settings/test-heartbeat'),
};

// BVE (Beta Virtual Environment) APIs
export const bveAPI = {
  enter: () => api.post('/bve/enter'),
  exit: (sessionId) => api.post('/bve/exit', { session_id: sessionId }),
  rewind: (sessionId) => api.post('/bve/rewind', { session_id: sessionId }),
  getSignals: () => api.get('/bve/signals'),
  createSignal: (data) => api.post('/bve/signals', data),
  updateSignal: (id, data) => api.put(`/bve/signals/${id}`, data),
  getActiveSignal: () => api.get('/bve/active-signal'),
  getSummary: () => api.get('/bve/summary'),
  logTrade: (data) => api.post('/bve/trade/log', data),
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
