import { type RefObject, useEffect, useState } from "react";

// Measured width of an element, so SVG charts can be drawn at pixel size instead of being
// stretched (stretching would distort the text). `fallback` is used before the first
// measurement and where ResizeObserver does not exist (jsdom).
export function useWidth(ref: RefObject<HTMLElement>, fallback = 640): number {
  const [width, setWidth] = useState(fallback);
  useEffect(() => {
    const el = ref.current;
    if (!el || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(([entry]) => {
      const w = Math.floor(entry.contentRect.width);
      if (w > 0) setWidth(w);
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, [ref]);
  return width;
}
