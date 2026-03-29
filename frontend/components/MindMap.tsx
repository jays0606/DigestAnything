"use client";

import { useEffect, useRef } from "react";

interface MindMapProps {
  markdown: string;
}

export default function MindMap({ markdown }: MindMapProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const mmRef = useRef<any>(null);

  useEffect(() => {
    if (!markdown || !svgRef.current) return;

    let cancelled = false;

    async function render() {
      const { Transformer } = await import("markmap-lib");
      const { Markmap } = await import("markmap-view");

      if (cancelled || !svgRef.current) return;

      const transformer = new Transformer();
      const { root } = transformer.transform(markdown);

      // Clear previous
      svgRef.current.innerHTML = "";

      mmRef.current = Markmap.create(svgRef.current, {
        autoFit: true,
        duration: 500,
        maxWidth: 300,
      }, root);
    }

    render();

    return () => {
      cancelled = true;
    };
  }, [markdown]);

  return (
    <div className="w-full bg-surface-container-lowest rounded-xl card-shadow overflow-hidden" data-component="mindmap">
      <svg ref={svgRef} className="w-full" style={{ height: "400px" }} />
    </div>
  );
}
