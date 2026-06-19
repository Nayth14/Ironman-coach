import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { runAuthBootstrap } from "../lib/authLink";
import { useEffect, useState } from "react";

export function RequireAuth() {
  const { session, loading, getAccessToken } = useAuth();
  const location = useLocation();
  const [bootstrapping, setBootstrapping] = useState(false);
  const [bootstrapError, setBootstrapError] = useState<string | null>(null);

  useEffect(() => {
    if (!session || !getAccessToken()) return;

    let cancelled = false;
    setBootstrapping(true);
    setBootstrapError(null);

    (async () => {
      const result = await runAuthBootstrap(getAccessToken());
      if (cancelled) return;

      if (result.ok === false) {
        setBootstrapError(
          result.message ||
            (result.reason === "conflict"
              ? "This account is already linked to a different profile. Please sign in with the correct account."
              : "Something went wrong while setting up your account.")
        );
      }

      if (!cancelled) setBootstrapping(false);
    })();

    return () => {
      cancelled = true;
    };
  }, [session, getAccessToken]);

  if (loading || bootstrapping) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-bg text-text-muted">
        Loading…
      </div>
    );
  }

  if (!session) {
    const next = encodeURIComponent(location.pathname + location.search);
    return <Navigate to={`/login?next=${next}`} replace />;
  }

  if (bootstrapError) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-bg p-6">
        <div className="max-w-md bg-white border border-border rounded-2xl p-6 text-center">
          <p className="text-red-600 text-sm mb-4">{bootstrapError}</p>
          <a href="/login" className="text-primary font-semibold text-sm">
            Back to login
          </a>
        </div>
      </div>
    );
  }

  return <Outlet />;
}
