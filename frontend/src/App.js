import React from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import { Toaster } from "./components/ui/sonner";

// Pages
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { DashboardPage } from "./pages/DashboardPage";
import { ProfitTrackerPage } from "./pages/ProfitTrackerPage";
import { TradeMonitorPage } from "./pages/TradeMonitorPage";
import { DebtManagementPage } from "./pages/DebtManagementPage";
import { ProfitPlannerPage } from "./pages/ProfitPlannerPage";
import { ProfilePage } from "./pages/ProfilePage";

// Admin Pages
import { AdminSignalsPage } from "./pages/admin/AdminSignalsPage";
import { AdminMembersPage } from "./pages/admin/AdminMembersPage";
import { AdminAPICenterPage } from "./pages/admin/AdminAPICenterPage";
import { AdminSettingsPage } from "./pages/admin/AdminSettingsPage";
import { AdminAnalyticsPage } from "./pages/admin/AdminAnalyticsPage";

// Layout
import { DashboardLayout } from "./components/layout/DashboardLayout";

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Protected routes */}
          <Route element={<DashboardLayout />}>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/profit-tracker" element={<ProfitTrackerPage />} />
            <Route path="/trade-monitor" element={<TradeMonitorPage />} />
            <Route path="/goals" element={<ProfitPlannerPage />} />
            <Route path="/debt" element={<DebtManagementPage />} />
            <Route path="/profile" element={<ProfilePage />} />
            
            {/* Admin routes */}
            <Route path="/admin/signals" element={<AdminSignalsPage />} />
            <Route path="/admin/members" element={<AdminMembersPage />} />
            <Route path="/admin/analytics" element={<AdminAnalyticsPage />} />
            <Route path="/admin/api-center" element={<AdminAPICenterPage />} />
            <Route path="/admin/settings" element={<AdminSettingsPage />} />
          </Route>

          {/* Default redirect */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" richColors theme="dark" />
    </AuthProvider>
  );
}

export default App;
