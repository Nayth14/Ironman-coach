import type { Session, User } from "@supabase/supabase-js";

const DEV_USER_KEY = "ironman_coach_dev_user_id";
const DEV_SESSION_KEY = "ironman_coach_dev_session";

function b64url(data: string): string {
  return btoa(data).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

export function createDevAccessToken(userId: string): string {
  const header = b64url(JSON.stringify({ alg: "HS256", typ: "JWT" }));
  const payload = b64url(
    JSON.stringify({
      sub: userId,
      aud: "authenticated",
      exp: Math.floor(Date.now() / 1000) + 60 * 60 * 24 * 30,
    })
  );
  return `${header}.${payload}.dev-signature`;
}

function getOrCreateDevUserId(): string {
  let id = localStorage.getItem(DEV_USER_KEY);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(DEV_USER_KEY, id);
  }
  return id;
}

export function loadDevSession(): Session | null {
  const raw = localStorage.getItem(DEV_SESSION_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as Session;
  } catch {
    return null;
  }
}

export function saveDevSession(session: Session | null): void {
  if (!session) {
    localStorage.removeItem(DEV_SESSION_KEY);
    return;
  }
  localStorage.setItem(DEV_SESSION_KEY, JSON.stringify(session));
}

export function createDevSession(email: string): Session {
  const userId = getOrCreateDevUserId();
  const accessToken = createDevAccessToken(userId);
  const user: User = {
    id: userId,
    aud: "authenticated",
    role: "authenticated",
    email,
    email_confirmed_at: new Date().toISOString(),
    phone: "",
    confirmed_at: new Date().toISOString(),
    last_sign_in_at: new Date().toISOString(),
    app_metadata: {},
    user_metadata: {},
    identities: [],
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    is_anonymous: false,
  };
  const session: Session = {
    access_token: accessToken,
    refresh_token: "dev-refresh",
    expires_in: 60 * 60 * 24 * 30,
    expires_at: Math.floor(Date.now() / 1000) + 60 * 60 * 24 * 30,
    token_type: "bearer",
    user,
  };
  saveDevSession(session);
  return session;
}

export function clearDevSession(): void {
  saveDevSession(null);
}
