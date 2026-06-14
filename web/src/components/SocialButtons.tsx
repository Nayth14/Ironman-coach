import type { Provider } from "@supabase/supabase-js";

interface SocialButtonsProps {
  onOAuth: (provider: Provider) => void;
  loading?: boolean;
}

export function SocialButtons({ onOAuth, loading }: SocialButtonsProps) {
  return (
    <div className="space-y-3">
      <div className="relative my-6">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-border" />
        </div>
        <div className="relative flex justify-center text-xs uppercase">
          <span className="bg-white px-3 text-text-muted">Or</span>
        </div>
      </div>

      <button
        type="button"
        disabled={loading}
        onClick={() => onOAuth("facebook")}
        className="w-full flex items-center justify-center gap-3 rounded-xl bg-[#1877F2] text-white py-3 text-sm font-semibold disabled:opacity-50"
      >
        <span className="font-bold">f</span>
        Continue with Facebook
      </button>

      <button
        type="button"
        disabled={loading}
        onClick={() => onOAuth("google")}
        className="w-full flex items-center justify-center gap-3 rounded-xl border border-border bg-white py-3 text-sm font-semibold hover:bg-gray-50 disabled:opacity-50"
      >
        <span>G</span>
        Continue with Google
      </button>
    </div>
  );
}
