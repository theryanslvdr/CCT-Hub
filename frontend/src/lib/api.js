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
  getDebugCalculation: () => api.get('/profit/debug-calculation'),
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
  // Member self-edit transactions
  getMyRecentTransactions: () => api.get('/profit/my-recent-transactions'),
  editMyTransaction: (txId, data) => api.put(`/profit/my-transactions/${txId}`, data),
  // Licensee
  getLicenseeWelcomeInfo: () => api.get('/profit/licensee/welcome-info'),
  markLicenseeWelcomeSeen: () => api.post('/profit/licensee/mark-welcome-seen'),
  getLicenseeDailyProjection: () => api.get('/profit/licensee/daily-projection'),
  getLicenseeYearProjections: (userId = null) => api.get('/profit/licensee/year-projections', { params: userId ? { user_id: userId } : {} }),
  // Admin: Get licensee projections for a specific license (used when simulating)
  getLicenseeProjectionsForLicense: (licenseId) => api.get(`/admin/licenses/${licenseId}/projections`),
};

// Family Account APIs
export const familyAPI = {
  getMembers: () => api.get('/family/members'),
  addMember: (data) => api.post('/family/members', data),
  updateMember: (id, data) => api.put(`/family/members/${id}`, data),
  removeMember: (id) => api.delete(`/family/members/${id}`),
  getMemberProjections: (id) => api.get(`/family/members/${id}/projections`),
  requestWithdrawal: (memberId, data) => api.post(`/family/members/${memberId}/withdraw`, data),
  getWithdrawals: () => api.get('/family/withdrawals'),
  approveWithdrawal: (id) => api.put(`/family/withdrawals/${id}/approve`),
  rejectWithdrawal: (id, reason) => api.put(`/family/withdrawals/${id}/reject`, null, { params: { reason } }),
  // Admin endpoints
  adminGetMembers: (userId) => api.get(`/admin/family/members/${userId}`),
  adminAddMember: (userId, data) => api.post(`/admin/family/members/${userId}`, data),
  adminUpdateMember: (userId, memberId, data) => api.put(`/admin/family/members/${userId}/${memberId}`, data),
  adminGetMemberProjections: (userId, memberId) => api.get(`/admin/family/members/${userId}/${memberId}/projections`),
  adminResetFamilyMember: (userId, memberId, data) => api.put(`/admin/family/members/${userId}/${memberId}/reset`, data),
  adminRemoveMember: (userId, memberId) => api.delete(`/admin/family/members/${userId}/${memberId}`),
  adminGetWithdrawals: () => api.get('/admin/family/withdrawals'),
  adminApproveWithdrawal: (id) => api.put(`/admin/family/withdrawals/${id}/approve`),
  adminRejectWithdrawal: (id, reason) => api.put(`/admin/family/withdrawals/${id}/reject`, null, { params: { reason } }),
};

