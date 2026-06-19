import { NavLink, Outlet } from "react-router-dom";
import { Logo } from "../components/Logo";
import { useAuth } from "../lib/auth";

const NAV = [
  { to: "/dashboard", label: "Overview", icon: "📊" },
  { to: "/dashboard/plan", label: "My Plan", icon: "📅" },
  { to: "/dashboard/workouts", label: "Workouts", icon: "💪" },
  { to: "/dashboard/progress", label: "Progress", icon: "📈" },
];

interface Props {
  raceName?: string;
  weeksToRace?: number;
}

export function DashboardLayout({ raceName, weeksToRace }: Props) {
  const { user, signOut } = useAuth();
  const displayName = user?.email?.split("@")[0] || "Athlete";

  return (
    <div className="flex min-h-screen">
      <aside className="w-56 bg-white border-r border-border flex flex-col shrink-0">
        <div className="p-5">
          <Logo to="/dashboard" />
        </div>
        <nav className="flex-1 px-3 space-y-1">
          {NAV.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              end={n.to === "/dashboard"}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-primary/10 text-primary"
                    : "text-text-muted hover:bg-gray-50 hover:text-text"
                }`
              }
            >
              <span>{n.icon}</span>
              {n.label}
            </NavLink>
          ))}
        </nav>
        <div className="p-4 border-t border-border space-y-3">
          <div className="flex items-center gap-2 text-sm">
            <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
              👤
            </div>
            <div className="min-w-0">
              <div className="font-medium truncate">{displayName}</div>
              {raceName && (
                <div className="text-xs text-text-muted truncate">
                  {raceName}
                  {weeksToRace != null ? ` · ${weeksToRace}w to race` : ""}
                </div>
              )}
            </div>
          </div>
          <button
            type="button"
            onClick={() => signOut()}
            className="w-full text-left text-xs text-text-muted hover:text-text px-1"
          >
            Sign out
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-auto">
        <Outlet context={{ raceName, weeksToRace }} />
      </main>
    </div>
  );
}
