import { useEffect, useRef, useState } from "react";
import { api, streamSSE } from "../lib/api";
import type { AdaptationEvent, ChatMessage } from "../lib/types";

interface Props {
  hasCompletions: boolean;
  onAdaptation: (event: AdaptationEvent) => void;
  llmAvailable?: boolean;
}

export function WeeklyCheckinPanel({
  hasCompletions,
  onAdaptation,
  llmAvailable = true,
}: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [ready, setReady] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (hasCompletions && messages.length === 0) {
      setMessages([
        {
          role: "assistant",
          content:
            "How did this week go? Tell me anything that stood out — sleep, stress, missed sessions, niggles, or how you felt overall.",
        },
      ]);
    }
  }, [hasCompletions, messages.length]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (!hasCompletions) return null;

  const sendMessage = async () => {
    if (!input.trim() || streaming || !llmAvailable) return;
    const userMsg: ChatMessage = { role: "user", content: input.trim() };
    const next = [...messages, userMsg];
    setMessages(next);
    setInput("");
    setStreaming(true);
    setError(null);
    setReady(false);

    try {
      await streamSSE(
        "/api/chat/weekly-checkin",
        { messages: next },
        {
          onToken: (d) => {
            setMessages([...next, { role: "assistant", content: d.full }]);
          },
          onDone: (d) => {
            setMessages([...next, { role: "assistant", content: d.content }]);
            setReady(d.ready ?? false);
          },
          onError: (d) => setError(d.message),
        },
        "auth"
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setStreaming(false);
    }
  };

  const runEvaluate = async (weeklyCheckinId?: string) => {
    setSubmitting(true);
    setError(null);
    try {
      const ev = await api.evaluateAdaptation(
        weeklyCheckinId ? { weeklyCheckinId } : undefined
      );
      onAdaptation(ev);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSubmitting(false);
    }
  };

  const getRecommendation = async () => {
    setSubmitting(true);
    setError(null);
    try {
      const extracted = await api.extractWeeklyContext(messages);
      await runEvaluate(extracted.checkinId);
    } catch (e) {
      setError((e as Error).message);
      setSubmitting(false);
    }
  };

  return (
    <div className="rounded-2xl border border-border bg-white p-5 mb-6">
      <h3 className="font-semibold mb-1">Weekly check-in</h3>
      <p className="text-sm text-text-muted mb-4">
        Describe your week in your own words — we&apos;ll use it alongside your workout
        data for adaptation.
      </p>

      {!llmAvailable && (
        <p className="text-sm text-amber-700 bg-amber-50 rounded-lg px-3 py-2 mb-4">
          Natural-language check-in is unavailable (no OpenAI key). You can still get a
          structured adaptation recommendation.
        </p>
      )}

      {llmAvailable && (
        <div className="max-h-64 overflow-y-auto space-y-3 mb-4 pr-1">
          {messages.map((m, i) => (
            <div
              key={i}
              className={`text-sm rounded-xl px-3 py-2 ${
                m.role === "user"
                  ? "bg-primary/10 ml-8"
                  : "bg-gray-100 mr-8"
              }`}
            >
              {m.content}
            </div>
          ))}
          <div ref={bottomRef} />
        </div>
      )}

      {llmAvailable && (
        <div className="flex gap-2 mb-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            placeholder="Anything else that happened this week…"
            disabled={streaming}
            className="flex-1 rounded-full border border-border px-4 py-2 text-sm"
          />
          <button
            onClick={sendMessage}
            disabled={streaming || !input.trim()}
            className="rounded-full bg-text text-white px-4 py-2 text-sm font-medium disabled:opacity-50"
          >
            Send
          </button>
        </div>
      )}

      <div className="flex flex-wrap gap-2 items-center">
        {llmAvailable && (
          <button
            onClick={getRecommendation}
            disabled={!ready || submitting || streaming}
            className="rounded-full bg-primary text-white px-4 py-2 text-sm font-semibold disabled:opacity-50"
          >
            {submitting ? "Evaluating…" : "Get adaptation recommendation"}
          </button>
        )}
        <button
          onClick={() => runEvaluate()}
          disabled={submitting}
          className="rounded-full border border-border px-4 py-2 text-sm font-medium"
        >
          {llmAvailable ? "Skip check-in" : "Get recommendation"}
        </button>
      </div>

      {error && <p className="text-sm text-red-600 mt-3">{error}</p>}
    </div>
  );
}