// Rewards APIs
export const rewardsAPI = {
  getSummary: (userId) => api.get('/rewards/summary', { params: { user_id: userId } }),
  getLeaderboard: (userId) => api.get('/rewards/leaderboard', { params: { user_id: userId } }),
  getFullLeaderboard: (period = 'monthly', limit = 100) => api.get('/rewards/leaderboard/full', { params: { period, limit } }),
  getHistory: (userId = null, limit = 100) => api.get('/rewards/history', { params: { ...(userId ? { user_id: userId } : {}), limit } }),
  // Badges
  getBadgeDefinitions: () => api.get('/rewards/badges'),
  getUserBadges: (userId = null) => api.get('/rewards/badges/user', { params: userId ? { user_id: userId } : {} }),
  checkBadges: (userId = null) => api.post('/rewards/badges/check', null, { params: userId ? { user_id: userId } : {} }),
  // Admin
  adminSearchUsers: (q) => api.get('/rewards/admin/search-users', { params: { q, limit: 10 } }),
  adminLookup: (params) => api.get('/rewards/admin/lookup', { params }),
  adminSimulate: (data) => api.post('/rewards/admin/simulate', data),
  adminAdjustPoints: (data) => api.post('/rewards/admin/adjust-points', data),
  adminGetBadges: () => api.get('/rewards/admin/badges'),
  adminUpdateBadge: (badgeId, data) => api.put(`/rewards/admin/badges/${badgeId}`, data),
  generateStoreToken: () => api.post('/rewards/store-token'),
  // Platform sync
  adminSyncAllUsers: () => api.post('/rewards/admin/sync-all-users'),
  adminSyncUser: (userId) => api.post(`/rewards/admin/sync-user/${userId}`),
  adminGetSyncStatus: () => api.get('/rewards/admin/sync-status'),
  adminGetOverview: () => api.get('/rewards/admin/overview'),
  adminListMembers: (params = {}) => api.get('/rewards/admin/members', { params }),
  adminAuditTrail: (params = {}) => api.get('/rewards/admin/audit-trail', { params }),
  adminExportCsv: () => api.get('/rewards/admin/export-csv', { responseType: 'blob' }),
  adminResetPoints: (data) => api.post('/rewards/admin/reset-points', data),
  adminAwardBadge: (data) => api.post('/rewards/admin/award-badge', data),
  adminRevokeBadge: (data) => api.post('/rewards/admin/revoke-badge', data),
  adminEditStreakFreezes: (data) => api.post('/rewards/admin/edit-streak-freezes', data),
  systemCheck: () => api.post('/rewards/system-check'),
  // Streak Freezes
  getStreakFreezes: () => api.get('/rewards/streak-freezes'),
  purchaseStreakFreeze: (freezeType, quantity = 1) => api.post('/rewards/streak-freezes/purchase', { freeze_type: freezeType, quantity }),
  // Retroactive badge scan
  retroactiveScan: (userId = null) => api.post('/rewards/retroactive-scan', null, { params: userId ? { user_id: userId } : {} }),
  retroactiveScanAll: () => api.post('/rewards/retroactive-scan-all'),
  // Earning actions
  getEarningActions: () => api.get('/rewards/earning-actions'),
  claimAction: (actionId) => api.post(`/rewards/claim/${actionId}`),
};

// Forum APIs
export const forumAPI = {
  listPosts: (params = {}) => api.get('/forum/posts', { params }),
  createPost: (data) => api.post('/forum/posts', data),
  getPost: (postId) => api.get(`/forum/posts/${postId}`),
  editPost: (postId, data) => api.put(`/forum/posts/${postId}`, data),
  createComment: (postId, data) => api.post(`/forum/posts/${postId}/comments`, data),
  editComment: (commentId, data) => api.put(`/forum/comments/${commentId}`, data),
  deleteComment: (commentId) => api.delete(`/forum/comments/${commentId}`),
  markBestAnswer: (postId, commentId) => api.put(`/forum/posts/${postId}/best-answer/${commentId}`),
  closePost: (postId, data) => api.put(`/forum/posts/${postId}/close`, data),
  deletePost: (postId) => api.delete(`/forum/posts/${postId}`),
  pinPost: (postId, pinned) => api.put(`/forum/posts/${postId}/pin`, { pinned }),
  getCategories: () => api.get('/forum/categories'),
  searchUsers: (q) => api.get('/forum/users/search', { params: { q } }),
  getStats: () => api.get('/forum/stats'),
  searchSimilar: (q) => api.get('/forum/search-similar', { params: { q } }),
  searchSimilarFull: (title, content) => api.get('/forum/search-similar-full', { params: { title, content } }),
  aiCheckDuplicate: (title, content) => api.post('/forum/ai-check-duplicate', { title, content }),
  voteComment: (commentId, voteType) => api.post(`/forum/comments/${commentId}/vote`, { vote_type: voteType }),
  getVoters: (commentId) => api.get(`/forum/comments/${commentId}/voters`),
  mergePosts: (sourcePostId, targetPostId) => api.post('/forum/posts/merge', { source_post_id: sourcePostId, target_post_id: targetPostId }),
  validateSolution: (postId) => api.put(`/forum/posts/${postId}/validate-solution`),
  getPostDetails: (postId) => api.get(`/forum/posts/${postId}/details`),
};

