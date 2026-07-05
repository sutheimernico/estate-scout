# Finanzierungsmathematik

Konkrete Beträge berechnet immer der Finanzkern (`finance/annuity`, `finance/affordability`), nie das
Sprachmodell. Dieser Text erklärt die Konzepte.

## Annuitätendarlehen

**Monatsrate (deutsche Baufinanzierungspraxis):**
```
Monatsrate = Darlehen × (Sollzins_p.a. + Anfangstilgung_p.a.) / 12
```
Zins und Tilgung als Dezimal (z.B. 0,0332 und 0,02).

**Zins-Tilgungs-Mechanik:** Bei konstanter Annuität sinkt der Zinsanteil (auf die sinkende Restschuld)
und der Tilgungsanteil steigt um denselben Betrag — die Rate bleibt konstant.

**Exakte Restschuld nach n Monaten** (für die Anschlussfinanzierung), mit i_m = Sollzins_p.a./12 und
konstanter Rate A:
```
Restschuld(n) = Darlehen × (1+i_m)^n − A × ((1+i_m)^n − 1) / i_m
```

- **Sollzins ≠ Effektivzins:** der Effektivzins berücksichtigt unterjährige Zinseszinsen,
  Auszahlungskurs und Bereitstellungszinsen (Differenz meist 0,07–0,1 Prozentpunkte).
- **Anfängliche Tilgung:** marktüblich 1/2/3 % (bis 5 %); höhere Tilgung → deutlich kürzere Laufzeit.
  Rechner-Default oft 2 %.

**Aktuelle Zinsen nach Zinsbindung (Stand 2026-07-05, Topkonditionen, drklein.de, Basis 350.000 €):**
5 J. 3,45 %, 10 J. 3,32 %, 15 J. 3,59 %, 20 J. 3,79 %, 30 J. 4,07 % (Sollzins). Das sind beste Zinsen,
nicht der Durchschnitt — reale Angebote je nach Bonität/LTV 0,2–0,5 Punkte höher. Offizielle Referenz:
Bundesbank MFI-Zinsstatistik.

## Sondertilgung vs. Sonderkündigung — wichtige Unterscheidung

**§ 489 BGB gibt KEIN "5 %/Jahr"-Sondertilgungsrecht** (verbreiteter Irrtum). Sauber trennen:
- **Gesetzliches Sonderkündigungsrecht (§ 489 BGB):** Nach Ablauf von 10 Jahren seit vollständiger
  Auszahlung kann der Kreditnehmer mit 6 Monaten Frist ganz oder teilweise ohne
  Vorfälligkeitsentschädigung kündigen/ablösen — unabhängig von Zinsbindung und Tilgungshöhe.
- **Vertragliche Sondertilgung (z.B. 5 % oder 10 %/Jahr):** optionale, bankabhängige Vertragsklausel,
  KEIN gesetzlicher Anspruch. Im Rechner als eigener Parameter modelliert (`annual_sondertilgung`).

## Beleihungsauslauf (LTV) und Eigenkapital

Risikoabhängige, bankindividuelle Marktpraxis (nicht gesetzlich fixiert):
- bis 60 % LTV: günstigste Konditionen; 60–80 %: sehr gut; > 80 %: Aufschlag ~+0,1 bis +0,8 Punkte;
  ≥ 90 %: oft Zusatzsicherheiten, deutlich teurer. Zinsdifferenz 60 % vs. 90 % LTV ca. 1,3 Punkte.
- **Eigenkapitalbedarf:** Minimum = die Kaufnebenkosten aus Eigenkapital (~10 % des Kaufpreises);
  empfohlen 20–30 % EK-Quote für gute Konditionen. 110%-Vollfinanzierung möglich, aber deutlich teurer
  und riskanter. (interhyp.de)

## Leistbarkeit (Affordability)

**Haushaltsrechnung:** Nettoeinkommen − laufende Lebenshaltungskosten − bestehende Kreditraten −
künftige Bewirtschaftungskosten (Banken kalkulieren pauschal 2,50–3,00 €/m² Wohnfläche) =
Haushaltsüberschuss, der die Kreditrate decken muss.

**Bank-Faustregel:** Kreditrate max. 35–40 % des monatlichen Netto-Haushaltseinkommens; oberhalb 40 %
meist keine Zusage. Praxis-Faustregel, keine regulatorische Vorgabe. (baufimanufaktur.de)

## KfW-Förderung (Stand Anfang Juli 2026 — extrem volatil)

KfW-Zinsen sind teils tagesaktuell; nur als Richtwert mit Datum, Live-Zins von kfw.de zum Zusagetag.
Relevante Programme: Wohneigentumsprogramm (124, bis 100.000 €, keine Energieauflagen), Klimafreundlicher
Neubau (297/298), Wohngebäude-Sanierung (261, Tilgungszuschuss 5–45 %), Jung kauft Alt (308, Familien,
sanierungsbedürftiger Bestand), Wohneigentum für Familien (300).
