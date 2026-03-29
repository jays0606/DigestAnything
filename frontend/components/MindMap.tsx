"use client";

import { useEffect, useRef, useState } from "react";

interface MindMapProps {
  markdown: string;
}

export default function MindMap({ markdown }: MindMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState(false);

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

        // Create SVG with explicit dimensions to avoid SVGLength error
        const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        svg.setAttribute("width", "100%");
        svg.setAttribute("height", "400");
        svg.style.width = "100%";
        svg.style.height = "400px";

        containerRef.current.innerHTML = "";
        containerRef.current.appendChild(svg);

        // Small delay to ensure SVG is in DOM and has dimensions
        requestAnimationFrame(() => {
          if (cancelled) return;
          try {
            Markmap.create(svg, { autoFit: true, duration: 500, maxWidth: 300 }, root);
          } catch {
            setError(true);
          }
        });
      } catch {
        setError(true);
      }
    }

    render();
    return () => { cancelled = true; };
  }, [markdown]);

  if (error) {
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
