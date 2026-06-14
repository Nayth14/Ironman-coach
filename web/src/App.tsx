import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect } from "react";
import { AuthProvider, useAuth } from "./lib/auth";
import { setAccessTokenGetter } from "./lib/api";
import { RequireAuth } from "./components/RequireAuth";
import { LandingPage } from "./pages/LandingPage";
import { OnboardingPage } from "./pages/OnboardingPage";
import { LoginPage } from "./pages/LoginPage";
import { SignUpPage } from "./pages/SignUpPage";
import { ForgotPasswordPage } from "./pages/ForgotPasswordPage";
import { ResetPasswordPage } from "./pages/ResetPasswordPage";
import { AuthCallbackPage } from "./pages/AuthCallbackPage";
import { DashboardLayout } from "./layouts/DashboardLayout";
import { OverviewPage } from "./pages/OverviewPage";
import { MyPlanPage } from "./pages/MyPlanPage";
import { WorkoutsPage } from "./pages/WorkoutsPage";
import { ProgressPage } from "./pages/ProgressPage";

const qc = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000, retry: 1 } },
});

function AuthTokenBridge() {
  const { getAccessToken } = useAuth();
  useEffect(() => {
    setAccessTokenGetter(getAccessToken);
  }, [getAccessToken]);
  return null;
}

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <AuthProvider>
        <AuthTokenBridge />
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/onboarding" element={<OnboardingPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/signup" element={<SignUpPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/reset-password" element={<ResetPasswordPage />} />
            <Route path="/auth/callback" element={<AuthCallbackPage />} />
            <Route element={<RequireAuth />}>
              <Route path="/dashboard" element={<DashboardLayout />}>
                <Route index element={<OverviewPage />} />
                <Route path="plan" element={<MyPlanPage />} />
                <Route path="workouts" element={<WorkoutsPage />} />
                <Route path="progress" element={<ProgressPage />} />
              </Route>
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}
