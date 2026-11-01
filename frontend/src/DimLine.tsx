import { type ReactNode } from "react";

// A dimension line (Maßlinie): the app's signature for "this figure measures that span".
export function DimLine({ children }: { children?: ReactNode }) {
  return (
    <div className="dim">
      <i className="dim-tick" aria-hidden="true" />
      <i className="dim-line" aria-hidden="true" />
      {children && <span className="dim-label">{children}</span>}
      {children && <i className="dim-line" aria-hidden="true" />}
      <i className="dim-tick" aria-hidden="true" />
    </div>
  );
}
