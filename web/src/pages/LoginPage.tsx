import type { Provider } from "@supabase/supabase-js";
import { FormEvent, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { AuthFooterLink, AuthLayout } from "../components/AuthLayout";
import { FormAlert } from "../components/FormAlert";
import { SocialButtons } from "../components/SocialButtons";
import { TextInput } from "../components/TextInput";
import { useAuth } from "../lib/auth";

export function LoginPage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const next = params.get("next") || "/dashboard";
  const { signInWithPassword, signInWithOAuth } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    const { error: authError } = await signInWithPassword(email, password);
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
    <AuthLayout title="Welcome back" subtitle="Log in to access your training plan.">
      <form onSubmit={onSubmit} className="space-y-4">
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
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label className="text-sm font-medium">Password</label>
            <Link to="/forgot-password" className="text-sm text-primary font-medium">
              Forgot password?
            </Link>
          </div>
          <TextInput
            label="Password"
            className="[&>label]:hidden"
            showToggle
            autoComplete="current-password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            icon={<span>🔒</span>}
            required
          />
        </div>

        <FormAlert message={error} />

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-full bg-primary text-white py-3 text-sm font-semibold disabled:opacity-50"
        >
          Log in
        </button>
      </form>

      <SocialButtons onOAuth={onOAuth} loading={loading} />

      <AuthFooterLink text="Don't have an account?" linkText="Sign up" to="/signup" />
    </AuthLayout>
  );
}
