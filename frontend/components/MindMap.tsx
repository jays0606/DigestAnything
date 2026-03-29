"use client";

import { useEffect, useRef, useState } from "react";

interface MindMapProps {
  markdown: string;
}

export default function MindMap({ markdown }: MindMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [fallback, setFallback] = useState(false);

  useEffect(() => {
    if (!markdown || !containerRef.current) return;

    let cancelled = false;

    async function render() {
      try {
        const { Transformer } = await import("markmap-lib");
        const { Markmap } = await import("markmap-view");

        if (cancelled || !containerRef.current) return;

        const transformer = new Transformer();
        const { root } = transformer.transform(markdown);

        // Create SVG with absolute pixel dimensions (avoids SVGLength error)
        containerRef.current.innerHTML = "";
        const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        svg.setAttribute("width", String(containerRef.current.clientWidth || 800));
        svg.setAttribute("height", "400");
        containerRef.current.appendChild(svg);

        // Suppress d3-zoom SVGLength errors
        const origError = window.onerror;
        window.onerror = (msg) => {
          if (typeof msg === "string" && msg.includes("SVGLength")) return true;
          return origError ? origError.call(window, msg) : false;
        };

        setTimeout(() => {
          if (cancelled || !svg.isConnected) return;
          try {
            Markmap.create(svg, { autoFit: true, duration: 0, maxWidth: 300 }, root);
          } catch { /* swallow d3 errors */ }
          window.onerror = origError;
        }, 100);
      } catch {
        setFallback(true);
      }
    }

    render();
    return () => { cancelled = true; };
  }, [markdown]);

  if (fallback) {
    return (
      <div className="w-full bg-surface-container-lowest rounded-xl card-shadow p-6" data-component="mindmap">
        <pre className="text-sm text-on-surface-variant whitespace-pre-wrap font-body">{markdown}</pre>
      </div>
    );
  }

  return (
    <div className="w-full bg-surface-container-lowest rounded-xl card-shadow overflow-hidden" data-component="mindmap">
      <div ref={containerRef} style={{ width: "100%", height: "400px" }} />
    </div>
  );
}
