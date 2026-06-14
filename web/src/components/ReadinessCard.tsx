import type { ReadinessVerdict } from "../lib/types";

const STYLES: Record<ReadinessVerdict, { bg: string; dot: string; label: string }> = {
  green: { bg: "bg-green-50 border-green-200", dot: "bg-green-500", label: "Ready to go" },
  amber: { bg: "bg-amber-50 border-amber-200", dot: "bg-amber-500", label: "Workable with adjustments" },
  red: { bg: "bg-red-50 border-red-200", dot: "bg-red-500", label: "Needs attention" },
};

interface Props {
  verdict: ReadinessVerdict;
  rationale: string;
  weeksToRace: number;
  adjustments?: string[];
}

export function ReadinessCard({ verdict, rationale, weeksToRace, adjustments = [] }: Props) {
  const s = STYLES[verdict];
  return (
    <div className={`rounded-2xl border p-5 ${s.bg}`}>
      <div className="flex items-center gap-2 mb-2">
        <span className={`w-3 h-3 rounded-full ${s.dot}`} />
        <span className="font-semibold capitalize">{verdict}</span>
        <span className="text-text-muted text-sm">· {weeksToRace} weeks to race</span>
      </div>
      <p className="text-sm text-text-muted mb-2">{s.label}</p>
      <p className="text-sm">{rationale}</p>
      {adjustments.length > 0 && (
        <ul className="mt-3 text-sm space-y-1">
          {adjustments.map((a, i) => (
            <li key={i} className="text-text-muted">• {a}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
