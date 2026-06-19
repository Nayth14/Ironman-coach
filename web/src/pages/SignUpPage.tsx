import type { Provider } from "@supabase/supabase-js";
import { FormEvent, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { AuthFooterLink, AuthLayout } from "../components/AuthLayout";
import { SocialButtons } from "../components/SocialButtons";
import { TextInput } from "../components/TextInput";
import { useAuth } from "../lib/auth";

export function SignUpPage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const next = params.get("next") || "/dashboard";
  const { signUp, signInWithOAuth } = useAuth();
  const [firstName, setFirstName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setInfo(null);

    const { error: authError } = await signUp(email, password, {
      firstName: firstName || undefined,
    });
    if (authError) {
      setError(authError);
      setLoading(false);
      return;
    }

    navigate(next, { replace: true });
    setLoading(false);
  };

  const onOAuth = async (provider: Provider) => {
    setError(null);
    const { error: authError } = await signInWithOAuth(provider);
    if (authError) setError(authError);
  };

  return (
    <AuthLayout title="Create your account" subtitle="Start training with your personalized plan.">
      <form onSubmit={onSubmit} className="space-y-4">
        <TextInput
          label="First name (optional)"
          autoComplete="given-name"
          placeholder="Alex"
          value={firstName}
          onChange={(e) => setFirstName(e.target.value)}
        />
        <TextInput
          label="Email address"
          type="email"
          autoComplete="email"
          placeholder="you@example.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          icon={<span>✉</span>}
          required
        />
        <TextInput
          label="Password"
          showToggle
          autoComplete="new-password"
          placeholder="••••••••"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          icon={<span>🔒</span>}
          required
        />

        {error && (
          <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-xl px-4 py-3">
            {error}
          </div>
        )}
        {info && !error && (
          <div className="text-sm text-green-700 bg-green-50 border border-green-200 rounded-xl px-4 py-3">
            {info}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-full bg-primary text-white py-3 text-sm font-semibold disabled:opacity-50"
        >
          Create account
        </button>
      </form>

      <SocialButtons onOAuth={onOAuth} loading={loading} />

      <p className="text-xs text-text-muted text-center mt-4">
        By creating an account you agree to our Terms of Service and Privacy Policy.
      </p>

      <AuthFooterLink text="Already have an account?" linkText="Log in" to="/login" />
    </AuthLayout>
  );
}
