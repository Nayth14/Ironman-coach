import { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Logo } from "../components/Logo";
import { ReadinessCard } from "../components/ReadinessCard";
import { Button } from "../components/Button";
import { api, streamSSE } from "../lib/api";
import { useAuth } from "../lib/auth";
import { setPendingPlanActivation } from "../lib/authLink";
import { ensureGuestId, setPlanId } from "../lib/guest";
import type { ChatMessage, PlanGenerateResponse } from "../lib/types";
import { DAY_NAMES, formatDate } from "../lib/config";
import { SportIcon } from "../components/SportIcon";

const STARTER_PROMPTS = [
  "I'm racing a full Ironman in 24 weeks",
  "Training for my first 70.3",
  "I want to go sub-12 hours",
  "Help me build base fitness",
];

function CoachAvatar() {
  return (
    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary/10">
      <svg width="18" height="18" viewBox="0 0 32 32" fill="none" aria-hidden>
        <path d="M16 4L28 26H4L16 4Z" fill="#FF5436" />
      </svg>
    </div>
  );
}

function TypingDots() {
  return (
    <span className="inline-flex items-center gap-1">
      {[0, 150, 300].map((delay) => (
        <span
          key={delay}
          className="h-1.5 w-1.5 rounded-full bg-text-muted/60 animate-bounce"
          style={{ animationDelay: `${delay}ms` }}
        />
      ))}
    </span>
  );
}

