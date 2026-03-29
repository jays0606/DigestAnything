"use client";

import { useState, useCallback } from "react";
import SourceInput from "../components/SourceInput";
import TabBar from "../components/TabBar";
import Overview from "../components/Overview";
import LoadingState from "../components/LoadingState";

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
      const res = await fetch("/api/digest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source }),
      });

      if (!res.ok) {
        throw new Error(`API error: ${res.status}`);
      }

      const result = await res.json();
      setData(result);

      const ready = new Set<string>();
      ready.add("overview");
      if (result.quiz) ready.add("quiz");
      if (result.cards) ready.add("cards");
      if (result.podcast) ready.add("podcast");
      ready.add("tutor"); // tutor is always ready (it's a chat)
      setReadyTabs(ready);
    } catch (err: any) {
      setError(err.message || "Something went wrong");
    } finally {
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
          {data && !loading && (
            <div className="space-y-6">
              <TabBar activeTab={activeTab} onTabChange={setActiveTab} readyTabs={readyTabs} />

              <div className="mt-6">
                {activeTab === "overview" && data.context && (
                  <Overview context={data.context} markmap={data.markmap || ""} />
                )}
                {activeTab === "quiz" && (
                  readyTabs.has("quiz") ? (
                    <div data-component="quiz-placeholder" className="bg-surface-container-lowest rounded-xl p-8 card-shadow text-center text-on-surface-variant">
                      Quiz component — Round 2
                    </div>
                  ) : (
                    <LoadingState message="Generating quiz questions..." />
                  )
                )}
                {activeTab === "cards" && (
                  readyTabs.has("cards") ? (
                    <div data-component="cards-placeholder" className="bg-surface-container-lowest rounded-xl p-8 card-shadow text-center text-on-surface-variant">
                      Flashcards component — Round 2
                    </div>
                  ) : (
                    <LoadingState message="Creating flashcards..." />
                  )
                )}
                {activeTab === "podcast" && (
                  readyTabs.has("podcast") ? (
                    <div data-component="podcast-placeholder" className="bg-surface-container-lowest rounded-xl p-8 card-shadow text-center text-on-surface-variant">
                      Podcast player — Round 4
                    </div>
                  ) : (
                    <LoadingState message="Generating podcast..." />
                  )
                )}
                {activeTab === "tutor" && (
                  <div data-component="tutor-placeholder" className="bg-surface-container-lowest rounded-xl p-8 card-shadow text-center text-on-surface-variant">
                    Tutor — Round 3
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
