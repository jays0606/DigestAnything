"use client";

import { useState, useEffect, useRef } from "react";

interface Message {
  role: "user" | "tutor";
  text: string;
}

interface TutorTabProps {
  sessionId: string;
  concepts: { term: string; definition: string }[];
}

function SimpleMarkdown({ text }: { text: string }) {
  const html = text
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.*?)\*/g, "<em>$1</em>")
    .replace(/`(.*?)`/g, '<code class="bg-black/10 px-1 rounded text-xs">$1</code>')
    .replace(/\n/g, "<br />");
  return <span className="font-body" dangerouslySetInnerHTML={{ __html: html }} />;
}

export default function TutorTab({ sessionId, concepts }: TutorTabProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const initialized = useRef(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => { scrollToBottom(); }, [messages]);

  // Auto-start
  useEffect(() => {
    if (initialized.current || concepts.length === 0) return;
    initialized.current = true;
    const concept = concepts[0]?.term || "the main topic";
    setMessages([{
      role: "tutor",
      text: `Hey! I'm Feynman, your Socratic tutor. Let's use the Feynman technique — try explaining **"${concept}"** in your own words, as if you're teaching it to a friend. What would you say?`,
    }]);
  }, [concepts]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const userMsg = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", text: userMsg }]);
    setLoading(true);

    try {
      const res = await fetch("http://localhost:8000/api/tutor", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMsg, session_id: sessionId }),
      });
      const data = await res.json();
      setMessages((prev) => [...prev, { role: "tutor", text: data.response }]);
    } catch {
      setMessages((prev) => [...prev, { role: "tutor", text: "Sorry, I had trouble responding. Try again?" }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4" data-component="tutor">
      {/* Chat messages */}
      <div className="bg-surface-container-lowest rounded-2xl card-shadow p-6 h-[600px] overflow-y-auto">
        <div className="space-y-4">
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`} data-message={msg.role}>
              {msg.role === "tutor" && (
                <div className="w-8 h-8 rounded-full bg-secondary/10 flex items-center justify-center mr-3 mt-1 flex-shrink-0">
                  <span className="material-symbols-outlined text-secondary text-sm">school</span>
                </div>
              )}
              <div className={`max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                msg.role === "user"
                  ? "bg-primary text-white rounded-br-md"
                  : "bg-surface-container-low text-on-surface rounded-bl-md"
              }`}>
                {msg.role === "tutor" && (
                  <span className="text-xs font-bold text-secondary font-label block mb-1.5">Feynman</span>
                )}
                <SimpleMarkdown text={msg.text} />
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="w-8 h-8 rounded-full bg-secondary/10 flex items-center justify-center mr-3 flex-shrink-0">
                <span className="material-symbols-outlined text-secondary text-sm">school</span>
              </div>
              <div className="bg-surface-container-low rounded-2xl rounded-bl-md px-4 py-3">
                <div className="flex gap-1">
                  <span className="w-2 h-2 bg-secondary/40 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                  <span className="w-2 h-2 bg-secondary/40 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                  <span className="w-2 h-2 bg-secondary/40 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="flex gap-3">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Try explaining the concept in your own words..."
          className="flex-1 px-4 py-3 bg-surface-container-high rounded-xl text-on-surface font-body text-sm focus:outline-none focus:ring-2 focus:ring-primary placeholder:text-on-surface-variant"
          disabled={loading}
          data-input="tutor-message"
        />
        <button
          onClick={handleSend}
          disabled={loading || !input.trim()}
          className="px-5 py-3 bg-gradient-to-br from-primary to-primary-container text-white rounded-xl font-headline font-bold text-sm disabled:opacity-50 transition-opacity hover:opacity-90"
          data-action="send-tutor"
        >
          Send
        </button>
      </div>
    </div>
  );
}
