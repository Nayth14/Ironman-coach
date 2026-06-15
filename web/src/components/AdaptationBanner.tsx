import type { AdaptationEvent } from "../lib/types";

const DECISION_COLORS: Record<string, string> = {
  progress: "bg-green-50 border-green-200 text-green-800",
  hold: "bg-amber-50 border-amber-200 text-amber-800",
  deload: "bg-red-50 border-red-200 text-red-800",
  bike_substitute: "bg-blue-50 border-blue-200 text-blue-800",
  gut_training: "bg-orange-50 border-orange-200 text-orange-800",
};

interface Props {
  adaptation: AdaptationEvent;
  onAccept: () => void;
  onDismiss: () => void;
}

export function AdaptationBanner({ adaptation, onAccept, onDismiss }: Props) {
  const cls = DECISION_COLORS[adaptation.decision] || "bg-gray-50 border-gray-200";
  return (
    <div className={`rounded-2xl border p-5 mb-6 ${cls}`}>
      <h3 className="font-semibold mb-1">
        Your coach adjusted this week — {adaptation.decision.replace(/_/g, " ")}
      </h3>
      <p className="text-sm mb-3">{adaptation.rationale}</p>
      {adaptation.changes.length > 0 && (
        <ul className="text-sm mb-4 space-y-1">
          {adaptation.changes.map((c, i) => (
            <li key={i}>• {c}</li>
          ))}
        </ul>
      )}
      {adaptation.diff && (
        <div className="text-sm mb-4 rounded-xl bg-white/60 p-3 border border-black/5">
          <p className="font-medium mb-1">Preview changes</p>
          <p>
            Weekly hours: {adaptation.diff.before_hours.toFixed(1)}h →{" "}
            {adaptation.diff.after_hours.toFixed(1)}h
          </p>
          {adaptation.diff.changed_workouts.length > 0 && (
            <ul className="mt-2 space-y-1">
              {adaptation.diff.changed_workouts.map((w) => (
                <li key={w.workout_id}>
                  • {w.title}: {w.change_summary}
                </li>
              ))}
            </ul>
          )}
          {adaptation.diff.substitutions.length > 0 && (
            <ul className="mt-2 space-y-1">
              {adaptation.diff.substitutions.map((s, i) => (
                <li key={i}>↔ {s}</li>
              ))}
            </ul>
          )}
        </div>
      )}
      {adaptation.playbookVersion && (
        <p className="text-xs opacity-60 mb-3">Ruleset v{adaptation.playbookVersion}</p>
      )}
      <div className="flex gap-2">
        <button
          onClick={onAccept}
          className="rounded-full bg-text text-white px-4 py-1.5 text-sm font-medium"
        >
          Accept changes
        </button>
        <button
          onClick={onDismiss}
          className="rounded-full border border-border px-4 py-1.5 text-sm font-medium"
        >
          Dismiss
        </button>
      </div>
    </div>
  );
}
