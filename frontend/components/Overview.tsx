"use client";

import MindMap from "./MindMap";

interface Concept {
  term: string;
  definition: string;
  importance: string;
}

interface Analogy {
  concept: string;
  analogy: string;
  explanation: string;
}

interface OverviewProps {
  context: {
    title: string;
    subtitle: string;
    summary: string;
    difficulty: string;
    estimated_read_time_minutes: number;
    key_concepts: Concept[];
    key_insights: string[];
    analogies: Analogy[];
  };
  markmap: string;
}

export default function Overview({ context, markmap }: OverviewProps) {
  const difficultyColor = {
    beginner: "text-secondary",
    intermediate: "text-primary",
    advanced: "text-error",
  }[context.difficulty] || "text-primary";

  return (
    <div className="space-y-8" data-component="overview">
      {/* Title Card */}
      <div className="bg-surface-container-lowest rounded-xl p-8 card-shadow">
        <div className="flex items-center gap-3 mb-4">
          <span className={`text-xs font-bold uppercase tracking-widest font-label ${difficultyColor}`}>
            {context.difficulty}
          </span>
          <span className="text-xs text-on-surface-variant font-label">
            {context.estimated_read_time_minutes} min read
          </span>
        </div>
        <h1 className="text-3xl font-headline font-extrabold text-on-surface tracking-tight mb-2" data-field="title">
          {context.title}
        </h1>
        <p className="text-lg text-on-surface-variant font-body mb-6" data-field="subtitle">
          {context.subtitle}
        </p>
        <p className="text-base text-on-surface font-body leading-relaxed" data-field="summary">
          {context.summary}
        </p>
      </div>

      {/* Mind Map */}
      {markmap && (
        <div>
          <h2 className="text-xl font-headline font-bold text-on-surface mb-4 tracking-tight">
            Knowledge Map
          </h2>
          <MindMap markdown={markmap} />
        </div>
      )}

      {/* Key Concepts */}
      <div>
        <h2 className="text-xl font-headline font-bold text-on-surface mb-4 tracking-tight">
          Key Concepts
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {context.key_concepts.map((c, i) => (
            <div key={i} className="bg-surface-container-lowest rounded-xl p-5 card-shadow" data-concept={c.term}>
              <div className="flex items-center gap-2 mb-2">
                <span className={`text-xs font-bold uppercase tracking-wider font-label ${c.importance === "high" ? "text-primary" : "text-on-surface-variant"}`}>
                  {c.importance}
                </span>
              </div>
              <h3 className="font-headline font-bold text-on-surface mb-1">{c.term}</h3>
              <p className="text-sm text-on-surface-variant font-body">{c.definition}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Key Insights */}
      <div>
        <h2 className="text-xl font-headline font-bold text-on-surface mb-4 tracking-tight">
          Key Insights
        </h2>
        <div className="space-y-3">
          {context.key_insights.map((insight, i) => (
            <div key={i} className="bg-surface-container-lowest rounded-xl p-5 card-shadow flex gap-4" data-insight={i}>
              <span className="text-primary font-headline font-bold text-lg">{i + 1}</span>
              <p className="text-on-surface font-body">{insight}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Analogies */}
      {context.analogies.length > 0 && (
        <div>
          <h2 className="text-xl font-headline font-bold text-on-surface mb-4 tracking-tight">
            Analogies
          </h2>
          <div className="space-y-3">
            {context.analogies.map((a, i) => (
              <div key={i} className="bg-primary-fixed/30 rounded-xl p-5" data-analogy={i}>
                <p className="font-headline font-bold text-on-surface mb-1">
                  {a.concept} is like {a.analogy}
                </p>
                <p className="text-sm text-on-surface-variant font-body">{a.explanation}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
