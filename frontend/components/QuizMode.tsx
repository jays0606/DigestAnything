"use client";

import { useState } from "react";

interface Question {
  id: number;
  difficulty: string;
  question: string;
  options: string[];
  correct: number;
  explanation: string;
}

interface QuizModeProps {
  quiz: { questions: Question[] };
}

export default function QuizMode({ quiz }: QuizModeProps) {
  const [current, setCurrent] = useState(0);
  const [selected, setSelected] = useState<number | null>(null);
  const [showExplanation, setShowExplanation] = useState(false);
  const [score, setScore] = useState(0);
  const [completed, setCompleted] = useState(false);

  const questions = quiz.questions;
  const q = questions[current];

  const handleSelect = (idx: number) => {
    if (selected !== null) return;
    setSelected(idx);
    setShowExplanation(true);
    if (idx === q.correct) {
      setScore((s) => s + 1);
    }
  };

  const handleNext = () => {
    if (current + 1 >= questions.length) {
      setCompleted(true);
      return;
    }
    setCurrent((c) => c + 1);
    setSelected(null);
    setShowExplanation(false);
  };

  const handleRestart = () => {
    setCurrent(0);
    setSelected(null);
    setShowExplanation(false);
    setScore(0);
    setCompleted(false);
  };

  if (completed) {
    return (
      <div className="bg-surface-container-lowest rounded-xl p-8 card-shadow text-center" data-component="quiz-complete">
        <h2 className="text-2xl font-headline font-bold text-on-surface mb-4">Quiz Complete!</h2>
        <p className="text-4xl font-headline font-extrabold text-primary mb-2">{score}/{questions.length}</p>
        <p className="text-on-surface-variant font-body mb-6">
          {score >= 8 ? "Excellent! You've mastered this content." : score >= 5 ? "Good job! Review the concepts you missed." : "Keep studying! Try again after reviewing."}
        </p>
        <button onClick={handleRestart} className="px-6 py-3 bg-gradient-to-br from-primary to-primary-container text-white rounded-full font-headline font-bold" data-action="restart-quiz">
          Try Again
        </button>
      </div>
    );
  }

  const difficultyColor = {
    easy: "text-secondary",
    medium: "text-primary",
    hard: "text-error",
    expert: "text-error",
  }[q.difficulty] || "text-primary";

  return (
    <div className="space-y-6" data-component="quiz">
      {/* Progress */}
      <div className="flex items-center justify-between">
        <span className={`text-xs font-bold uppercase tracking-widest font-label ${difficultyColor}`}>{q.difficulty}</span>
        <span className="text-sm text-on-surface-variant font-label">
          Question {current + 1} of {questions.length}
        </span>
      </div>
      <div className="w-full h-1.5 bg-surface-container-high rounded-full overflow-hidden">
        <div className="h-full bg-secondary rounded-full transition-all" style={{ width: `${((current + 1) / questions.length) * 100}%` }} />
      </div>

      {/* Question */}
      <div className="bg-surface-container-lowest rounded-xl p-8 card-shadow">
        <h2 className="text-xl font-headline font-bold text-on-surface mb-6" data-field="question">{q.question}</h2>
        <div className="space-y-3">
          {q.options.map((opt, idx) => {
            let bg = "bg-surface-container-low hover:bg-surface-container-high";
            if (selected !== null) {
              if (idx === q.correct) bg = "bg-secondary-container";
              else if (idx === selected) bg = "bg-error-container";
            }
            return (
              <button
                key={idx}
                onClick={() => handleSelect(idx)}
                className={`w-full text-left p-4 rounded-xl font-body transition-all ${bg}`}
                disabled={selected !== null}
                data-option={idx}
                data-correct={idx === q.correct}
              >
                <span className="font-headline font-bold mr-3">{String.fromCharCode(65 + idx)}.</span>
                {opt}
              </button>
            );
          })}
        </div>
      </div>

      {/* Explanation */}
      {showExplanation && (
        <div className="bg-primary-fixed/30 rounded-xl p-6" data-component="explanation">
          <p className="font-body text-on-surface">{q.explanation}</p>
          <button
            onClick={handleNext}
            className="mt-4 px-6 py-2.5 bg-gradient-to-br from-primary to-primary-container text-white rounded-full font-headline font-bold text-sm"
            data-action="next-question"
          >
            {current + 1 >= questions.length ? "See Results" : "Next Question"}
          </button>
        </div>
      )}
    </div>
  );
}
