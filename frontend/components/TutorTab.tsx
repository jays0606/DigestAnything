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

export default function TutorTab({ sessionId, concepts }: TutorTabProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [selectedConcept, setSelectedConcept] = useState(concepts[0]?.term || "");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const initialized = useRef(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Auto-start: immediately prompt the user
  useEffect(() => {
    if (initialized.current || concepts.length === 0) return;
    initialized.current = true;
    const concept = concepts[0]?.term || "the main topic";
    const introMessage: Message = {
      role: "tutor",
      text: `Hey! Let's use the Feynman technique. Try explaining "${concept}" in your own words — as if you're teaching it to a friend. What would you say?`,
    };
    setMessages([introMessage]);
  }, [concepts]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const userMsg = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", text: userMsg }]);
    setLoading(true);

    try {
      const res = await fetch("/api/tutor", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userMsg,
          session_id: sessionId,
          concept: selectedConcept || undefined,
        }),
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
      {/* Concept selector */}
      {concepts.length > 0 && (
        <div className="flex items-center gap-3">
          <span className="text-sm font-label text-on-surface-variant">Focus on:</span>
          <select
            value={selectedConcept}
            onChange={(e) => setSelectedConcept(e.target.value)}
            className="px-3 py-1.5 bg-surface-container-high rounded-lg text-sm font-body text-on-surface focus:outline-none focus:ring-2 focus:ring-primary"
            data-select="concept"
          >
            {concepts.map((c) => (
              <option key={c.term} value={c.term}>{c.term}</option>
            ))}
          </select>
        </div>
      )}

      {/* Chat messages */}
      <div className="bg-surface-container-lowest rounded-xl card-shadow p-6 h-[500px] overflow-y-auto">
        <div className="space-y-4">
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`} data-message={msg.role}>
              <div className={`max-w-[80%] rounded-xl px-4 py-3 ${
                msg.role === "user"
                  ? "bg-primary text-white"
                  : "bg-surface-container-low text-on-surface"
              }`}>
                {msg.role === "tutor" && (
                  <span className="text-xs font-bold text-primary font-label block mb-1">Sage</span>
                )}
                <p className="font-body text-sm whitespace-pre-wrap">{msg.text}</p>
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-surface-container-low rounded-xl px-4 py-3">
                <span className="material-symbols-outlined animate-spin text-primary text-sm">progress_activity</span>
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
          className="flex-1 px-4 py-3 bg-surface-container-high rounded-xl text-on-surface font-body text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          disabled={loading}
          data-input="tutor-message"
        />
        <button
          onClick={handleSend}
          disabled={loading || !input.trim()}
          className="px-5 py-3 bg-gradient-to-br from-primary to-primary-container text-white rounded-xl font-headline font-bold text-sm disabled:opacity-50"
          data-action="send-tutor"
        >
          Send
        </button>
      </div>
    </div>
  );
}
