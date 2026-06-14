import { useCallback, useEffect, useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { DisciplineFilter, type SportFilter } from "../components/DisciplineFilter";
import { TrainingLoadChart } from "../components/TrainingLoadChart";
import { WorkoutCard } from "../components/WorkoutCard";
import { SportIcon } from "../components/SportIcon";
import { CoachChatFab, CoachChatPanel } from "../components/CoachChat";
import { AdaptationBanner } from "../components/AdaptationBanner";
import { api } from "../lib/api";
import { ensureGuestId } from "../lib/guest";
import { formatDuration } from "../lib/config";
import type { Workout, Phase, AdaptationEvent } from "../lib/types";

export function OverviewPage() {
  const [sportFilter, setSportFilter] = useState<SportFilter>("all");
  const [chatOpen, setChatOpen] = useState(false);
  const [adaptation, setAdaptation] = useState<AdaptationEvent | null>(null);
  const qc = useQueryClient();

  useEffect(() => {
    ensureGuestId();
    api.getPendingAdaptation().then((r) => {
      if (r.adaptation) setAdaptation(r.adaptation);
    });
  }, []);

  const { data, isLoading, error } = useQuery({
    queryKey: ["currentPlan"],
    queryFn: () => api.getCurrentPlan(),
  });

  const workouts = data?.workouts || [];
  const phases = (data?.plan?.phases as Phase[]) || [];
  const totalWeeks = (data?.plan?.total_weeks as number) || 24;
  const profile = data?.profile;
  const readiness = data?.readiness;

  const filtered = useMemo(() => {
    if (sportFilter === "all") return workouts;
    return workouts.filter((w) => w.sport === sportFilter);
  }, [workouts, sportFilter]);

  const currentWorkout = useMemo(() => {
    const planned = filtered.filter((w) => w.status === "planned");
    const today = new Date().toISOString().slice(0, 10);
    const withDates = planned.filter((w) => w.scheduled_date);
    if (withDates.length > 0) {
      const upcoming = withDates
        .filter((w) => w.scheduled_date! >= today)
        .sort((a, b) => a.scheduled_date!.localeCompare(b.scheduled_date!));
      if (upcoming.length > 0) return upcoming[0];
      return withDates.sort((a, b) =>
        b.scheduled_date!.localeCompare(a.scheduled_date!)
      )[0];
    }
    return planned[0] || filtered[0];
  }, [filtered]);

  const recentCompleted = useMemo(
    () =>
      filtered
        .filter((w) => w.status === "completed")
        .slice(0, 5),
    [filtered]
  );

  const handleComplete = useCallback(
    async (w: Workout) => {
      await api.completeWorkout(w.id, { completed: true, rpe: 5 });
      qc.invalidateQueries({ queryKey: ["currentPlan"] });
      qc.invalidateQueries({ queryKey: ["workouts"] });
      try {
        const ev = await api.evaluateAdaptation();
        setAdaptation(ev);
      } catch {
        /* need more completions */
      }
    },
    [qc]
  );

  const handleAdaptAccept = async () => {
    const id = adaptation?.eventId || adaptation?.id;
    if (id) await api.acceptAdaptation(id, true);
    setAdaptation(null);
  };

  const handleAdaptDismiss = async () => {
    const id = adaptation?.eventId || adaptation?.id;
    if (id) await api.acceptAdaptation(id, false);
    setAdaptation(null);
  };

  if (isLoading) {
    return <div className="p-8 text-text-muted">Loading your plan…</div>;
  }

  if (error || !data?.plan) {
    return (
      <div className="p-8">
        <p className="text-text-muted mb-4">No active plan yet.</p>
        <a href="/onboarding" className="text-primary font-semibold">
          Build your plan →
        </a>
      </div>
    );
  }

  return (
    <div className="p-8">
      <header className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold">Training Overview</h1>
          {profile && (
            <span className="inline-block mt-2 rounded-full bg-gray-100 px-3 py-1 text-sm font-medium">
              {profile.race_name} · {readiness?.weeks_to_race ?? "—"} weeks to go
            </span>
          )}
        </div>
        <DisciplineFilter value={sportFilter} onChange={setSportFilter} />
      </header>

      {adaptation && (
        <AdaptationBanner
          adaptation={adaptation}
          onAccept={handleAdaptAccept}
          onDismiss={handleAdaptDismiss}
        />
      )}

      <div className="space-y-6">
        <TrainingLoadChart
          phases={phases}
          totalWeeks={totalWeeks}
          sportFilter={sportFilter}
        />

        {currentWorkout ? (
          <WorkoutCard
            workout={currentWorkout}
            onComplete={() => handleComplete(currentWorkout)}
          />
        ) : (
          <div className="bg-white rounded-2xl border border-border p-8 text-center text-text-muted">
            No workouts for this filter
          </div>
        )}

        <div className="bg-white rounded-2xl border border-border p-6 shadow-sm">
          <h3 className="font-semibold mb-4">
            Recent {sportFilter !== "all" ? sportFilter : ""} workouts
          </h3>
          {recentCompleted.length === 0 ? (
            <p className="text-text-muted text-sm">No completed workouts yet</p>
          ) : (
            <div className="space-y-2">
              {recentCompleted.map((w) => (
                <div
                  key={w.id}
                  className="flex items-center gap-3 text-sm py-2 border-b border-border last:border-0"
                >
                  <SportIcon sport={w.sport} size="sm" />
                  <span className="flex-1">{w.title}</span>
                  <span className="text-text-muted">
                    {formatDuration(w.estimated_duration_seconds)}
                  </span>
                  <span className="text-green-500">✓</span>
                </div>
              ))}
            </div>
          )}
          <a
            href="/dashboard/workouts"
            className="inline-block mt-4 text-sm text-primary font-medium"
          >
            View all workouts →
          </a>
        </div>
      </div>

      <CoachChatFab onClick={() => setChatOpen(true)} />
      <CoachChatPanel open={chatOpen} onClose={() => setChatOpen(false)} />
    </div>
  );
}
