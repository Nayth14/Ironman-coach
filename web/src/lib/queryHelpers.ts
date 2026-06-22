import type { QueryClient } from "@tanstack/react-query";

export function invalidateTrainingQueries(qc: QueryClient): void {
  qc.invalidateQueries({ queryKey: ["currentPlan"] });
  qc.invalidateQueries({ queryKey: ["workouts"] });
}
