import { type ReactNode, useEffect, useRef } from "react";

// A drawer: slides in from the right, becomes a bottom sheet on narrow screens (CSS).
// Escape and the scrim close it; focus moves into it on open and back on close.
export function Sheet({
  title,
  onClose,
  children,
}: {
  title: string;
  onClose: () => void;
  children: ReactNode;
}) {
  const ref = useRef<HTMLDivElement>(null);
  // the parent passes a fresh closure every render; a ref keeps the effect (and the focus
  // move) from re-running while the user types inside the sheet
  const close = useRef(onClose);
  close.current = onClose;
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    ref.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") close.current();
    };
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("keydown", onKey);
      previous?.focus?.();
    };
  }, []);
  return (
    <div className="sheet-layer">
      <div className="scrim" onClick={onClose} aria-hidden="true" />
      <div className="drawer" role="dialog" aria-modal="true" aria-label={title} tabIndex={-1} ref={ref}>
        <header className="drawer-head">
          <h3>{title}</h3>
          <button type="button" className="btn ghost sm" onClick={onClose}>
            Schließen
          </button>
        </header>
        <div className="drawer-body">{children}</div>
      </div>
    </div>
  );
}
