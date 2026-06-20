import { Link } from "react-router-dom";
import { BRAND_NAME } from "../lib/config";

interface LogoProps {
  className?: string;
  to?: string;
}

export function Logo({ className = "", to }: LogoProps) {
  const content = (
    <>
      <svg width="28" height="28" viewBox="0 0 32 32" fill="none">
        <path d="M16 4L28 26H4L16 4Z" fill="#FF5436" />
      </svg>
      <span className="text-xl font-bold tracking-tight">{BRAND_NAME}</span>
    </>
  );

  const classes = `flex items-center gap-2 ${className}`;

  if (to) {
    return (
      <Link to={to} className={`${classes} hover:opacity-80 transition-opacity`}>
        {content}
      </Link>
    );
  }

  return <div className={classes}>{content}</div>;
}
