import { useState } from "react";

interface TextInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  icon?: React.ReactNode;
  showToggle?: boolean;
}

export function TextInput({
  label,
  icon,
  showToggle,
  type = "text",
  className = "",
  ...props
}: TextInputProps) {
  const [visible, setVisible] = useState(false);
  const inputType = showToggle ? (visible ? "text" : "password") : type;

  return (
    <div className={className}>
      {label ? <label className="block text-sm font-medium mb-1.5">{label}</label> : null}
      <div className="relative">
        {icon && (
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted">
            {icon}
          </span>
        )}
        <input
          type={inputType}
          className={`w-full rounded-xl border border-border px-4 py-3 text-sm outline-none focus:border-primary ${
            icon ? "pl-10" : ""
          } ${showToggle ? "pr-10" : ""}`}
          {...props}
        />
        {showToggle && (
          <button
            type="button"
            onClick={() => setVisible((v) => !v)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text"
            aria-label={visible ? "Hide password" : "Show password"}
          >
            {visible ? "🙈" : "👁"}
          </button>
        )}
      </div>
    </div>
  );
}