function coachSignalsPlanReady(content: string): boolean {
  const text = content.trim();
  if (!text || text.endsWith("?")) return false;
  if (text.includes("[[READY_TO_BUILD]]")) return true;
  return /i have all the information i need/i.test(text)
    || /start building your (?:training )?plan/i.test(text)
    || /putting (?:your |together )?(?:training )?plan together/i.test(text)
    || /i(?:'ve| have) got (?:everything|what) i need/i.test(text);
}

export function OnboardingPage() {
  const navigate = useNavigate();
  const { session } = useAuth();
  const [params] = useSearchParams();
  const demo = params.get("demo");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [planProgress, setPlanProgress] = useState<string | null>(null);
  const [result, setResult] = useState<PlanGenerateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    ensureGuestId().then(async () => {
      if (demo) {
        setGenerating(true);
        try {
          const res = await api.buildFixture(demo);
          setResult(res);
          setPlanId(res.planId);
        } catch (e) {
          setError((e as Error).message);
        } finally {
          setGenerating(false);
        }
      } else {
        setMessages([
          {
            role: "assistant",
            content:
              "Hey! I'm your Ironman coach. Let's build a plan that fits your life. What race are you training for, and when is it?",
          },
        ]);
      }
    });
  }, [demo]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, result, planProgress]);

  useEffect(() => {
    if (!streaming && !generating && !result && !demo) {
      inputRef.current?.focus();
    }
  }, [streaming, generating, result, demo, messages.length]);

  const sendMessage = async (text?: string) => {
    const content = (text ?? input).trim();
    if (!content || streaming || generating) return;
    const userMsg: ChatMessage = { role: "user", content };
    const next = [...messages, userMsg];
    setMessages(next);
    setInput("");
    setStreaming(true);
    setError(null);

    let ready = false;
    try {
      await streamSSE("/api/chat/onboarding", { messages: next }, {
        onToken: (d) => {
          setMessages([...next, { role: "assistant", content: d.full }]);
        },
        onDone: async (d) => {
          const final: ChatMessage[] = [...next, { role: "assistant", content: d.content }];
          setMessages(final);
          ready = d.ready ?? false;
          if (!ready && coachSignalsPlanReady(d.content)) ready = true;
          if (ready) await generatePlan(final);
        },
        onError: (d) => setError(d.message),
      });
    } catch (e) {
      setError((e as Error).message);
    } finally {
      if (!ready) setStreaming(false);
    }
  };

  const generatePlan = async (msgs: ChatMessage[]) => {
    setGenerating(true);
    setPlanProgress("Starting your plan…");
    setError(null);
    try {
      await ensureGuestId();
      await api.generatePlan(msgs, {
        onProgress: (d) => setPlanProgress(d.message),
        onDone: (d) => {
          setResult(d);
          setPlanId(d.planId);
          setPlanProgress(null);
        },
        onError: (d) => setError(d.message),
      });
    } catch (e) {
      const msg = (e as Error).message;
      setError(
        msg === "Failed to fetch"
          ? "Plan generation timed out or lost connection. Keep the API running and try sending your last message again."
          : msg
      );
    } finally {
      setGenerating(false);
      setStreaming(false);
    }
  };

  const startWeek1 = () => {
    if (!result) return;
    setPendingPlanActivation(result.planId);
    navigate(session ? "/dashboard" : "/signup?next=/dashboard");
  };

  const showChat = !result && !demo;
  const showStarters =
    showChat && messages.length <= 1 && !streaming && !generating && !input;

  return (
    <div className="min-h-screen bg-bg flex flex-col">
      <header className="px-6 sm:px-8 py-4 border-b border-border bg-white/80 backdrop-blur sticky top-0 z-10">
        <div className="max-w-3xl mx-auto w-full flex items-center justify-between">
          <Logo to="/" />
          {showChat && (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-primary/10 text-primary text-xs font-semibold px-3 py-1">
              <span className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse" />
              Building your plan
            </span>
          )}
        </div>
      </header>

      {showChat && (
        <div className="flex-1 flex flex-col max-w-3xl mx-auto w-full">
          <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-8 space-y-6">
            <div className="space-y-6">
              {messages.map((m, i) => (
                <div
                  key={i}
                  className={`flex items-end gap-2.5 ${
                    m.role === "user" ? "justify-end" : "justify-start"
                  }`}
                >
                  {m.role === "assistant" && <CoachAvatar />}
                  <div
                    className={`max-w-[80%] whitespace-pre-wrap text-sm leading-relaxed px-4 py-3 shadow-sm ${
                      m.role === "user"
                        ? "bg-primary text-white rounded-2xl rounded-br-md"
                        : "bg-white border border-border text-text rounded-2xl rounded-bl-md"
                    }`}
                  >
                    {m.content}
                  </div>
                </div>
              ))}

              {streaming && !generating && (
                <div className="flex items-end gap-2.5 justify-start">
                  <CoachAvatar />
                  <div className="bg-white border border-border rounded-2xl rounded-bl-md px-4 py-3.5 shadow-sm">
                    <TypingDots />
                  </div>
                </div>
              )}

              {generating && planProgress && (
                <div className="flex items-end gap-2.5 justify-start">
                  <CoachAvatar />
                  <div className="bg-white border border-border rounded-2xl rounded-bl-md px-4 py-3 shadow-sm">
                    <div className="flex items-center gap-2 text-sm text-text-muted">
                      <span className="inline-block h-2 w-2 rounded-full bg-primary animate-pulse" />
                      {planProgress}
                    </div>
                  </div>
                </div>
              )}

              {error && (
                <div className="bg-red-50 border border-red-200 rounded-2xl p-4 text-red-700 text-sm">
                  {error}
                </div>
              )}
            </div>
            <div ref={bottomRef} />
          </div>

          <div className="sticky bottom-0 px-4 sm:px-6 pb-6 pt-2 bg-gradient-to-t from-bg via-bg to-transparent">
            {showStarters && (
              <div className="flex flex-wrap gap-2 mb-3">
                {STARTER_PROMPTS.map((p) => (
                  <button
                    key={p}
                    onClick={() => sendMessage(p)}
                    className="rounded-full border border-border bg-white px-3.5 py-1.5 text-xs font-medium text-text-muted hover:border-primary hover:text-primary transition-colors"
                  >
                    {p}
                  </button>
                ))}
              </div>
            )}
            <div className="flex items-center gap-2 rounded-full border border-border bg-white p-1.5 pl-5 shadow-sm focus-within:border-primary transition-colors">
              <input
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && sendMessage()}
                placeholder="Talk to your coach…"
                className="flex-1 bg-transparent text-sm outline-none placeholder:text-text-muted"
                disabled={streaming || generating}
                autoFocus
              />
              <button
                onClick={() => sendMessage()}
                disabled={streaming || generating || !input.trim()}
                aria-label="Send message"
                className="h-9 w-9 shrink-0 rounded-full bg-primary text-white flex items-center justify-center hover:bg-primary-hover disabled:opacity-40 disabled:hover:bg-primary transition-colors"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden>
                  <path
                    d="M12 19V5M12 5l-6 6M12 5l6 6"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </button>
            </div>
            <p className="text-center text-xs text-text-muted mt-3">
              Your coach uses your answers to build a fully personalized plan.
            </p>
          </div>
        </div>
      )}

      {!showChat && (
        <div className="flex-1 max-w-2xl mx-auto w-full px-4 sm:px-6 py-8 space-y-4">
          {generating && planProgress && (
            <div className="bg-white rounded-2xl border border-border p-8 text-center">
              <div className="flex items-center justify-center gap-2 text-text-muted">
                <span className="inline-block h-2 w-2 rounded-full bg-primary animate-pulse" />
                {planProgress}
              </div>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-2xl p-4 text-red-700 text-sm">
              {error}
            </div>
          )}

          {result && (
            <>
              <div className="text-center mb-2">
                <div className="inline-flex h-12 w-12 items-center justify-center rounded-full bg-green-100 text-2xl mb-3">
                  🎉
                </div>
                <h1 className="text-2xl font-bold tracking-tight">Your plan is ready</h1>
              </div>

              <div className="bg-green-50 border border-green-200 rounded-2xl p-4 text-sm">
                {result.summary}
              </div>

              <ReadinessCard
                verdict={result.readiness.verdict}
                rationale={result.readiness.rationale}
                weeksToRace={result.readiness.weeks_to_race}
                adjustments={result.readiness.adjustments}
              />

              <div className="bg-white rounded-2xl border border-border p-5">
                <h3 className="font-semibold mb-3">
                  Macrocycle ({result.plan.total_weeks} weeks)
                </h3>
                <div className="space-y-2">
                  {result.plan.phases.map((p) => (
                    <div
                      key={p.name}
                      className="flex justify-between text-sm bg-gray-50 rounded-lg px-3 py-2"
                    >
                      <span className="font-medium capitalize">{p.name}</span>
                      <span className="text-text-muted">
                        wk {p.start_week}–{p.end_week}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-white rounded-2xl border border-border p-5">
                <h3 className="font-semibold mb-3">First weeks preview</h3>
                {result.plan.weeks.map((wk) => (
                  <div key={wk.week_number} className="mb-4">
                    <div className="text-sm font-medium mb-2">
                      Week {wk.week_number} · {wk.phase}
                      {wk.is_deload && " · deload"} · {wk.target_hours}h
                    </div>
                    <div className="space-y-1">
                      {wk.workouts.map((w) => (
                        <div
                          key={w.id}
                          className="flex items-center gap-2 text-sm bg-gray-50 rounded-lg px-3 py-2"
                        >
                          <SportIcon sport={w.sport} size="sm" />
                          <span className="flex-1">{w.title}</span>
                          <span className="text-text-muted text-xs">
                            {w.scheduled_date
                              ? formatDate(w.scheduled_date)
                              : w.day_of_week != null
                                ? DAY_NAMES[w.day_of_week]
                                : ""}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              <Button onClick={startWeek1} className="w-full">
                Start week 1
              </Button>
            </>
          )}

          {!result && !generating && demo && (
            <div className="text-text-muted text-sm text-center">Loading sample plan…</div>
          )}
        </div>
      )}
    </div>
  );
}
