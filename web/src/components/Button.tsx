import { Link } from "react-router-dom";

type Variant = "primary" | "secondary" | "ghost" | "dark";

const styles: Record<Variant, string> = {
  primary:
    "bg-primary text-white hover:bg-primary-hover shadow-sm",
  secondary:
    "bg-white text-text border border-border hover:bg-gray-50",
  ghost: "bg-transparent text-text hover:bg-black/5",
  dark: "bg-text text-white hover:bg-black",
};

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  to?: string;
  children: React.ReactNode;
}

export function Button({
  variant = "primary",
  to,
  children,
  className = "",
  ...props
}: ButtonProps) {
  const cls = `inline-flex items-center justify-center rounded-full px-6 py-2.5 text-sm font-semibold transition-colors ${styles[variant]} ${className}`;
  if (to) {
    return (
      <Link to={to} className={cls}>
        {children}
      </Link>
    );
  }
  return (
    <button className={cls} {...props}>
      {children}
    </button>
  );
}
