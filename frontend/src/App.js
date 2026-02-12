import React, { useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import { WebSocketProvider } from "./contexts/WebSocketContext";
import { TradeCountdownProvider } from "./contexts/TradeCountdownContext";
import { BVEProvider } from "./contexts/BVEContext";
import { Toaster } from "./components/ui/sonner";
import { PWAInstallBanner } from "./lib/pwa";

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

// Layout
import { DashboardLayout } from "./components/layout/DashboardLayout";

function App() {
  // Register service worker for PWA
  useEffect(() => {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js').catch(() => {});
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
            
            {/* Admin routes */}
            <Route path="/admin/signals" element={<AdminSignalsPage />} />
            <Route path="/admin/members" element={<AdminMembersPage />} />
            <Route path="/admin/analytics" element={<AdminAnalyticsPage />} />
            <Route path="/admin/transactions" element={<AdminTransactionsPage />} />
            <Route path="/admin/api-center" element={<AdminAPICenterPage />} />
            <Route path="/admin/settings" element={<AdminSettingsPage />} />
            <Route path="/admin/licenses" element={<AdminLicensesPage />} />
            <Route path="/admin/daily-summary" element={<DailyTradeSummaryPage />} />
          </Route>

          {/* Default redirect */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
        </TradeCountdownProvider>
        </BVEProvider>
        </BrowserRouter>
        <Toaster position="top-right" richColors theme="dark" />
        <PWAInstallBanner />
      </WebSocketProvider>
    </AuthProvider>
  );
}

export default App;
