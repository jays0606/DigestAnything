"use client";

import { useState, useCallback } from "react";
import SourceInput from "../components/SourceInput";
import TabBar from "../components/TabBar";
import Overview from "../components/Overview";
import LoadingState from "../components/LoadingState";
import QuizMode from "../components/QuizMode";
import FlashCards from "../components/FlashCards";
import TutorTab from "../components/TutorTab";
import FloatingChat from "../components/FloatingChat";
import PodcastPlayer from "../components/PodcastPlayer";

const API = "http://localhost:8000";

type DigestData = {
  context: any;
  markmap: string | null;
  quiz: any | null;
  cards: any | null;
  podcast: any | null;
};

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<DigestData | null>(null);
  const [activeTab, setActiveTab] = useState("overview");
  const [readyTabs, setReadyTabs] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);

  const processContext = useCallback(async (context: any) => {
    // Show overview immediately (without markmap yet)
    setData({ context, markmap: null, quiz: null, cards: null, podcast: null });
    setLoading(false);
    setReadyTabs(new Set(["overview", "tutor"]));

    const post = (path: string) =>
      fetch(`${API}${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(context),
      }).then(r => r.json());

    // Fire ALL 4 in parallel — each updates state independently when done
    post("/api/visual").then(v => {
      setData(prev => prev ? { ...prev, markmap: v.markdown || null } : prev);
    }).catch(() => {});

    post("/api/quiz").then(q => {
      setData(prev => prev ? { ...prev, quiz: q } : prev);
      setReadyTabs(prev => new Set([...prev, "quiz"]));
    }).catch(() => {});

    post("/api/cards").then(c => {
      setData(prev => prev ? { ...prev, cards: c } : prev);
      setReadyTabs(prev => new Set([...prev, "cards"]));
    }).catch(() => {});

    post("/api/podcast").then(p => {
      setData(prev => prev ? { ...prev, podcast: p } : prev);
      setReadyTabs(prev => new Set([...prev, "podcast"]));
    }).catch(() => {});
  }, []);

  const handleSubmit = useCallback(async (source: string) => {
    setLoading(true);
    setError(null);
    setData(null);
    setReadyTabs(new Set());
    setActiveTab("overview");

    try {
      // Step 1: Ingest — get context
      const ingestRes = await fetch(`${API}/api/ingest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source }),
      });
      if (!ingestRes.ok) throw new Error(`Ingest failed: ${ingestRes.status}`);
      const context = await ingestRes.json();
      await processContext(context);
    } catch (err: any) {
      setError(err.message || "Something went wrong");
      setLoading(false);
    }
  }, [processContext]);

  const handleFileUpload = useCallback(async (file: File) => {
    setLoading(true);
    setError(null);
    setData(null);
    setReadyTabs(new Set());
    setActiveTab("overview");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const uploadRes = await fetch(`${API}/api/upload`, {
        method: "POST",
        body: formData,
      });
      if (!uploadRes.ok) throw new Error(`Upload failed: ${uploadRes.status}`);
      const context = await uploadRes.json();
      await processContext(context);
    } catch (err: any) {
      setError(err.message || "Something went wrong");
      setLoading(false);
    }
  }, [processContext]);

  return (
    <div className="min-h-screen">
      {/* Glass Header */}
      <header className="fixed top-0 w-full z-50 glass-header shadow-sm flex items-center justify-between px-6 h-16">
        <div className="flex items-center gap-3">
          <span className="text-2xl font-bold tracking-tighter text-primary font-headline">
            DigestAnything
          </span>
        </div>
      </header>

      {/* Main Content */}
      <main className="pt-24 pb-12 px-4 sm:px-8 min-h-screen">
        <div className="max-w-4xl mx-auto">
          {/* Hero + Input */}
          {!data && !loading && (
            <div className="text-center mb-12 pt-12">
              <h1 className="text-5xl font-headline font-extrabold text-on-surface tracking-tight mb-3" style={{ letterSpacing: "-0.02em" }}>
                Any source. Understood.
              </h1>
              <p className="text-lg text-on-surface-variant font-body mb-10">
                Paste any URL, YouTube link, or upload a PDF — get 5 AI-powered learning tools instantly.
              </p>
            </div>
          )}

          {/* Sample sources */}
          {!data && !loading && (
            <div className="flex flex-wrap justify-center gap-2 mb-8">
              {[
                { label: "Agentic Design Patterns", sub: "Anthropic Engineering Blog", icon: "article", url: "https://www.anthropic.com/engineering/harness-design-long-running-apps" },
                { label: "Andrej Karpathy on LLMs", sub: "YouTube Talk", icon: "play_circle", url: "https://www.youtube.com/watch?v=zjkBMFhNj_g" },
                { label: "Transformer Architecture", sub: "Wikipedia", icon: "public", url: "https://en.wikipedia.org/wiki/Transformer_(deep_learning_architecture)" },
              ].map((s) => (
                <button
                  key={s.label}
                  onClick={() => handleSubmit(s.url)}
                  className="flex items-center gap-3 px-5 py-3 bg-surface-container-lowest rounded-xl text-left font-body hover:bg-primary-fixed/30 transition-all card-shadow"
                  data-preset={s.label.toLowerCase()}
                >
                  <span className="material-symbols-outlined text-xl text-primary">{s.icon}</span>
                  <div>
                    <p className="text-sm font-headline font-semibold text-on-surface">{s.label}</p>
                    <p className="text-xs text-on-surface-variant">{s.sub}</p>
                  </div>
                </button>
              ))}
            </div>
          )}

          <div className="mb-8">
            <SourceInput onSubmit={handleSubmit} onFileUpload={handleFileUpload} loading={loading} />
          </div>

          {/* Features */}
          {!data && !loading && (
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-12">
              {[
                { icon: "description", title: "Overview", desc: "Summary + mind map" },
                { icon: "quiz", title: "Quiz", desc: "10 adaptive MCQs" },
                { icon: "style", title: "Flashcards", desc: "Spaced repetition" },
                { icon: "podcasts", title: "Podcast", desc: "AI-generated audio" },
                { icon: "psychology", title: "Tutor", desc: "Feynman technique" },
              ].map((f) => (
                <div key={f.title} className="bg-surface-container-lowest rounded-xl p-4 card-shadow text-center">
                  <span className="material-symbols-outlined text-primary text-2xl mb-2 block">{f.icon}</span>
                  <p className="font-headline font-bold text-sm text-on-surface">{f.title}</p>
                  <p className="text-xs text-on-surface-variant font-body mt-0.5">{f.desc}</p>
                </div>
              ))}
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="bg-error-container rounded-xl p-4 text-error text-center font-body mb-8" data-component="error">
              {error}
            </div>
          )}

          {/* Loading */}
          {loading && (
            <LoadingState message="Analyzing content with Gemini... this takes 30-60 seconds" />
          )}

          {/* Results */}
          {data && (
            <div className="space-y-6">
              <TabBar activeTab={activeTab} onTabChange={setActiveTab} readyTabs={readyTabs} />

              <div className="mt-6">
                {activeTab === "overview" && data.context && (
                  <Overview context={data.context} markmap={data.markmap || ""} />
                )}
                {activeTab === "quiz" && (
                  readyTabs.has("quiz") && data.quiz ? (
                    <QuizMode quiz={data.quiz} />
                  ) : (
                    <LoadingState message="Generating quiz questions..." />
                  )
                )}
                {activeTab === "cards" && (
                  readyTabs.has("cards") && data.cards ? (
                    <FlashCards cards={data.cards} />
                  ) : (
                    <LoadingState message="Creating flashcards..." />
                  )
                )}
                {activeTab === "podcast" && (
                  readyTabs.has("podcast") && data.podcast ? (
                    <PodcastPlayer podcast={data.podcast} />
                  ) : (
                    <LoadingState message="Generating podcast... this takes 2-3 minutes" />
                  )
                )}
                {activeTab === "tutor" && data.context && (
                  <TutorTab
                    sessionId={data.context.session_id || "default"}
                    concepts={data.context.key_concepts || []}
                  />
                )}
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Floating Chat */}
      {data && (
        <FloatingChat sessionId={data.context?.session_id || "default"} />
      )}
    </div>
  );
}
