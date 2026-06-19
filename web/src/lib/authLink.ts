import { api } from "./api";
import { getGuestId } from "./guest";

const PENDING_PLAN_KEY = "ironman_coach_pending_plan_activation";

export function setPendingPlanActivation(planId: string): void {
  sessionStorage.setItem(PENDING_PLAN_KEY, planId);
}

export function getPendingPlanActivation(): string | null {
  return sessionStorage.getItem(PENDING_PLAN_KEY);
}

export function clearPendingPlanActivation(): void {
  sessionStorage.removeItem(PENDING_PLAN_KEY);
}

export type LinkGuestResult =
  | { ok: true; athleteId: string }
  | { ok: false; reason: "no_guest" | "not_found" | "conflict" | "error"; message?: string };

export async function linkGuestIfNeeded(): Promise<LinkGuestResult> {
  const guestId = getGuestId();
  if (!guestId) return { ok: false, reason: "no_guest" };

  try {
    const res = await api.linkGuest();
    return { ok: true, athleteId: res.athleteId };
  } catch (e) {
    const message = (e as Error).message;
    if (message.includes("404") || message.toLowerCase().includes("not found")) {
      return { ok: false, reason: "not_found", message };
    }
    if (message.includes("409") || message.toLowerCase().includes("conflict")) {
      return { ok: false, reason: "conflict", message };
    }
    return { ok: false, reason: "error", message };
  }
}

export async function activatePendingPlanIfNeeded(): Promise<void> {
  const planId = getPendingPlanActivation();
  if (!planId) return;
  await api.activatePlan(planId);
  clearPendingPlanActivation();
}

export type AuthBootstrapResult =
  | { ok: true }
  | { ok: false; reason: "conflict" | "error"; message?: string };

let bootstrapPromise: Promise<AuthBootstrapResult> | null = null;
let bootstrapCacheKey: string | null = null;

export function resetAuthBootstrap(): void {
  bootstrapPromise = null;
  bootstrapCacheKey = null;
}

/** Link guest + activate pending plan once per auth session (deduped). */
export async function runAuthBootstrap(accessToken: string | null): Promise<AuthBootstrapResult> {
  const cacheKey = accessToken ?? "anonymous";
  if (bootstrapPromise && bootstrapCacheKey === cacheKey) {
    return bootstrapPromise;
  }

  bootstrapCacheKey = cacheKey;
  bootstrapPromise = (async (): Promise<AuthBootstrapResult> => {
    const link = await linkGuestIfNeeded();
    if (link.ok === false && link.reason === "conflict") {
      return { ok: false, reason: "conflict", message: link.message };
    }
    try {
      await activatePendingPlanIfNeeded();
    } catch (e) {
      return { ok: false, reason: "error", message: (e as Error).message };
    }
    return { ok: true };
  })();

  return bootstrapPromise;
}
