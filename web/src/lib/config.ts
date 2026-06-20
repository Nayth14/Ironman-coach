export const BRAND_NAME = import.meta.env.VITE_BRAND_NAME || "Ironman Coach";
export const API_URL = import.meta.env.VITE_API_URL || "";

/** Resolve an API path, using VITE_API_URL when set (bypasses Netlify's ~26s proxy limit). */
export function apiPath(path: string): string {
  const base = API_URL.replace(/\/$/, "");
  return base ? `${base}${path}` : path;
}

export const COLORS = {
  bg: "#FAFAF8",
  primary: "#FF5436",
  swim: "#3B82F6",
  bike: "#22C55E",
  run: "#FF5436",
  strength: "#A855F7",
} as const;

export const SPORT_COLORS: Record<string, string> = {
  swim: COLORS.swim,
  bike: COLORS.bike,
  run: COLORS.run,
  strength: COLORS.strength,
  brick: COLORS.bike,
  other: "#6B7280",
};

export const SPORT_LABELS: Record<string, string> = {
  swim: "Swim",
  bike: "Bike",
  run: "Run",
  strength: "Strength",
  brick: "Brick",
  other: "Other",
};

export const DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

export function formatDuration(seconds: number | null | undefined): string {
  if (!seconds) return "—";
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

export function formatDistance(meters: number | null | undefined): string {
  if (!meters) return "—";
  if (meters >= 1000) return `${(meters / 1000).toFixed(1)} km`;
  return `${meters} m`;
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "";
  const d = new Date(iso + "T12:00:00");
  return d.toLocaleDateString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
  });
}
