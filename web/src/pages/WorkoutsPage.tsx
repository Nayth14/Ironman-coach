import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { DisciplineFilter, type SportFilter } from "../components/DisciplineFilter";
import { SportIcon } from "../components/SportIcon";
import { api } from "../lib/api";
import { formatDuration } from "../lib/config";
import type { Workout } from "../lib/types";

export function WorkoutsPage() {
  const [sportFilter, setSportFilter] = useState<SportFilter>("all");
  const [completing, setCompleting] = useState<string | null>(null);
  const [rpe, setRpe] = useState(5);
  const [error, setError] = useState<string | null>(null);
  const qc = useQueryClient();

  const sport = sportFilter === "all" ? undefined : sportFilter;
  const { data, isLoading } = useQuery({
    queryKey: ["workouts", sport],
    queryFn: () => api.listWorkouts(sport),
  });

  const workouts = data?.workouts || [];
  const planned = workouts.filter((w) => w.status === "planned");
  const completed = workouts.filter((w) => w.status === "completed");

  const submitComplete = async (w: Workout) => {
    try {
      setError(null);
      await api.completeWorkout(w.id, {
        completed: true,
        rpe,
        readiness_score: 7,
      });
      setCompleting(null);
      qc.invalidateQueries({ queryKey: ["workouts"] });
      qc.invalidateQueries({ queryKey: ["currentPlan"] });
    } catch (e) {
      setError(`Failed to complete workout: ${(e as Error).message}`);
    }
  };

  if (isLoading) return <div className="p-8 text-text-muted">Loading…</div>;

  return (
    <div className="p-8">
      {error && (
        <div className="mb-4 rounded-xl bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}
      <header className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <h1 className="text-2xl font-bold">Workouts</h1>
        <DisciplineFilter value={sportFilter} onChange={setSportFilter} />
      </header>

      {planned.length > 0 && (
        <section className="mb-8">
          <h2 className="font-semibold mb-3">Upcoming</h2>
          <div className="space-y-2">
            {planned.map((w) => (
              <div
                key={w.id}
                className="bg-white rounded-xl border border-border p-4 flex items-center gap-3"
              >
                <SportIcon sport={w.sport} size="sm" />
                <div className="flex-1">
                  <div className="font-medium text-sm">{w.title}</div>
                  <div className="text-xs text-text-muted">
                    Week {w.week_number} · {formatDuration(w.estimated_duration_seconds)}
                  </div>
                </div>
                {completing === w.id ? (
                  <div className="flex items-center gap-2">
                    <label className="text-xs">
                      RPE
                      <input
                        type="range"
                        min={1}
                        max={10}
                        value={rpe}
                        onChange={(e) => setRpe(+e.target.value)}
                        className="ml-2"
                      />
                      {rpe}
                    </label>
                    <button
                      onClick={() => submitComplete(w)}
                      className="text-sm bg-primary text-white px-3 py-1 rounded-full"
                    >
                      Save
                    </button>
                    <button
                      onClick={() => setCompleting(null)}
                      className="text-sm text-text-muted"
                    >
                      Cancel
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => setCompleting(w.id)}
                    className="text-sm text-primary font-medium"
                  >
                    Complete
                  </button>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      <section>
        <h2 className="font-semibold mb-3">History</h2>
        {completed.length === 0 ? (
          <p className="text-text-muted text-sm">No completed workouts yet</p>
        ) : (
          <div className="space-y-2">
            {completed.map((w) => (
              <div
                key={w.id}
                className="bg-white rounded-xl border border-border p-4 flex items-center gap-3"
              >
                <SportIcon sport={w.sport} size="sm" />
                <div className="flex-1">
                  <div className="font-medium text-sm">{w.title}</div>
                  <div className="text-xs text-text-muted">
                    Week {w.week_number} · {formatDuration(w.estimated_duration_seconds)}
                  </div>
                </div>
                <span className="text-green-500 text-sm">Completed ✓</span>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
