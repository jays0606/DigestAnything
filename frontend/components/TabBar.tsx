"use client";

interface Tab {
  id: string;
  label: string;
  icon: string;
}

const TABS: Tab[] = [
  { id: "overview", label: "Overview", icon: "description" },
  { id: "quiz", label: "Quiz", icon: "quiz" },
  { id: "cards", label: "Flashcards", icon: "style" },
  { id: "podcast", label: "Podcast", icon: "podcasts" },
  { id: "tutor", label: "Tutor", icon: "psychology" },
];

interface TabBarProps {
  activeTab: string;
  onTabChange: (tabId: string) => void;
  readyTabs: Set<string>;
}

export default function TabBar({ activeTab, onTabChange, readyTabs }: TabBarProps) {
  return (
    <div className="flex gap-1 bg-surface-container-low rounded-xl p-1" data-component="tab-bar">
      {TABS.map((tab) => {
        const isActive = activeTab === tab.id;
        const isReady = readyTabs.has(tab.id);
        return (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-lg font-headline font-semibold text-sm transition-all ${
              isActive
                ? "bg-surface-container-lowest text-primary card-shadow"
                : "text-on-surface-variant hover:text-on-surface"
            }`}
            data-tab={tab.id}
            data-ready={isReady}
          >
            <span className="material-symbols-outlined text-lg" style={isActive ? { fontVariationSettings: "'FILL' 1" } : {}}>
              {tab.icon}
            </span>
            {tab.label}
            {!isReady && tab.id !== "overview" && (
              <span className="material-symbols-outlined animate-spin text-xs text-on-surface-variant">progress_activity</span>
            )}
          </button>
        );
      })}
    </div>
  );
}
