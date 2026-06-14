import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";

export function ProgressPage() {
  const { data } = useQuery({
    queryKey: ["currentPlan"],
    queryFn: () => api.getCurrentPlan(),
  });

  const workouts = data?.workouts || [];
  const completed = workouts.filter((w) => w.status === "completed");
  const keySessions = workouts.filter((w) => w.is_key_session);
  const keyCompleted = keySessions.filter((w) => w.status === "completed");
  const consistency =
    keySessions.length > 0
      ? Math.round((keyCompleted.length / keySessions.length) * 100)
      : 0;

  const bySport: Record<string, number> = {};
  for (const w of completed) {
    bySport[w.sport] = (bySport[w.sport] || 0) + (w.estimated_duration_seconds || 0);
  }

  const phase =
    (data?.plan?.phases as { name: string }[])?.[0]?.name || "—";

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-6">Progress</h1>

      <div className="grid md:grid-cols-3 gap-6">
        <div className="bg-white rounded-2xl border border-border p-6">
          <div className="text-sm text-text-muted mb-1">Consistency score</div>
          <div className="text-4xl font-bold">{consistency}%</div>
          <div className="text-xs text-text-muted mt-1">Key sessions completed</div>
        </div>

        <div className="bg-white rounded-2xl border border-border p-6">
          <div className="text-sm text-text-muted mb-1">Current phase</div>
          <div className="text-2xl font-bold capitalize">{phase}</div>
        </div>

        <div className="bg-white rounded-2xl border border-border p-6">
          <div className="text-sm text-text-muted mb-1">Sessions logged</div>
          <div className="text-4xl font-bold">{completed.length}</div>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-border p-6 mt-6">
        <h3 className="font-semibold mb-4">Volume by discipline (completed)</h3>
        <div className="space-y-3">
          {Object.entries(bySport).map(([sport, secs]) => (
            <div key={sport} className="flex items-center gap-3">
              <span className="w-16 capitalize text-sm">{sport}</span>
              <div className="flex-1 bg-gray-100 rounded-full h-3">
                <div
                  className="bg-primary h-3 rounded-full"
                  style={{
                    width: `${Math.min(100, (secs / 36000) * 100)}%`,
                  }}
                />
              </div>
              <span className="text-sm text-text-muted w-16 text-right">
                {Math.round(secs / 3600)}h
              </span>
            </div>
          ))}
          {Object.keys(bySport).length === 0 && (
            <p className="text-text-muted text-sm">Complete workouts to see trends</p>
          )}
        </div>
      </div>
    </div>
  );
}
