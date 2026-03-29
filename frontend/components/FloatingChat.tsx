"use client";

import { useState, useRef, useEffect } from "react";

interface Message {
  role: "user" | "assistant";
  text: string;
}

interface FloatingChatProps {
  sessionId: string;
}

function SimpleMarkdown({ text }: { text: string }) {
  const html = text
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.*?)\*/g, "<em>$1</em>")
    .replace(/`(.*?)`/g, '<code class="bg-black/10 px-1 rounded text-xs">$1</code>')
    .replace(/\n/g, "<br />");
  return <span className="font-body" dangerouslySetInnerHTML={{ __html: html }} />;
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
      {open && (
        <div className="mb-4 w-[360px] sm:w-[420px] bg-surface-container-lowest rounded-2xl card-shadow overflow-hidden flex flex-col" style={{ height: "600px" }}>
          {/* Header */}
          <div className="bg-gradient-to-br from-primary to-primary-container text-white px-5 py-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-lg">smart_toy</span>
              <span className="font-headline font-bold text-sm">Chat Assistant</span>
            </div>
            <button onClick={() => setOpen(false)} className="text-white/80 hover:text-white transition-colors" data-action="close-chat">
              <span className="material-symbols-outlined text-lg">close</span>
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center h-full text-center px-6">
                <span className="material-symbols-outlined text-4xl text-on-surface-variant/40 mb-3">forum</span>
                <p className="text-sm text-on-surface-variant font-body">
                  Ask anything about the content you&apos;re studying.
                </p>
              </div>
            )}
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`} data-message={msg.role}>
                {msg.role === "assistant" && (
                  <div className="w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center mr-2 mt-1 flex-shrink-0">
                    <span className="material-symbols-outlined text-primary text-sm">smart_toy</span>
                  </div>
                )}
                <div className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                  msg.role === "user"
                    ? "bg-primary text-white rounded-br-md"
                    : "bg-surface-container-low text-on-surface rounded-bl-md"
                }`}>
                  <SimpleMarkdown text={msg.text} />
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center mr-2 flex-shrink-0">
                  <span className="material-symbols-outlined text-primary text-sm">smart_toy</span>
                </div>
                <div className="bg-surface-container-low rounded-2xl rounded-bl-md px-4 py-3">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-primary/40 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                    <span className="w-2 h-2 bg-primary/40 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                    <span className="w-2 h-2 bg-primary/40 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="p-3 border-t border-outline-variant/15">
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSend()}
                placeholder="Ask a question..."
                className="flex-1 px-4 py-3 bg-surface-container-high rounded-xl text-sm font-body text-on-surface focus:outline-none focus:ring-2 focus:ring-primary placeholder:text-on-surface-variant"
                disabled={loading}
                data-input="chat-message"
              />
              <button
                onClick={handleSend}
                disabled={loading || !input.trim()}
                className="p-3 bg-gradient-to-br from-primary to-primary-container text-white rounded-xl disabled:opacity-50 transition-opacity hover:opacity-90"
                data-action="send-chat"
              >
                <span className="material-symbols-outlined text-lg">send</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* FAB */}
      <button
        onClick={() => setOpen(!open)}
        className="w-14 h-14 rounded-full bg-gradient-to-br from-primary to-primary-container text-white flex items-center justify-center shadow-lg hover:shadow-xl transition-all"
        data-action="toggle-chat"
      >
        <span className="material-symbols-outlined text-2xl">{open ? "close" : "chat"}</span>
      </button>
    </div>
  );
}
