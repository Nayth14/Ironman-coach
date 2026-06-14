import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Phase } from "../lib/types";
import { SPORT_COLORS } from "../lib/config";
import type { SportFilter } from "./DisciplineFilter";

interface Props {
  phases: Phase[];
  totalWeeks: number;
  sportFilter: SportFilter;
}

function buildChartData(phases: Phase[], totalWeeks: number, sport: SportFilter) {
  const sportFactor =
    sport === "swim" ? 0.15 : sport === "bike" ? 0.45 : sport === "run" ? 0.3 : sport === "strength" ? 0.1 : 1;
  const points: { week: number; tss: number; phase: string }[] = [];
  for (let w = 1; w <= totalWeeks; w++) {
    const phase = phases.find((p) => w >= p.start_week && w <= p.end_week);
    const phaseName = phase?.name || "base";
    let base = 400;
    if (phaseName === "prep") base = 250;
    if (phaseName === "base") base = 500;
    if (phaseName === "build") base = 750;
    if (phaseName === "peak") base = 900;
    if (phaseName === "taper") base = 350;
    const wave = Math.sin((w / totalWeeks) * Math.PI * 4) * 80;
    const deload = w % 4 === 0 ? 0.7 : 1;
    points.push({
      week: w,
      tss: Math.round((base + wave) * deload * sportFactor),
      phase: phaseName,
    });
  }
  return points;
}

function phaseLabels(phases: Phase[]) {
  return phases.map((p) => ({
    name: p.name.charAt(0).toUpperCase() + p.name.slice(1),
    start: p.start_week,
    end: p.end_week,
  }));
}

export function TrainingLoadChart({ phases, totalWeeks, sportFilter }: Props) {
  const data = buildChartData(phases, totalWeeks, sportFilter);
  const labels = phaseLabels(phases);
  const color =
    sportFilter === "all"
      ? SPORT_COLORS.bike
      : SPORT_COLORS[sportFilter] || SPORT_COLORS.bike;

  return (
    <div className="bg-card rounded-2xl border border-border p-6 shadow-sm">
      <h3 className="font-semibold mb-4">
        Your race plan{sportFilter !== "all" ? ` — ${sportFilter.charAt(0).toUpperCase() + sportFilter.slice(1)}` : ""}
      </h3>
      <div className="h-56">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="tssGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={color} stopOpacity={0.35} />
                <stop offset="100%" stopColor={color} stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="week" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip />
            <Area
              type="monotone"
              dataKey="tss"
              stroke={color}
              fill="url(#tssGrad)"
              strokeWidth={2}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      <div className="flex flex-wrap gap-2 mt-3 text-xs text-text-muted">
        {labels.map((l) => (
          <span key={l.name} className="px-2 py-1 bg-gray-50 rounded-full">
            {l.name} (wk {l.start}–{l.end})
          </span>
        ))}
        <span className="px-2 py-1 bg-primary/10 text-primary rounded-full font-medium">
          Race Day
        </span>
      </div>
    </div>
  );
}
