import { SPORT_COLORS } from "../lib/config";
import type { Sport } from "../lib/types";

const ICONS: Record<string, string> = {
  swim: "🏊",
  bike: "🚴",
  run: "🏃",
  strength: "🏋️",
  brick: "🔁",
  other: "•",
};

export function SportIcon({ sport, size = "md" }: { sport: Sport | string; size?: "sm" | "md" }) {
  const color = SPORT_COLORS[sport] || "#6B7280";
  const sz = size === "sm" ? "w-8 h-8 text-sm" : "w-10 h-10 text-base";
  return (
    <span
      className={`inline-flex items-center justify-center rounded-lg ${sz}`}
      style={{ backgroundColor: `${color}18`, color }}
    >
      {ICONS[sport] || "•"}
    </span>
  );
}
