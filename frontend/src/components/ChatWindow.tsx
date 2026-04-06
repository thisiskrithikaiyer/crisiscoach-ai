"use client";

import { useState, useRef, useEffect } from "react";
import { Message, sendMessage } from "@/lib/api";
import ChatBubble from "./ChatBubble";

export default function ChatWindow() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function handleSend() {
    const text = input.trim();
    if (!text || loading) return;

    const updated: Message[] = [...messages, { role: "user", content: text }];
    setMessages(updated);
    setInput("");
    setLoading(true);
    setError(null);

    try {
      const res = await sendMessage(updated);
      setMessages([...updated, { role: "assistant", content: res.reply }]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-3 space-y-1">
        {messages.length === 0 && (
          <p className="text-center text-violet-300 mt-10 text-xs leading-relaxed px-2">
            Hi, I&apos;m CrisisCoach.<br />How are you feeling today?
          </p>
        )}
        {messages.map((m, i) => (
          <ChatBubble key={i} message={m} />
        ))}
        {loading && (
          <div className="flex justify-start mb-1">
            <div className="bg-violet-50 rounded-2xl rounded-bl-sm px-3 py-2 text-xs text-violet-400">
              Thinking…
            </div>
          </div>
        )}
        {error && (
          <p className="text-center text-rose-400 text-xs mt-2 px-2">{error}</p>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-violet-100 p-3 flex gap-2 shrink-0">
        <textarea
          className="flex-1 resize-none border border-violet-200 rounded-xl px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-violet-400 placeholder-violet-300 text-gray-700"
          rows={2}
          placeholder="Type a message…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
        />
        <button
          onClick={handleSend}
          disabled={loading || !input.trim()}
          className="bg-violet-600 hover:bg-violet-700 disabled:opacity-40 text-white rounded-xl px-3 py-2 text-xs font-medium transition-colors shrink-0"
        >
          Send
        </button>
      </div>
    </div>
  );
}
