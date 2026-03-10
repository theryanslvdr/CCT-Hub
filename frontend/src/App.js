import React, { useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import { WebSocketProvider } from "./contexts/WebSocketContext";
import { TradeCountdownProvider } from "./contexts/TradeCountdownContext";
import { BVEProvider } from "./contexts/BVEContext";
import { Toaster } from "./components/ui/sonner";
import { PWAInstallBanner } from "./lib/pwa";
import { VersionBanner } from "./components/VersionBanner";
import ReferralOnboardingModal from "./components/ReferralOnboardingModal";

// Pages
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { LicenseRegistrationPage } from "./pages/LicenseRegistrationPage";
import { DashboardPage } from "./pages/DashboardPage";
import { ProfitTrackerPage } from "./pages/ProfitTrackerPage";
import { TradeMonitorPage } from "./pages/TradeMonitorPage";
import { DebtManagementPage } from "./pages/DebtManagementPage";
import { ProfitPlannerPage } from "./pages/ProfitPlannerPage";
import { ProfilePage } from "./pages/ProfilePage";
import { LicenseeAccountPage } from "./pages/LicenseeAccountPage";
import { NotificationsPage } from "./pages/NotificationsPage";

// Admin Pages
import { AdminSignalsPage } from "./pages/admin/AdminSignalsPage";
import { AdminMembersPage } from "./pages/admin/AdminMembersPage";
import { AdminAPICenterPage } from "./pages/admin/AdminAPICenterPage";
import { AdminSettingsPage } from "./pages/admin/AdminSettingsPage";
import { AdminAnalyticsPage } from "./pages/admin/AdminAnalyticsPage";
import { AdminTransactionsPage } from "./pages/admin/AdminTransactionsPage";
import { AdminLicensesPage } from "./pages/admin/AdminLicensesPage";
import { DailyTradeSummaryPage } from "./pages/admin/DailyTradeSummaryPage";
import HabitTrackerPage from "./pages/HabitTrackerPage";
import AffiliateCenterPage from "./pages/AffiliateCenterPage";
import FamilyAccountsPage from "./pages/FamilyAccountsPage";
import SystemCheckPage from "./pages/admin/SystemCheckPage";
import SystemHealthPage from "./pages/admin/SystemHealthPage";
import MyRewardsPage from "./pages/MyRewardsPage";
import LeaderboardPage from "./pages/LeaderboardPage";
import RewardsAdminPage from "./pages/admin/RewardsAdminPage";
import ReferralTreePage from "./pages/admin/ReferralTreePage";
import QuizManagementPage from "./pages/admin/QuizManagementPage";
import ForumListPage from "./pages/ForumListPage";
import ForumPostPage from "./pages/ForumPostPage";

// Layout
import { DashboardLayout } from "./components/layout/DashboardLayout";

function App() {
  // Register service worker for PWA
  useEffect(() => {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/service-worker.js').catch(() => {});
    }
    // Dynamic manifest - try settings route, fallback to admin route, then static
    const manifestLink = document.querySelector('link[rel="manifest"]');
    if (manifestLink) {
      fetch(`${process.env.REACT_APP_BACKEND_URL}/api/settings/manifest.json`)
        .then(r => { if (r.ok) manifestLink.href = `${process.env.REACT_APP_BACKEND_URL}/api/settings/manifest.json`; else throw new Error(); })
        .catch(() => {
          fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/pwa-manifest`)
            .then(r => { if (r.ok) manifestLink.href = `${process.env.REACT_APP_BACKEND_URL}/api/admin/pwa-manifest`; })
            .catch(() => {});
        });
    }
  }, []);

  return (
    <AuthProvider>
      <WebSocketProvider>
        <BrowserRouter>
          <BVEProvider>
          <TradeCountdownProvider>
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/register/license/:code" element={<LicenseRegistrationPage />} />

          {/* Protected routes */}
          <Route element={<DashboardLayout />}>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/profit-tracker" element={<ProfitTrackerPage />} />
            <Route path="/trade-monitor" element={<TradeMonitorPage />} />
            <Route path="/goals" element={<ProfitPlannerPage />} />
            <Route path="/debt" element={<DebtManagementPage />} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/licensee-account" element={<LicenseeAccountPage />} />
            <Route path="/notifications" element={<NotificationsPage />} />
            <Route path="/habits" element={<HabitTrackerPage />} />
            <Route path="/affiliate" element={<AffiliateCenterPage />} />
            <Route path="/family-accounts" element={<FamilyAccountsPage />} />
            <Route path="/my-rewards" element={<MyRewardsPage />} />
            <Route path="/leaderboard" element={<LeaderboardPage />} />
            <Route path="/forum" element={<ForumListPage />} />
            <Route path="/forum/:postId" element={<ForumPostPage />} />
            
            {/* Admin routes */}
            <Route path="/admin/signals" element={<AdminSignalsPage />} />
            <Route path="/admin/members" element={<AdminMembersPage />} />
            <Route path="/admin/analytics" element={<AdminAnalyticsPage />} />
            <Route path="/admin/transactions" element={<AdminTransactionsPage />} />
            <Route path="/admin/api-center" element={<AdminAPICenterPage />} />
            <Route path="/admin/settings" element={<AdminSettingsPage />} />
            <Route path="/admin/licenses" element={<AdminLicensesPage />} />
            <Route path="/admin/daily-summary" element={<DailyTradeSummaryPage />} />
            <Route path="/admin/system-check" element={<SystemCheckPage />} />
            <Route path="/admin/system-health" element={<SystemHealthPage />} />
            <Route path="/admin/rewards" element={<RewardsAdminPage />} />
            <Route path="/admin/referrals" element={<ReferralTreePage />} />
            <Route path="/admin/quizzes" element={<QuizManagementPage />} />
          </Route>

          {/* Default redirect */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
        </TradeCountdownProvider>
        </BVEProvider>
        </BrowserRouter>
        <Toaster position="top-right" richColors theme="dark" />
        <ReferralOnboardingModal />
        <PWAInstallBanner />
        <VersionBanner />
      </WebSocketProvider>
    </AuthProvider>
  );
}

export default App;
