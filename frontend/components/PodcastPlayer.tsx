"use client";

import { useState, useRef } from "react";

interface ScriptLine {
  speaker: string;
  text: string;
  segment: number;
}

interface PodcastPlayerProps {
  podcast: {
    script: ScriptLine[];
    audio_url: string;
  };
}

export default function PodcastPlayer({ podcast }: PodcastPlayerProps) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [playing, setPlaying] = useState(false);
  const [showTranscript, setShowTranscript] = useState(false);

  const togglePlay = () => {
    if (!audioRef.current) return;
    if (playing) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
    setPlaying(!playing);
  };

  const speakerName = (s: string) => (s === "A" ? "Alex" : "Sam");
  const speakerColor = (s: string) => (s === "A" ? "text-primary" : "text-tertiary");

  return (
    <div className="space-y-6" data-component="podcast">
      {/* Player Card */}
      <div className="bg-surface-container-lowest rounded-xl p-8 card-shadow">
        <div className="flex items-center gap-6">
          {/* Play button */}
          <button
            onClick={togglePlay}
            className="w-16 h-16 rounded-full bg-gradient-to-br from-primary to-primary-container text-white flex items-center justify-center shadow-lg hover:shadow-xl transition-shadow flex-shrink-0"
            data-action="play-pause"
          >
            <span className="material-symbols-outlined text-3xl" style={{ fontVariationSettings: "'FILL' 1" }}>
              {playing ? "pause" : "play_arrow"}
            </span>
          </button>

          <div className="flex-1">
            <h2 className="text-xl font-headline font-bold text-on-surface mb-1">AI Podcast</h2>
            <p className="text-sm text-on-surface-variant font-body">
              {podcast.script.length} turns across {new Set(podcast.script.map((l) => l.segment)).size} segments
            </p>
            <audio
              ref={audioRef}
              src={`http://localhost:8000${podcast.audio_url}`}
              onEnded={() => setPlaying(false)}
              controls
              className="w-full mt-3"
              data-element="audio-player"
            />
          </div>
        </div>
      </div>

      {/* Transcript Toggle */}
      <button
        onClick={() => setShowTranscript(!showTranscript)}
        className="flex items-center gap-2 text-sm font-headline font-semibold text-primary hover:text-primary-container transition-colors"
        data-action="toggle-transcript"
      >
        <span className="material-symbols-outlined text-lg">
          {showTranscript ? "expand_less" : "expand_more"}
        </span>
        {showTranscript ? "Hide Transcript" : "Show Transcript"}
      </button>

      {/* Transcript */}
      {showTranscript && (
        <div className="bg-surface-container-lowest rounded-xl p-6 card-shadow space-y-3 max-h-[500px] overflow-y-auto" data-component="transcript">
          {podcast.script.map((line, i) => (
            <div key={i} className="flex gap-3" data-turn={i}>
              <span className={`font-headline font-bold text-sm flex-shrink-0 w-12 ${speakerColor(line.speaker)}`}>
                {speakerName(line.speaker)}
              </span>
              <p className="font-body text-sm text-on-surface">{line.text}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
