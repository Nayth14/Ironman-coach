import { BRAND_NAME } from "../lib/config";

export function Logo({ className = "" }: { className?: string }) {
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <svg width="28" height="28" viewBox="0 0 32 32" fill="none">
        <path d="M16 4L28 26H4L16 4Z" fill="#FF5436" />
      </svg>
      <span className="text-xl font-bold tracking-tight">{BRAND_NAME}</span>
    </div>
  );
}
