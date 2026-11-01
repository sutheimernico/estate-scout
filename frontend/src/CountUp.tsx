import { useCountUp } from "./motion";

// A number that ticks up to its value. `format` is the same de-DE formatter the static
// display would use, so the final frame is identical to the non-animated rendering.
export function CountUp({
  value,
  format,
  duration,
}: {
  value: number;
  format: (n: number) => string;
  duration?: number;
}) {
  const shown = useCountUp(value, duration);
  return <>{format(shown)}</>;
}
