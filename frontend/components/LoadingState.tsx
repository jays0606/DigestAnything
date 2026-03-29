"use client";

export default function LoadingState({ message = "Generating..." }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 gap-4" data-component="loading">
      <div className="w-12 h-12 rounded-full bg-primary-fixed flex items-center justify-center">
        <span className="material-symbols-outlined animate-spin text-primary text-2xl">progress_activity</span>
      </div>
      <p className="text-on-surface-variant font-label text-sm">{message}</p>
    </div>
  );
}
