import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { activatePendingPlanIfNeeded, linkGuestIfNeeded } from "../lib/authLink";
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
      const link = await linkGuestIfNeeded();
      if (cancelled) return;

      if (link.ok === false && link.reason === "conflict") {
        setBootstrapError(
          link.message ||
            "This account is already linked to a different profile. Please sign in with the correct account."
        );
        setBootstrapping(false);
        return;
      }

      try {
        await activatePendingPlanIfNeeded();
      } catch (e) {
        if (!cancelled) {
          setBootstrapError((e as Error).message);
        }
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
