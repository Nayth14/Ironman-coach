import { apiPath } from "./config";

const GUEST_KEY = "ironman_coach_guest_id";
const PLAN_KEY = "ironman_coach_plan_id";

export function getGuestId(): string | null {
  return localStorage.getItem(GUEST_KEY);
}

export function setGuestId(id: string): void {
  localStorage.setItem(GUEST_KEY, id);
}

export function getPlanId(): string | null {
  return localStorage.getItem(PLAN_KEY);
}

export function setPlanId(id: string): void {
  localStorage.setItem(PLAN_KEY, id);
}

export async function ensureGuestId(): Promise<string> {
  let id = getGuestId();
  if (id) return id;
  const res = await fetch(apiPath("/api/guests"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: "{}",
  });
  if (!res.ok) throw new Error("Failed to create guest");
  const data = (await res.json()) as { guestId: string };
  id = data.guestId;
  setGuestId(id);
  return id;
}
