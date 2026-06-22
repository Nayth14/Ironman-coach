import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { AuthLayout } from "../components/AuthLayout";
import { FormAlert } from "../components/FormAlert";
import { TextInput } from "../components/TextInput";
import { useAuth } from "../lib/auth";

export function ForgotPasswordPage() {
  const { resetPasswordForEmail } = useAuth();
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    const { error: authError } = await resetPasswordForEmail(email);
    setLoading(false);
    if (authError) {
      setError(authError);
      return;
    }
    setSent(true);
  };

  return (
    <AuthLayout
      title="Reset your password"
      subtitle="Enter your email and we'll send you a reset link."
    >
      {sent ? (
        <div className="bg-green-50 border border-green-200 rounded-2xl p-5 text-sm text-green-800">
          If an account exists for that email, we've sent a password reset link. Check your
          inbox.
        </div>
      ) : (
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

          <FormAlert message={error} />

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-full bg-primary text-white py-3 text-sm font-semibold disabled:opacity-50"
          >
            Send reset link
          </button>
        </form>
      )}

      <p className="text-center mt-6">
        <Link to="/login" className="text-sm text-primary font-semibold hover:underline">
          Back to log in
        </Link>
      </p>
    </AuthLayout>
  );
}
