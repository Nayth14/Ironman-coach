import { SPORT_COLORS, SPORT_LABELS } from "../lib/config";

const ALL_SPORTS = ["all", "swim", "bike", "run", "strength"] as const;
export type SportFilter = (typeof ALL_SPORTS)[number];

interface Props {
  value: SportFilter;
  onChange: (v: SportFilter) => void;
}

export function DisciplineFilter({ value, onChange }: Props) {
  return (
    <div className="inline-flex rounded-full bg-white border border-border p-1 gap-0.5">
      {ALL_SPORTS.map((s) => {
        const active = value === s;
        const color = s !== "all" ? SPORT_COLORS[s] : undefined;
        return (
          <button
            key={s}
            onClick={() => onChange(s)}
            className={`rounded-full px-4 py-1.5 text-sm font-medium transition-all ${
              active
                ? "bg-text text-white shadow-sm"
                : "text-text-muted hover:text-text"
            }`}
            style={active && color ? { backgroundColor: color } : undefined}
          >
            {s === "all" ? "All" : SPORT_LABELS[s]}
          </button>
        );
      })}
    </div>
  );
}
