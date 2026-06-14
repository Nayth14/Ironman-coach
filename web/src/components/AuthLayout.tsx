import { Link } from "react-router-dom";
import { Logo } from "./Logo";

interface AuthLayoutProps {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}

export function AuthLayout({ title, subtitle, children }: AuthLayoutProps) {
  return (
    <div className="min-h-screen grid lg:grid-cols-2">
      <div
        className="hidden lg:flex relative flex-col justify-between p-10 text-white bg-cover bg-center"
        style={{
          backgroundImage:
            "linear-gradient(rgba(0,0,0,0.45), rgba(0,0,0,0.55)), url('/auth-hero.svg')",
        }}
      >
        <div className="[&_span]:text-white [&_svg]:text-white">
          <Logo />
        </div>
        <div>
          <h2 className="text-4xl font-bold leading-tight mb-3">Cross your finish line.</h2>
          <p className="text-white/80 text-lg">Train smarter. Arrive ready.</p>
        </div>
      </div>

      <div className="flex flex-col min-h-screen bg-white">
        <header className="flex items-center justify-between px-6 py-5 lg:px-12">
          <div className="lg:hidden">
            <Logo />
          </div>
          <div className="ml-auto flex items-center gap-3 text-sm">
            <span className="text-text-muted hidden sm:inline">Questions?</span>
            <a
              href="mailto:support@ironmancoach.app"
              className="rounded-full border border-text px-4 py-1.5 font-semibold hover:bg-gray-50"
            >
              Contact
            </a>
          </div>
        </header>

        <main className="flex-1 flex items-center justify-center px-6 pb-12 lg:px-12">
          <div className="w-full max-w-md">
            <h1 className="text-3xl font-bold mb-2">{title}</h1>
            {subtitle && <p className="text-text-muted mb-8">{subtitle}</p>}
            {!subtitle && <div className="mb-8" />}
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}

interface AuthFooterLinkProps {
  text: string;
  linkText: string;
  to: string;
}

export function AuthFooterLink({ text, linkText, to }: AuthFooterLinkProps) {
  return (
    <p className="text-center text-sm text-text-muted mt-8">
      {text}{" "}
      <Link to={to} className="text-primary font-semibold hover:underline">
        {linkText}
      </Link>
    </p>
  );
}
