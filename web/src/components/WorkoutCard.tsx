import type { Workout } from "../lib/types";
import { formatDuration, formatDistance, formatDate } from "../lib/config";
import { SportIcon } from "./SportIcon";

interface Props {
  workout: Workout;
  onComplete?: () => void;
}

export function WorkoutCard({ workout, onComplete }: Props) {
  const steps = workout.steps || [];
  return (
    <div className="bg-card rounded-2xl border border-border p-6 shadow-sm">
      <div className="flex items-start gap-3 mb-4">
        <SportIcon sport={workout.sport} />
        <div className="flex-1">
          <h3 className="font-semibold text-lg">{workout.title}</h3>
          {workout.scheduled_date && (
            <div className="text-xs text-text-muted">{formatDate(workout.scheduled_date)}</div>
          )}
          {workout.is_key_session && (
            <span className="text-xs text-primary font-medium">★ Key session</span>
          )}
        </div>
      </div>

      {steps.length > 0 && (
        <div className="space-y-2 mb-4">
          {steps.map((s) => (
            <div key={s.id} className="flex items-center gap-3 text-sm">
              <span className="w-2 h-2 rounded-full bg-bike shrink-0" />
              <span className="flex-1">{s.name || s.type}</span>
              {s.duration_seconds && (
                <span className="text-text-muted">{formatDuration(s.duration_seconds)}</span>
              )}
              {s.target?.label && (
                <span className="text-xs bg-gray-100 px-2 py-0.5 rounded">{s.target.label}</span>
              )}
            </div>
          ))}
        </div>
      )}

      {workout.exercises?.length > 0 && (
        <div className="space-y-1 mb-4 text-sm">
          {workout.exercises.map((e, i) => (
            <div key={i}>
              {e.name} — {e.sets}×{e.reps}
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-3 gap-4 pt-4 border-t border-border">
        <div>
          <div className="text-xs text-text-muted">Duration</div>
          <div className="font-semibold">{formatDuration(workout.estimated_duration_seconds)}</div>
        </div>
        <div>
          <div className="text-xs text-text-muted">Distance</div>
          <div className="font-semibold">{formatDistance(workout.estimated_distance_meters)}</div>
        </div>
        <div>
          <div className="text-xs text-text-muted">TSS</div>
          <div className="font-semibold">{workout.estimated_tss ?? "—"}</div>
        </div>
      </div>

      {workout.status === "planned" && onComplete && (
        <button
          onClick={onComplete}
          className="mt-4 w-full rounded-full bg-primary text-white py-2 text-sm font-semibold hover:bg-primary-hover"
        >
          Mark complete
        </button>
      )}
    </div>
  );
}
