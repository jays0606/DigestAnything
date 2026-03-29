"use client";

import { useState, useRef, useEffect } from "react";

interface SourceInputProps {
  onSubmit: (source: string) => void;
  onFileUpload: (file: File) => void;
  loading: boolean;
  prefill?: string;
}

export default function SourceInput({ onSubmit, onFileUpload, loading, prefill }: SourceInputProps) {
  const [source, setSource] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (prefill) setSource(prefill);
  }, [prefill]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (source.trim() && !loading) {
      onSubmit(source.trim());
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && !loading) {
      onFileUpload(file);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-2xl mx-auto" data-component="source-input">
      <div className="relative flex gap-2">
        <div className="relative flex-1">
          <input
            type="text"
            value={source}
            onChange={(e) => setSource(e.target.value)}
            placeholder="Paste any URL, YouTube link, or text..."
            className="w-full px-6 py-4 bg-surface-container-high rounded-xl text-on-surface font-body text-base focus:outline-none focus:ring-2 focus:ring-primary placeholder:text-on-surface-variant pr-28"
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
        <button
          type="button"
          onClick={() => fileRef.current?.click()}
          disabled={loading}
          className="flex-shrink-0 w-12 h-14 flex items-center justify-center bg-surface-container-high rounded-xl text-on-surface-variant hover:text-primary transition-colors disabled:opacity-50"
          title="Upload PDF or file"
          data-action="upload-file"
        >
          <span className="material-symbols-outlined text-xl">upload_file</span>
        </button>
        <input
          ref={fileRef}
          type="file"
          accept=".pdf,.txt,.md,.html,.csv"
          onChange={handleFileChange}
          className="hidden"
          data-input="file-upload"
        />
      </div>
    </form>
  );
}
