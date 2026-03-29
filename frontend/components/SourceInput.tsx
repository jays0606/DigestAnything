"use client";

import { useState } from "react";

interface SourceInputProps {
  onSubmit: (source: string) => void;
  loading: boolean;
}

export default function SourceInput({ onSubmit, loading }: SourceInputProps) {
  const [source, setSource] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (source.trim() && !loading) {
      onSubmit(source.trim());
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-2xl mx-auto" data-component="source-input">
      <div className="relative">
        <input
          type="text"
          value={source}
          onChange={(e) => setSource(e.target.value)}
          placeholder="Paste any URL, YouTube link, or text..."
          className="w-full px-6 py-4 bg-surface-container-high rounded-xl text-on-surface font-body text-base focus:outline-none focus:ring-2 focus:ring-primary placeholder:text-on-surface-variant"
          disabled={loading}
          data-input="source"
        />
        <button
          type="submit"
          disabled={loading || !source.trim()}
          className="absolute right-2 top-1/2 -translate-y-1/2 px-6 py-2 bg-gradient-to-br from-primary to-primary-container text-white rounded-full font-headline font-bold text-sm disabled:opacity-50 transition-opacity hover:opacity-90"
          data-action="submit"
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <span className="material-symbols-outlined animate-spin text-sm">progress_activity</span>
              Digesting...
            </span>
          ) : (
            "Digest"
          )}
        </button>
      </div>
    </form>
  );
}
