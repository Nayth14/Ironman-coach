import { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Logo } from "../components/Logo";
import { ReadinessCard } from "../components/ReadinessCard";
import { Button } from "../components/Button";
import { api, streamSSE } from "../lib/api";
import { useAuth } from "../lib/auth";
import { setPendingPlanActivation, linkGuestIfNeeded } from "../lib/authLink";
import { ensureGuestId, setPlanId } from "../lib/guest";
import type { ChatMessage, PlanGenerateResponse } from "../lib/types";
import { DAY_NAMES, formatDate } from "../lib/config";
import { SportIcon } from "../components/SportIcon";

export function OnboardingPage() {
  const navigate = useNavigate();
  const { session } = useAuth();
  const [params] = useSearchParams();
  const demo = params.get("demo");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [result, setResult] = useState<PlanGenerateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

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
  }, [messages, result]);

  const sendMessage = async () => {
    if (!input.trim() || streaming) return;
    const userMsg: ChatMessage = { role: "user", content: input.trim() };
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
          if (ready) await generatePlan(final);
        },
        onError: (d) => setError(d.message),
      });
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setStreaming(false);
    }
  };

  const generatePlan = async (msgs: ChatMessage[]) => {
    setGenerating(true);
    setError(null);
    try {
      const res = await api.generatePlan(msgs);
      setResult(res);
      setPlanId(res.planId);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setGenerating(false);
    }
  };

  const startWeek1 = async () => {
    if (!result) return;
    if (!session) {
      setPendingPlanActivation(result.planId);
      navigate("/signup?next=/dashboard");
      return;
    }
    try {
      await linkGuestIfNeeded();
      await api.activatePlan(result.planId);
      navigate("/dashboard");
    } catch (e) {
      setError((e as Error).message);
    }
  };

  return (
    <div className="min-h-screen bg-bg flex flex-col">
      <header className="px-8 py-4 border-b border-border bg-white">
        <Logo />
      </header>

      <div className="flex-1 max-w-6xl mx-auto w-full p-6 grid lg:grid-cols-2 gap-6">
        {!result && !demo && (
          <div className="bg-white rounded-2xl border border-border flex flex-col h-[70vh]">
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((m, i) => (
                <div
                  key={i}
                  className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm ${
                      m.role === "user" ? "bg-primary text-white" : "bg-gray-50"
                    }`}
                  >
                    {m.content}
                  </div>
                </div>
              ))}
              {streaming && (
                <div className="text-text-muted text-sm animate-pulse">Coach is typing…</div>
              )}
              <div ref={bottomRef} />
            </div>
            <footer className="p-4 border-t border-border">
              <div className="flex gap-2">
                <input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && sendMessage()}
                  placeholder="Talk to your coach…"
                  className="flex-1 rounded-full border border-border px-4 py-2.5 text-sm outline-none focus:border-primary"
                  disabled={streaming || generating}
                />
                <button
                  onClick={sendMessage}
                  disabled={streaming || generating || !input.trim()}
                  className="rounded-full bg-primary text-white px-5 py-2 text-sm font-semibold disabled:opacity-50"
                >
                  Send
                </button>
              </div>
            </footer>
          </div>
        )}

        <div className="space-y-4">
          {generating && (
            <div className="bg-white rounded-2xl border border-border p-8 text-center">
              <div className="animate-pulse text-text-muted">Building your plan…</div>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-2xl p-4 text-red-700 text-sm">
              {error}
            </div>
          )}

          {result && (
            <>
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
            <div className="text-text-muted text-sm">Loading sample plan…</div>
          )}
        </div>
      </div>
    </div>
  );
}