// Publitio Image Upload APIs
export const publitioAPI = {
  uploadImage: (file, folder = 'general', onProgress = null) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('folder', folder);
    return api.post('/publitio/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: onProgress ? (e) => onProgress(Math.round((e.loaded * 100) / e.total)) : undefined,
    });
  },
  testConnection: () => api.get('/publitio/test'),
  listFolders: () => api.get('/publitio/folders'),
  createFolder: (name, parentFolder = null) => api.post('/publitio/folder/create', null, { params: { name, parent_folder: parentFolder } }),
  deleteFile: (fileId) => api.delete(`/publitio/file/${fileId}`),
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
  getSignalBlockStatus: () => api.get('/trade/signal-block-status'),
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
  getMemberStatsOverview: () => api.get('/admin/members/stats/overview'),
  getMemberDetails: (userId) => api.get(`/admin/members/${userId}`),
  getMemberSimulation: (userId) => api.get(`/admin/members/${userId}/simulate`),
  updateMember: (userId, data) => api.put(`/admin/members/${userId}`, data),
  upgradeRole: (data) => api.post('/admin/upgrade-role', data),
  downgradeRole: (userId) => api.post(`/admin/downgrade-role/${userId}`),
  unblockSignal: (userId, days = 7) => api.post(`/admin/members/${userId}/unblock-signal`, null, { params: { days } }),
  getActivityFeed: (since = '', limit = 50) => api.get('/admin/activity-feed', { params: { since, limit } }),
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
  getTeamTransactions: (page = 1, pageSize = 20, type = null, userSearch = null) => api.get('/admin/transactions', { 
    params: { page, page_size: pageSize, transaction_type: type, user_search: userSearch } 
  }),
  getTransactionStats: () => api.get('/admin/transactions/stats'),
  // Transaction Corrections
  getMemberRecentTransactions: (userId, limit = 5) => api.get(`/admin/members/${userId}/recent-transactions`, { params: { limit } }),
  correctTransaction: (txId, data) => api.put(`/admin/transactions/${txId}/correct`, data),
  deleteTransaction: (txId) => api.delete(`/admin/transactions/${txId}`),
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
  // Licensee Health Check (one-click diagnostic)
  licenseeHealthCheck: () => api.post('/admin/licensee-health-check'),
  // Force sync/recalculate licensee data
  forceSyncLicensee: (userId) => api.post(`/admin/licensee/${userId}/force-sync`),
  // Batch sync all licensees
  batchSyncAllLicensees: () => api.post('/admin/licensee/batch-sync-all'),
  // Run diagnostic for a licensee by email
  runDiagnostic: (email) => api.get(`/diagnostic/licensee/${encodeURIComponent(email)}`),
  // Smart Registration
  getPendingRegistrations: () => api.get('/admin/pending-registrations'),
  approveRegistration: (userId) => api.post(`/admin/approve-registration/${userId}`),
  rejectRegistration: (userId) => api.post(`/admin/reject-registration/${userId}`),
  // Admin Cleanup
  getCleanupOverview: () => api.get('/admin/cleanup-overview'),
  // Pending Proofs (AI Visual Review)
  getPendingProofs: (page = 1) => api.get(`/habits/admin/pending-proofs?page=${page}`),
  spotCheckProof: (completionId, action, reason = '') => api.post(`/habits/admin/spot-check/${completionId}`, { action, reason }),
  getSpotCheckStats: () => api.get('/habits/admin/spot-check-stats'),
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
    // Try settings route first, fallback to admin route
    return api.post('/settings/upload-pwa-icon', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).catch(() => api.post('/admin/pwa-icon/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }));
  },
  setPwaIconUrl: (url) => {
    return api.put('/settings/pwa-icon-url', { url })
      .catch(() => api.put('/admin/pwa-icon/url', { url }));
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
  // Notice Banner & Promotion Popup (public)
  getNoticeBanner: () => api.get('/settings/notice-banner'),
  getPromotionPopup: () => api.get('/settings/promotion-popup'),
  trackBannerEvent: (eventType, bannerType) => api.post('/settings/banner-analytics/track', null, { params: { event_type: eventType, banner_type: bannerType } }),
  getBannerAnalytics: (days = 30) => api.get('/settings/banner-analytics', { params: { days } }),
  getBookingEmbed: () => api.get('/settings/booking-embed'),
};

// Habit Tracker APIs
export const habitAPI = {
  getHabits: () => api.get('/habits/'),
  getStreak: () => api.get('/habits/streak'),
  completeHabit: (habitId, screenshotUrl = '') => api.post(`/habits/${habitId}/complete`, { screenshot_url: screenshotUrl }),
  uncompleteHabit: (habitId) => api.post(`/habits/${habitId}/uncomplete`),
  uploadScreenshot: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/habits/upload-screenshot', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
  },
  getSocialTasks: () => api.get('/habits/social-tasks'),
  completeSocialTask: (taskId) => api.post(`/habits/social-task/${taskId}/complete`),
  uncompleteSocialTask: (taskId) => api.post(`/habits/social-task/${taskId}/uncomplete`),
  // Fraud warnings
  getMyWarnings: () => api.get('/habits/my-warnings'),
  acknowledgeWarning: (warningId) => api.post(`/habits/acknowledge-warning/${warningId}`),
};

