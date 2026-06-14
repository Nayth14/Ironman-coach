import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { DisciplineFilter, type SportFilter } from "../components/DisciplineFilter";
import { SportIcon } from "../components/SportIcon";
import { api } from "../lib/api";
import { DAY_NAMES, formatDuration } from "../lib/config";
import type { Workout } from "../lib/types";

export function MyPlanPage() {
  const [sportFilter, setSportFilter] = useState<SportFilter>("all");
  const [expanded, setExpanded] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["currentPlan"],
    queryFn: () => api.getCurrentPlan(),
  });

  const byWeek = useMemo(() => {
    const workouts = data?.workouts || [];
    const filtered =
      sportFilter === "all"
        ? workouts
        : workouts.filter((w) => w.sport === sportFilter);
    const map = new Map<number, Workout[]>();
    for (const w of filtered) {
      const wk = w.week_number || 1;
      if (!map.has(wk)) map.set(wk, []);
      map.get(wk)!.push(w);
    }
    return [...map.entries()].sort((a, b) => a[0] - b[0]);
  }, [data, sportFilter]);

  if (isLoading) return <div className="p-8 text-text-muted">Loading…</div>;

  return (
    <div className="p-8">
      <header className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <h1 className="text-2xl font-bold">My Plan</h1>
        <DisciplineFilter value={sportFilter} onChange={setSportFilter} />
      </header>

      <div className="space-y-6">
        {byWeek.map(([week, items]) => (
          <div key={week} className="bg-white rounded-2xl border border-border p-5">
            <h3 className="font-semibold mb-3">Week {week}</h3>
            <div className="space-y-2">
              {items.map((w) => (
                <div key={w.id}>
                  <button
                    onClick={() =>
                      setExpanded(expanded === w.id ? null : w.id)
                    }
                    className="w-full flex items-center gap-3 text-left bg-gray-50 rounded-xl px-4 py-3 hover:bg-gray-100"
                  >
                    <SportIcon sport={w.sport} size="sm" />
                    <div className="flex-1">
                      <div className="font-medium text-sm">{w.title}</div>
                      <div className="text-xs text-text-muted">
                        {w.day_of_week != null ? DAY_NAMES[w.day_of_week] : ""} ·{" "}
                        {formatDuration(w.estimated_duration_seconds)} · {w.purpose_tag}
                        {w.is_key_session && " · ★ key"}
                      </div>
                    </div>
                    <span className="text-text-muted">{expanded === w.id ? "▲" : "▼"}</span>
                  </button>
                  {expanded === w.id && (
                    <div className="px-4 py-3 text-sm space-y-2 border-t border-border mt-1">
                      {w.steps?.map((s) => (
                        <div key={s.id}>
                          {s.name || s.type}
                          {s.duration_seconds
                            ? ` — ${formatDuration(s.duration_seconds)}`
                            : ""}
                        </div>
                      ))}
                      {w.fueling_notes && (
                        <p className="text-text-muted">Fueling: {w.fueling_notes}</p>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
