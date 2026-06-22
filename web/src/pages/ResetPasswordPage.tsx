import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AuthLayout } from "../components/AuthLayout";
import { FormAlert } from "../components/FormAlert";
import { TextInput } from "../components/TextInput";
import { useAuth } from "../lib/auth";

export function ResetPasswordPage() {
  const navigate = useNavigate();
  const { updatePassword, session } = useAuth();
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (password !== confirm) {
      setError("Passwords do not match");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }

    setLoading(true);
    setError(null);
    const { error: authError } = await updatePassword(password);
    setLoading(false);
    if (authError) {
      setError(authError);
      return;
    }
    setSuccess(true);
    setTimeout(() => {
      navigate(session ? "/dashboard" : "/login", { replace: true });
    }, 1500);
  };

  return (
    <AuthLayout title="Choose a new password" subtitle="Enter and confirm your new password.">
      {success ? (
        <div className="bg-green-50 border border-green-200 rounded-2xl p-5 text-sm text-green-800">
          Password updated. Redirecting…
        </div>
      ) : (
        <form onSubmit={onSubmit} className="space-y-4">
          <TextInput
            label="New password"
            showToggle
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <TextInput
            label="Confirm password"
            showToggle
            autoComplete="new-password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            required
          />

          <FormAlert message={error} />

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-full bg-primary text-white py-3 text-sm font-semibold disabled:opacity-50"
          >
            Update password
          </button>
        </form>
      )}
    </AuthLayout>
  );
}