export const storeAPI = {
  getItems: () => api.get('/store/items'),
  purchase: (itemId) => api.post('/store/purchase', { item_id: itemId }),
  getMyCredits: () => api.get('/store/my-credits'),
};

// Admin Habit APIs
export const adminHabitAPI = {
  getHabits: () => api.get('/admin/habits'),
  createHabit: (data) => api.post('/admin/habits', data),
  updateHabit: (habitId, data) => api.put(`/admin/habits/${habitId}`, data),
  deleteHabit: (habitId) => api.delete(`/admin/habits/${habitId}`),
  activateHabit: (habitId) => api.post(`/admin/habits/${habitId}/activate`),
};

// Affiliate Center APIs
export const affiliateAPI = {
  getResources: () => api.get('/affiliate-resources'),
  getChatbase: () => api.get('/affiliate-chatbase-public'),
};

export const adminAffiliateAPI = {
  getResources: () => api.get('/admin/affiliate-resources'),
  createResource: (data) => api.post('/admin/affiliate-resources', data),
  updateResource: (id, data) => api.put(`/admin/affiliate-resources/${id}`, data),
  deleteResource: (id) => api.delete(`/admin/affiliate-resources/${id}`),
  getChatbase: () => api.get('/admin/affiliate-chatbase'),
  updateChatbase: (bot_id, enabled) => api.put('/admin/affiliate-chatbase', null, { params: { bot_id, enabled } }),
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

// Version check API (no auth required)
export const versionAPI = {
  getVersion: () => api.get('/version'),
};

export default api;

// Referral System API
export const referralAPI = {
  checkOnboarding: () => api.get('/referrals/check-onboarding'),
  getMyCode: () => api.get('/referrals/my-code'),
  setCode: (referralCode) => api.post('/referrals/set-code', { referral_code: referralCode }),
  setReferredBy: (referralCode) => api.post('/referrals/set-referred-by', { referral_code: referralCode }),
  awardHabitReward: () => api.post('/referrals/habit-reward'),
  // Admin
  getTree: () => api.get('/referrals/admin/tree'),
  getFlatList: (params) => api.get('/referrals/admin/flat-list', { params }),
  adminSetCode: (userId, referralCode) => api.post('/referrals/admin/set-code', { user_id: userId, referral_code: referralCode }),
  // Tracking & Leaderboard
  getTracking: () => api.get('/referrals/tracking'),
  getLeaderboard: () => api.get('/referrals/leaderboard'),
  getAdminStats: () => api.get('/referrals/admin/stats'),
  lookupMembers: (q) => api.get('/referrals/lookup-members', { params: { q } }),
  setInviter: (inviterId) => api.post('/referrals/set-inviter', { inviter_id: inviterId }),
  // Team System
  getMyTeam: () => api.get('/referrals/my-team'),
  getTeamRecommendations: () => api.get('/referrals/my-team/recommendations'),
  getTeamWeeklyReport: () => api.get('/referrals/my-team/weekly-report'),
};

// Quiz System API
export const quizAPI = {
  // Admin
  generate: (data) => api.post('/habits/quiz/admin/generate', data),
  getPool: (params) => api.get('/habits/quiz/admin/pool', { params }),
  approve: (quizIds) => api.post('/habits/quiz/admin/approve', { quiz_ids: quizIds }),
  reject: (quizIds, reason) => api.post('/habits/quiz/admin/reject', { quiz_ids: quizIds, reason }),
  edit: (quizId, data) => api.put(`/habits/quiz/admin/edit/${quizId}`, data),
  publish: (quizIds, date) => api.post('/habits/quiz/admin/publish', { quiz_ids: quizIds, date }),
  getPublished: (date) => api.get('/habits/quiz/admin/published', { params: { date } }),
  // Member
  getToday: () => api.get('/habits/quiz/today'),
  answer: (quizId, answer) => api.post(`/habits/quiz/${quizId}/answer`, { answer }),
};

// AI Features API
export const aiAPI = {
  // Phase 1
  getTradeCoach: (tradeId) => api.get(`/ai/trade-coach/${tradeId}`),
  getFinancialSummary: (period = 'weekly') => api.get('/ai/financial-summary', { params: { period } }),
  getBalanceForecast: () => api.get('/ai/balance-forecast'),
  getForumSummary: (postId) => api.get(`/ai/forum-summary/${postId}`),
  // Phase 2
  getSignalInsights: (signalId) => api.get(`/ai/signal-insights/${signalId}`),
  getTradeJournal: (period = 'daily') => api.get('/ai/trade-journal', { params: { period } }),
  getGoalAdvisor: (goalId) => api.get(`/ai/goal-advisor/${goalId}`),
  getAnomalyCheck: () => api.get('/ai/anomaly-check'),
  // Phase 3
  getAnswerSuggestion: (postId) => api.get(`/ai/answer-suggestion/${postId}`),
  getMemberRisk: (userId) => api.get(`/ai/member-risk/${userId}`),
  getDailyReport: () => api.get('/ai/daily-report'),
  smartNotification: (eventType, context) => api.post('/ai/smart-notification', { event_type: eventType, context }),
  getCommissionInsights: () => api.get('/ai/commission-insights'),
  getMilestoneMotivation: (goalId) => api.get(`/ai/milestone/${goalId}`),
};

// AI Assistant API (RyAI & zxAI)
export const aiAssistantAPI = {
  listAssistants: () => api.get('/ai-assistant/assistants'),
  chat: (data) => api.post('/ai-assistant/chat', data),
  getSessions: (assistantId) => api.get('/ai-assistant/sessions', { params: { assistant_id: assistantId } }),
  getSessionMessages: (sessionId) => api.get(`/ai-assistant/sessions/${sessionId}/messages`),
  deleteSession: (sessionId) => api.delete(`/ai-assistant/sessions/${sessionId}`),
  getPopularPrompts: (assistantId) => api.get('/ai-assistant/popular-prompts', { params: { assistant_id: assistantId } }),
  // Admin endpoints
  getAdminConfig: () => api.get('/ai-assistant/admin/config'),
  updateConfig: (assistantId, data) => api.put(`/ai-assistant/admin/config/${assistantId}`, data),
  getKnowledge: (assistantId) => api.get('/ai-assistant/admin/knowledge', { params: { assistant_id: assistantId } }),
  addTraining: (data) => api.post('/ai-assistant/admin/train', data),
  deleteKnowledge: (entryId) => api.delete(`/ai-assistant/admin/knowledge/${entryId}`),
  getUnanswered: (assistantId) => api.get('/ai-assistant/admin/unanswered', { params: { assistant_id: assistantId } }),
  answerUnanswered: (itemId, answer) => api.post(`/ai-assistant/admin/unanswered/${itemId}/answer`, { answer }),
  getStats: () => api.get('/ai-assistant/admin/stats'),
  getModels: () => api.get('/ai-assistant/models'),
};

// Public Member Profile
export const memberAPI = {
  getPublicProfile: (memberId) => api.get(`/users/member/${memberId}/public`),
};

// Daily Profit Summary
export const profitSummaryAPI = {
  getDailySummary: () => api.get('/profit/daily-summary'),
};

// Onboarding Checklist & Invite
export const onboardingAPI = {
  getChecklist: () => api.get('/onboarding/checklist'),
  updateStep: (data) => api.put('/onboarding/checklist/step', data),
  updateMerinCode: (code) => api.put('/onboarding/merin-code', { merin_referral_code: code }),
  getInviteLink: () => api.get('/onboarding/invite-link'),
};


