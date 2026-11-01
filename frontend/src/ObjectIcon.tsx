// Three small line drawings instead of an icon set: Wohnung (block with a window grid),
// Haus (gable house), Grundstück (plot boundary with a survey point). Same stroke as the
// rest of the sheet; the red is reserved for the one thing that identifies the type.

export function ObjectIcon({ type, size = 56 }: { type: string; size?: number }) {
  return (
    <svg className="object-icon" width={size} height={size} viewBox="0 0 56 56" aria-hidden="true">
      {type === "haus" ? (
        <>
          <path className="oi-ink" d="M10 50V26h36v24M5 50h46" />
          <path className="oi-red" d="M7 28L28 9l21 19" />
          <path className="oi-ink" d="M24 50V37h8v13M14 31h6v6h-6zM36 31h6v6h-6z" />
        </>
      ) : type === "grundstueck" ? (
        <>
          <path className="oi-ink oi-dash" d="M8 14l30-6 12 14-8 26-34-4z" />
          <path className="oi-red" d="M24 22h12v11H24zM22 24l8-6 8 6" />
          <circle className="oi-dot" cx="8" cy="14" r="2.5" />
          <circle className="oi-dot" cx="38" cy="8" r="2.5" />
          <circle className="oi-dot" cx="50" cy="22" r="2.5" />
          <circle className="oi-dot" cx="42" cy="48" r="2.5" />
          <circle className="oi-dot" cx="8" cy="44" r="2.5" />
        </>
      ) : (
        <>
          <path className="oi-ink" d="M14 50V8h28v42M7 50h42" />
          <path
            className="oi-red"
            d="M20 15h6v6h-6zM30 15h6v6h-6zM20 27h6v6h-6zM30 27h6v6h-6z"
          />
          <path className="oi-ink" d="M25 50V41h6v9" />
        </>
      )}
    </svg>
  );
}
