import { useState } from "react";
import { streamSSE } from "../lib/api";
import type { ChatMessage } from "../lib/types";

interface Props {
  open: boolean;
  onClose: () => void;
}

export function CoachChatPanel({ open, onClose }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content:
        "Hi! I'm your AI coach. Ask me about workouts, pacing, fueling, or how your plan fits together.",
    },
  ]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);

  const send = async () => {
    if (!input.trim() || streaming) return;
    const userMsg: ChatMessage = { role: "user", content: input.trim() };
    const next = [...messages, userMsg];
    setMessages(next);
    setInput("");
    setStreaming(true);

    try {
      await streamSSE(
        "/api/chat/coaching",
        { messages: next },
        {
          onToken: (d) => {
            setMessages([...next, { role: "assistant", content: d.full }]);
          },
          onDone: (d) => {
            setMessages([...next, { role: "assistant", content: d.content }]);
          },
          onError: (d) => {
            setMessages([
              ...next,
              { role: "assistant", content: `Error: ${d.message}` },
            ]);
          },
        }
      );
    } catch (e) {
      setMessages([
        ...next,
        { role: "assistant", content: `Error: ${(e as Error).message}` },
      ]);
    } finally {
      setStreaming(false);
    }
  };

  if (!open) return null;

  return (
    <>
      <div className="fixed inset-0 bg-black/30 z-40" onClick={onClose} />
      <aside className="fixed right-0 top-0 h-full w-full max-w-md bg-white shadow-2xl z-50 flex flex-col">
        <header className="flex items-center justify-between px-5 py-4 border-b border-border">
          <div className="flex items-center gap-2">
            <span className="text-xl">🤖</span>
            <span className="font-semibold">Coach Chat</span>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full hover:bg-gray-100 flex items-center justify-center"
          >
            ✕
          </button>
        </header>

        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((m, i) => (
            <div
              key={i}
              className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm ${
                  m.role === "user"
                    ? "bg-primary text-white"
                    : "bg-gray-50 text-text"
                }`}
              >
                {m.content}
              </div>
            </div>
          ))}
          {streaming && (
            <div className="text-text-muted text-sm animate-pulse">Coach is typing…</div>
          )}
        </div>

        <footer className="p-4 border-t border-border">
          <div className="flex gap-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && send()}
              placeholder="Ask your AI coach…"
              className="flex-1 rounded-full border border-border px-4 py-2.5 text-sm outline-none focus:border-primary"
              disabled={streaming}
            />
            <button
              onClick={send}
              disabled={streaming || !input.trim()}
              className="w-10 h-10 rounded-full bg-primary text-white flex items-center justify-center disabled:opacity-50"
            >
              ↑
            </button>
          </div>
        </footer>
      </aside>
    </>
  );
}

export function CoachChatFab({ onClick }: { onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="fixed bottom-6 right-6 w-14 h-14 rounded-full bg-primary text-white shadow-lg hover:bg-primary-hover flex items-center justify-center text-xl z-30"
      aria-label="Open coach chat"
    >
      💬
    </button>
  );
}
