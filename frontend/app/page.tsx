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

      // Step 2: Get markmap immediately (fast)
      const visualRes = await fetch(`${API}/api/visual`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(context),
      });
      const visual = await visualRes.json();

      // Show overview immediately
      const initial: DigestData = {
        context,
        markmap: visual.markdown || null,
        quiz: null,
        cards: null,
        podcast: null,
      };
      setData(initial);
      setLoading(false);
      setReadyTabs(new Set(["overview", "tutor"]));

      // Step 3: Fire quiz, cards, podcast in parallel
      const [quizRes, cardsRes, podcastRes] = await Promise.allSettled([
        fetch(`${API}/api/quiz`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(context),
        }).then(r => r.json()),
        fetch(`${API}/api/cards`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(context),
        }).then(r => r.json()),
        fetch(`${API}/api/podcast`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(context),
        }).then(r => r.json()),
      ]);

      setData(prev => {
        if (!prev) return prev;
        return {
          ...prev,
          quiz: quizRes.status === "fulfilled" ? quizRes.value : null,
          cards: cardsRes.status === "fulfilled" ? cardsRes.value : null,
          podcast: podcastRes.status === "fulfilled" ? podcastRes.value : null,
        };
      });

      setReadyTabs(prev => {
        const next = new Set(prev);
        if (quizRes.status === "fulfilled") next.add("quiz");
        if (cardsRes.status === "fulfilled") next.add("cards");
        if (podcastRes.status === "fulfilled") next.add("podcast");
        return next;
      });

    } catch (err: any) {
      setError(err.message || "Something went wrong");
      setLoading(false);
    }
  }, []);

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
              <h1 className="text-5xl font-headline font-extrabold text-on-surface tracking-tight mb-4" style={{ letterSpacing: "-0.02em" }}>
                Any source. Understood.
              </h1>
              <p className="text-lg text-on-surface-variant font-body mb-10">
                Paste any URL, YouTube link, or text — get AI-powered learning tabs in seconds.
              </p>
            </div>
          )}

          <div className="mb-8">
            <SourceInput onSubmit={handleSubmit} loading={loading} />
          </div>

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
