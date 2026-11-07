// One decision point for "may we animate?" plus the count-up maths. CSS handles everything
// else; this file only exists for the things CSS cannot do (numbers that tick).

import { useEffect, useRef, useState } from "react";

// Environments without matchMedia (jsdom, very old browsers) get no animation: the final state
// renders immediately, which is also what tests want.
export function motionAllowed(): boolean {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") return false;
  return !window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export const easeOutCubic = (t: number) => 1 - Math.pow(1 - t, 3);

// Value of a count-up `elapsed` ms into a `duration` ms animation, clamped to [from, to].
export function countUpValue(from: number, to: number, elapsed: number, duration: number): number {
  if (duration <= 0 || elapsed >= duration) return to;
  if (elapsed <= 0) return from;
  return from + (to - from) * easeOutCubic(elapsed / duration);
}

// Returns the number to display right now; animates from the previously shown value to `target`.
export function useCountUp(target: number, duration = 400): number {
  const [value, setValue] = useState(() => (motionAllowed() ? 0 : target));
  const shown = useRef(value);
  shown.current = value;

  useEffect(() => {
    if (!motionAllowed()) {
      setValue(target);
      return;
    }
    const from = shown.current;
    const start = performance.now();
    let frame = 0;
    const tick = (now: number) => {
      setValue(countUpValue(from, target, now - start, duration));
      if (now - start < duration) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [target, duration]);

  return value;
}
