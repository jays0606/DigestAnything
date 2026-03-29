"use client";

import { useState, useRef, useEffect } from "react";

interface Message {
  role: "user" | "assistant";
  text: string;
}

interface FloatingChatProps {
  sessionId: string;
}

export default function FloatingChat({ sessionId }: FloatingChatProps) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const userMsg = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", text: userMsg }]);
    setLoading(true);

    try {
      const res = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMsg, session_id: sessionId }),
      });
      const data = await res.json();
      setMessages((prev) => [...prev, { role: "assistant", text: data.response }]);
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", text: "Sorry, something went wrong." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-50" data-component="floating-chat">
      {/* Chat window */}
      {open && (
        <div className="mb-4 w-80 sm:w-96 bg-surface-container-lowest rounded-xl card-shadow overflow-hidden flex flex-col" style={{ height: "440px" }}>
          {/* Header */}
          <div className="bg-gradient-to-br from-primary to-primary-container text-white px-4 py-3 flex items-center justify-between">
            <span className="font-headline font-bold text-sm">Chat Assistant</span>
            <button onClick={() => setOpen(false)} className="text-white/80 hover:text-white" data-action="close-chat">
              <span className="material-symbols-outlined text-lg">close</span>
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {messages.length === 0 && (
              <p className="text-sm text-on-surface-variant font-body text-center mt-8">
                Ask anything about the content you're studying.
              </p>
            )}
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`} data-message={msg.role}>
                <div className={`max-w-[85%] rounded-xl px-3 py-2 text-sm ${
                  msg.role === "user"
                    ? "bg-primary text-white"
                    : "bg-surface-container-low text-on-surface"
                }`}>
                  <p className="font-body whitespace-pre-wrap">{msg.text}</p>
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-surface-container-low rounded-xl px-3 py-2">
                  <span className="material-symbols-outlined animate-spin text-primary text-xs">progress_activity</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="p-3 flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              placeholder="Ask a question..."
              className="flex-1 px-3 py-2 bg-surface-container-high rounded-lg text-sm font-body text-on-surface focus:outline-none focus:ring-2 focus:ring-primary"
              disabled={loading}
              data-input="chat-message"
            />
            <button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              className="p-2 bg-primary text-white rounded-lg disabled:opacity-50"
              data-action="send-chat"
            >
              <span className="material-symbols-outlined text-lg">send</span>
            </button>
          </div>
        </div>
      )}

      {/* FAB */}
      <button
        onClick={() => setOpen(!open)}
        className="w-14 h-14 rounded-full bg-gradient-to-br from-primary to-primary-container text-white flex items-center justify-center shadow-lg hover:shadow-xl transition-shadow"
        data-action="toggle-chat"
      >
        <span className="material-symbols-outlined text-2xl">{open ? "close" : "chat"}</span>
      </button>
    </div>
  );
}
