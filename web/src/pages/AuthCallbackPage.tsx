import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { supabase } from "../lib/supabase";

export function AuthCallbackPage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const { session, loading } = useAuth();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!supabase) return;

    supabase.auth.getSession().then(({ error: sessionError }) => {
      if (sessionError) setError(sessionError.message);
    });
  }, []);

  useEffect(() => {
    if (loading) return;
    if (!session) {
      const hash = window.location.hash;
      if (hash.includes("access_token") || hash.includes("error")) {
        return;
      }
      setError("Authentication failed. Please try again.");
      return;
    }

    const next = params.get("next") || "/dashboard";
    navigate(next, { replace: true });
  }, [loading, session, navigate, params]);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-bg p-6">
        <div className="max-w-md bg-white border border-border rounded-2xl p-6 text-center">
          <p className="text-red-600 text-sm mb-4">{error}</p>
          <a href="/login" className="text-primary font-semibold text-sm">
            Back to login
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-bg text-text-muted">
      Completing sign in…
    </div>
  );
}
