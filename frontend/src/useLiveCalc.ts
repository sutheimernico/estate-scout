// Recalculates a calculator while the user types: debounced, stale answers are ignored, and the
// previous result stays on screen (marked `loading`) until the next one arrives, so the figure
// ticks from old to new instead of flashing empty.

import { useEffect, useRef, useState } from "react";

import { ApiError, finance, type KnownCalc, toKnownCalc } from "./api";
import { type BuiltArgs, type CalcSpec } from "./calcSpecs";

export interface LiveState {
  calc: KnownCalc | null;
  args: Record<string, unknown> | null; // the arguments `calc` was computed from
  loading: boolean;
  error: string | null;
}

export const DEBOUNCE_MS = 350;

export function useLiveCalc(spec: CalcSpec, built: BuiltArgs): LiveState {
  const [state, setState] = useState<LiveState>({ calc: null, args: null, loading: false, error: null });
  const lastCalc = useRef<string | null>(null);
  // A new argument object every render would re-run the effect; the JSON key is the identity.
  const key = built.ok ? JSON.stringify(built.args) : null;

  useEffect(() => {
    if (!built.ok || key === null) {
      // An unusable input must not leave the previous figures standing as if they still applied.
      setState((s) => ({ ...s, calc: null, args: null, loading: false, error: null }));
      return;
    }
    const args = built.args;
    const ctrl = new AbortController();
    // switching calculators computes at once; typing within one calculator waits for a pause
    const delay = lastCalc.current === spec.calc ? DEBOUNCE_MS : 0;
    lastCalc.current = spec.calc;
    setState((s) => ({ ...s, loading: true, error: null }));
    const timer = setTimeout(() => {
      finance(spec.calc, args, ctrl.signal)
        .then((resp) =>
          setState({ calc: toKnownCalc(spec.calc, resp.result), args, loading: false, error: null }),
        )
        .catch((err: unknown) => {
          if (err instanceof DOMException && err.name === "AbortError") return;
          setState((s) => ({
            ...s,
            loading: false,
            error: err instanceof ApiError || err instanceof Error ? err.message : String(err),
          }));
        });
    }, delay);
    return () => {
      clearTimeout(timer);
      ctrl.abort();
    };
    // `built` is represented by `key`; spec.calc picks the endpoint
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, spec.calc]);

  return state;
}
