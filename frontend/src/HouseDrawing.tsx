// The hero drawing: a house in elevation with the purchase dimensioned the way a drawing sheet
// would do it (equity | loan along the footing), next to the Restschuld curve with its
// Zinsbindung marked. Illustration only: it carries no numbers. Strokes draw themselves in.

const D = (i: number) => ({ ["--d" as string]: `${i * 90}ms` });

function Tick({ x, y }: { x: number; y: number }) {
  return <path className="hd-ink" d={`M${x - 5} ${y + 5}L${x + 5} ${y - 5}`} pathLength={1} />;
}

export function HouseDrawing() {
  return (
    <svg className="house-drawing" viewBox="0 0 580 330" role="img" aria-label="Zeichnung: Haus mit bemaßter Finanzierung und Restschuldkurve">
      {/* ground */}
      <path className="hd-ink hd-ground" d="M20 250H540" pathLength={1} style={D(0)} />

      {/* house */}
      <g className="hd-house">
        <path className="hd-ink" d="M70 250V142H330V250" pathLength={1} style={D(1)} />
        <path className="hd-red" d="M52 146L200 70L348 146" pathLength={1} style={D(2)} />
        <path className="hd-red" d="M282 108V84H304V120" pathLength={1} style={D(3)} />
        <path className="hd-ink" d="M178 250V194H222V250" pathLength={1} style={D(3)} />
        <path className="hd-ink" d="M98 164H142V206H98ZM120 164V206M98 185H142" pathLength={1} style={D(4)} />
        <path className="hd-ink" d="M258 164H302V206H258ZM280 164V206M258 185H302" pathLength={1} style={D(4)} />
        <circle className="hd-dot" cx="200" cy="108" r="6" />
      </g>

      {/* dimension chain under the footing */}
      <g className="hd-dim">
        <path className="hd-ink" d="M70 280H330M70 270V290M122 270V290M330 270V290" pathLength={1} style={D(5)} />
        <Tick x={70} y={280} />
        <Tick x={122} y={280} />
        <Tick x={330} y={280} />
        <text x="96" y="306" textAnchor="middle">Eigenkapital</text>
        <text x="226" y="306" textAnchor="middle">Darlehen</text>
      </g>

      {/* Restschuld section */}
      <g className="hd-section">
        <path className="hd-rule" d="M392 70V250H520" pathLength={1} style={D(2)} />
        <path className="hd-curve" d="M394 96C432 98 470 142 518 246" pathLength={1} style={D(5)} />
        <path className="hd-red" d="M452 78V250M446 84L458 72M446 256L458 244" pathLength={1} style={D(6)} />
        <circle className="hd-dot" cx="452" cy="132" r="4.5" style={D(7)} />
        <text x="466" y="124">Restschuld</text>
        <text x="442" y="232" textAnchor="end" className="hd-red-text">Zinsbindung</text>
        <text x="392" y="56">Tilgungsverlauf</text>
      </g>
    </svg>
  );
}
