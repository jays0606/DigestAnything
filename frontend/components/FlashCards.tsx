"use client";

import { useState } from "react";

interface Card {
  front: string;
  back: string;
  type: string;
}

interface FlashCardsProps {
  cards: { cards: Card[] };
}

export default function FlashCards({ cards }: FlashCardsProps) {
  const [current, setCurrent] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [known, setKnown] = useState<Set<number>>(new Set());

  const allCards = cards.cards;
  const remaining = allCards.filter((_, i) => !known.has(i));
  const card = allCards[current];

  if (remaining.length === 0) {
    return (
      <div className="bg-surface-container-lowest rounded-xl p-8 card-shadow text-center" data-component="cards-complete">
        <h2 className="text-2xl font-headline font-bold text-on-surface mb-4">All Cards Reviewed!</h2>
        <p className="text-on-surface-variant font-body mb-6">You mastered all {allCards.length} flashcards.</p>
        <button
          onClick={() => { setKnown(new Set()); setCurrent(0); setFlipped(false); }}
          className="px-6 py-3 bg-gradient-to-br from-primary to-primary-container text-white rounded-full font-headline font-bold"
          data-action="restart-cards"
        >
          Start Over
        </button>
      </div>
    );
  }

  const handleFlip = () => setFlipped(!flipped);

  const handleGotIt = () => {
    setKnown((prev) => new Set([...prev, current]));
    goNext();
  };

  const handleReviewAgain = () => {
    goNext();
  };

  const goNext = () => {
    setFlipped(false);
    let next = (current + 1) % allCards.length;
    while (known.has(next) && !known.has(current)) {
      next = (next + 1) % allCards.length;
    }
    setCurrent(next);
  };

  const typeColor = {
    definition: "text-primary",
    comparison: "text-tertiary",
    application: "text-secondary",
  }[card.type] || "text-primary";

  return (
    <div className="flex flex-col items-center" data-component="flashcards">
      {/* Counter */}
      <div className="mb-6 flex items-center gap-2 px-4 py-1.5 bg-surface-container-low rounded-full">
        <span className="material-symbols-outlined text-primary text-sm">layers</span>
        <span className="text-sm font-bold font-label text-on-surface-variant">
          Cards Left: <span className="text-on-surface">{remaining.length}</span>
        </span>
      </div>

      {/* Card */}
      <div
        className="w-full max-w-2xl aspect-[1.6/1] cursor-pointer"
        onClick={handleFlip}
        data-action="flip-card"
        data-flipped={flipped}
      >
        <div className="w-full h-full bg-surface-container-lowest rounded-xl card-shadow flex flex-col items-center justify-center p-12 transition-all">
          <span className={`text-xs font-bold uppercase tracking-widest font-label mb-6 ${typeColor}`}>
            {card.type}
          </span>
          {!flipped ? (
            <>
              <h2 className="text-3xl font-headline font-extrabold text-on-surface text-center mb-6" data-field="front">
                {card.front}
              </h2>
              <button className="flex items-center gap-2 px-6 py-2.5 bg-surface-container-high hover:bg-surface-container text-primary font-bold rounded-full transition-all text-sm">
                <span className="material-symbols-outlined text-lg">sync</span>
                Flip Card
              </button>
            </>
          ) : (
            <p className="text-base font-body text-on-surface text-center leading-relaxed" data-field="back">
              {card.back}
            </p>
          )}
        </div>
      </div>

      {/* Actions */}
      {flipped && (
        <div className="mt-8 flex items-center gap-4 w-full max-w-2xl">
          <button
            onClick={handleReviewAgain}
            className="flex-1 flex items-center justify-center gap-3 py-4 rounded-xl bg-surface-container-low hover:bg-error-container transition-all"
            data-action="review-again"
          >
            <span className="material-symbols-outlined text-error">history</span>
            <span className="font-bold text-on-surface text-sm">Review Again</span>
          </button>
          <button
            onClick={handleGotIt}
            className="flex-1 flex items-center justify-center gap-3 py-4 rounded-xl bg-secondary text-white hover:shadow-lg transition-all"
            data-action="got-it"
          >
            <span className="material-symbols-outlined">check_circle</span>
            <span className="font-bold text-sm">Got It</span>
          </button>
        </div>
      )}
    </div>
  );
}
