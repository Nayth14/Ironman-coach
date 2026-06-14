import { getGuestId } from "./guest";

async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const guestId = getGuestId();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (guestId) headers["X-Guest-Id"] = guestId;

  const res = await fetch(path, { ...options, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }
  return res.json();
}

export interface SSEHandlers {
  onToken?: (data: { content: string; full: string }) => void;
  onDone?: (data: { content: string; ready?: boolean }) => void;
  onError?: (data: { message: string }) => void;
}

export async function streamSSE(
  path: string,
  body: unknown,
  handlers: SSEHandlers
): Promise<void> {
  const guestId = getGuestId();
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (guestId) headers["X-Guest-Id"] = guestId;

  const res = await fetch(path, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });
  if (!res.ok || !res.body) throw new Error("Stream failed");

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() || "";
    for (const part of parts) {
      if (!part.trim()) continue;
      let event = "message";
      let data = "";
      for (const line of part.split("\n")) {
        if (line.startsWith("event: ")) event = line.slice(7);
        if (line.startsWith("data: ")) data = line.slice(6);
      }
      if (!data) continue;
      const parsed = JSON.parse(data);
      if (event === "token") handlers.onToken?.(parsed);
      else if (event === "done") handlers.onDone?.(parsed);
      else if (event === "error") handlers.onError?.(parsed);
    }
  }
}

export const api = {
  createGuest: () => apiFetch<{ guestId: string }>("/api/guests", { method: "POST", body: "{}" }),

  generatePlan: (messages: { role: string; content: string }[]) =>
    apiFetch<import("./types").PlanGenerateResponse>("/api/plans/generate", {
      method: "POST",
      body: JSON.stringify({ messages }),
    }),

  activatePlan: (planId: string) =>
    apiFetch<{ status: string }>(`/api/plans/${planId}/activate`, { method: "POST" }),

  getCurrentPlan: () => apiFetch<{
    plan: Record<string, unknown>;
    planStartDate?: string | null;
    workouts: import("./types").Workout[];
    profile: import("./types").AthleteProfile | null;
    readiness: import("./types").ReadinessResult | null;
  }>("/api/plans/current"),

  listWorkouts: (sport?: string, status?: string) => {
    const params = new URLSearchParams();
    if (sport) params.set("sport", sport);
    if (status) params.set("status", status);
    const q = params.toString();
    return apiFetch<{ workouts: import("./types").Workout[] }>(
      `/api/workouts${q ? `?${q}` : ""}`
    );
  },

  completeWorkout: (
    id: string,
    data: {
      completed: boolean;
      rpe?: number;
      readiness_score?: number;
      fatigue_flags?: string[];
      notes?: string;
    }
  ) =>
    apiFetch(`/api/workouts/${id}/complete`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  evaluateAdaptation: () =>
    apiFetch<import("./types").AdaptationEvent>("/api/adaptations/evaluate", {
      method: "POST",
      body: "{}",
    }),

  getPendingAdaptation: () =>
    apiFetch<{ adaptation: import("./types").AdaptationEvent | null }>(
      "/api/adaptations/pending"
    ),

  acceptAdaptation: (eventId: string, accepted: boolean) =>
    apiFetch(`/api/adaptations/${eventId}/accept`, {
      method: "POST",
      body: JSON.stringify({ accepted }),
    }),

  buildFixture: (name: string) =>
    apiFetch<import("./types").PlanGenerateResponse>(
      `/api/fixtures/${name}/build`,
      { method: "POST", body: "{}" }
    ),

  listFixtures: () =>
    apiFetch<{ fixtures: string[] }>("/api/fixtures"),
};
