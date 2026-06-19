import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type { Provider, Session, User } from "@supabase/supabase-js";
import {
  clearDevSession,
  createDevSession,
  loadDevSession,
  saveDevSession,
} from "./devAuth";
import { resetAuthBootstrap } from "./authLink";
import { isSupabaseConfigured, supabase } from "./supabase";

interface AuthContextValue {
  session: Session | null;
  user: User | null;
  loading: boolean;
  isConfigured: boolean;
  signInWithPassword: (email: string, password: string) => Promise<{ error: string | null }>;
  signUp: (
    email: string,
    password: string,
    metadata?: { firstName?: string }
  ) => Promise<{ error: string | null }>;
  signInWithOAuth: (provider: Provider) => Promise<{ error: string | null }>;
  resetPasswordForEmail: (email: string) => Promise<{ error: string | null }>;
  updatePassword: (password: string) => Promise<{ error: string | null }>;
  signOut: () => Promise<void>;
  getAccessToken: () => string | null;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isSupabaseConfigured || !supabase) {
      setSession(loadDevSession());
      setLoading(false);
      return;
    }

    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session);
      setLoading(false);
    });

    const { data: sub } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession);
      setLoading(false);
    });

    return () => sub.subscription.unsubscribe();
  }, []);

  const signInWithPassword = useCallback(async (email: string, password: string) => {
    if (!isSupabaseConfigured || !supabase) {
      if (!email || !password) return { error: "Email and password required" };
      const devSession = createDevSession(email);
      setSession(devSession);
      return { error: null };
    }
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    return { error: error?.message ?? null };
  }, []);

  const signUp = useCallback(
    async (email: string, password: string, metadata?: { firstName?: string }) => {
      if (!isSupabaseConfigured || !supabase) {
        if (!email || !password) return { error: "Email and password required" };
        const devSession = createDevSession(email);
        setSession(devSession);
        return { error: null };
      }
      const { error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: metadata?.firstName ? { first_name: metadata.firstName } : undefined,
          emailRedirectTo: `${window.location.origin}/auth/callback`,
        },
      });
      return { error: error?.message ?? null };
    },
    []
  );

  const signInWithOAuth = useCallback(async (provider: Provider) => {
    if (!isSupabaseConfigured || !supabase) {
      return { error: "OAuth requires Supabase configuration" };
    }
    const { error } = await supabase.auth.signInWithOAuth({
      provider,
      options: { redirectTo: `${window.location.origin}/auth/callback` },
    });
    return { error: error?.message ?? null };
  }, []);

  const resetPasswordForEmail = useCallback(async (email: string) => {
    if (!isSupabaseConfigured || !supabase) {
      if (!email) return { error: "Email required" };
      return { error: null };
    }
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/reset-password`,
    });
    return { error: error?.message ?? null };
  }, []);

  const updatePassword = useCallback(async (password: string) => {
    if (!isSupabaseConfigured || !supabase) {
      if (!password) return { error: "Password required" };
      return { error: null };
    }
    const { error } = await supabase.auth.updateUser({ password });
    return { error: error?.message ?? null };
  }, []);

  const signOut = useCallback(async () => {
    resetAuthBootstrap();
    if (!isSupabaseConfigured || !supabase) {
      clearDevSession();
      setSession(null);
      return;
    }
    await supabase.auth.signOut();
    setSession(null);
  }, []);

  const getAccessToken = useCallback(() => session?.access_token ?? null, [session]);

  const value = useMemo<AuthContextValue>(
    () => ({
      session,
      user: session?.user ?? null,
      loading,
      isConfigured: isSupabaseConfigured,
      signInWithPassword,
      signUp,
      signInWithOAuth,
      resetPasswordForEmail,
      updatePassword,
      signOut,
      getAccessToken,
    }),
    [
      session,
      loading,
      signInWithPassword,
      signUp,
      signInWithOAuth,
      resetPasswordForEmail,
      updatePassword,
      signOut,
      getAccessToken,
    ]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

export { saveDevSession };
