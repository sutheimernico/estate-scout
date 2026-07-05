# Immobilienbewertung

## Wertfaktoren einer Wohnimmobilie

**Lage** ist der wichtigste Einzelfaktor für Marktwert, Wertentwicklung und Vermietbarkeit.
- **Makrolage:** Region/Stadt/Landkreis, Wirtschaftskraft, Arbeitsmarkt, demografische Perspektive,
  Verkehrsanbindung.
- **Mikrolage:** unmittelbare Umgebung — Straße/Viertel, ÖPNV-Nähe, Nahversorgung, soziales Umfeld,
  Lärm, Sicherheit.

**Zustand / Baujahr / Sanierungsstand** wird v.a. über die **Alterswertminderung** im
Sachwertverfahren quantifiziert. Gesetzlich angesetzte Gesamtnutzungsdauer 80 Jahre für Ein-/
Zweifamilienhäuser und Eigentumswohnungen, lineare Wertminderung ca. 1,25 %/Jahr. Modernisierungen
verlängern die Restnutzungsdauer. (Grundsatz in ImmoWertV; erläuternd: certa-gutachten.de,
heid-immobilienbewertung.de — Gutachterportale, keine amtliche Primärquelle.)

**Energieeffizienz / GEG-Pflichten:** Der Energieausweis (Bedarfs- vs. Verbrauchsausweis) liefert die
Kennzahl; GEG-Nachrüst- und Betriebsverbotspflichten (§§ 47, 71, 72 GEG) beeinflussen den
Investitionsbedarf und damit den Wert. Bei Eigentümerwechsel: 2 Jahre Frist ab Grundbucheintragung
für Nachrüstpflichten (Details siehe Risiken/Recht).

**Grundstück:** Größe (größere Fläche = höherer Gesamtwert, kleinere pro m² teurer), Zuschnitt
(rechteckig vorteilhafter), Erschließungsgrad. **Wohnfläche nach WoFlV** (amtlich, seit 2004):
Deckenhöhe ≥ 2 m → 100 %, 1–2 m → 50 %, < 1 m → 0 %; Balkone/Terrassen 25–50 % (üblich 25 %); Keller,
Garagen, Heizungsräume nicht anrechenbar. **Ausstattung:** Marktkonvention einfach / gehoben /
luxuriös (keine Norm). Quelle: gesetze-im-internet.de/woflv, immobilienscout24.de.

## Bewertungsverfahren nach ImmoWertV 2022

Amtlicher Volltext: gesetze-im-internet.de/immowertv_2022.

- **Vergleichswertverfahren (§§ 24–25):** Wert aus tatsächlich erzielten Vergleichspreisen ähnlicher
  Objekte. Für Eigentumswohnungen und unbebaute Baugrundstücke — gilt als präziseste Methode.
- **Ertragswertverfahren (§§ 27–30):** nachhaltig erzielbare Mieteinnahmen minus
  Bewirtschaftungskosten, kapitalisiert mit dem Liegenschaftszinssatz. Für vermietete Rendite-/
  Mehrfamilienobjekte und Gewerbe.
- **Sachwertverfahren (§ 35, Boden § 40):** Bodenwert + (Herstellungskosten − Alterswertminderung),
  angepasst mit dem Sachwertfaktor der Gutachterausschüsse. Für selbstgenutzte Ein-/
  Zweifamilienhäuser und individuelle Objekte ohne ausreichende Vergleichspreise.

**Faustregel:** ETW → Vergleichswert; Eigenheim (Eigennutzung) → Sachwert; vermietetes Renditeobjekt
→ Ertragswert. In der Praxis oft mehrere Verfahren zur Plausibilisierung.

## Kennzahlen für Bewertung und Scoring

**Kaufpreisfaktor (KPF) / Vervielfältiger** = Kaufpreis / Jahreskaltmiete; Bruttorendite % ≈ 100 / KPF.
- KPF < 20 (> 5,0 % Rendite): attraktiv für Rendite-Investoren.
- KPF 20–25 (4,0–5,0 %): marktüblich.
- KPF > 30 (< 3,3 %): nur bei Wertsteigerungsstrategie (Cashflow negativ); Metropolen (München,
  Hamburg) aktuell 30–45.
Marktkonvention, keine Norm (homeday.de, immoverkauf24.de, Stand 2026).

**Mietrendite** (formelgenau; sparkasse.de, finanztip.de):
- Bruttomietrendite % = (Jahreskaltmiete / Kaufpreis) × 100.
- Nettomietrendite % = (Jahreskaltmiete − nicht umlegbare Bewirtschaftungskosten) / (Kaufpreis +
  Kaufnebenkosten) × 100.
Richtwerte: Bruttorendite ab 4 % solide, Nettorendite ab 3 % lohnend; Netto typ. 1–2 Prozentpunkte
unter Brutto. (Die exakte Berechnung übernimmt `finance/yield_metrics`.)

**Quadratmeterpreise — Quellen klar trennen:**
- Trend/Index (amtlich, belastbar): Destatis Häuserpreisindex (Q1 2026 +1,4 % ggü. Vorjahr; ländliche
  Kreise +3,6 %, TOP-7-Metropolen +0,3 %; PM Nr. 219 vom 2026-06-25) und vdp-Immobilienpreisindex
  (+2,3 %, 2026-05-12). Destatis liefert nur Indizes, keine absoluten €/m².
- Absolute €/m²: Portaldaten sind **Angebotspreise** aus Inseraten, nicht Transaktionspreise,
  tendenziell zu hoch — nur grobe Orientierung. Niedersachsen Häuser ~2.710 €/m², ETW ~2.277–2.624
  €/m² (immowelt.de, 3/2026); NRW gesamt ~2.846 €/m² (immowelt.de, 6/2026). Für absolute lokale
  Niveaus besser amtliche Gutachterausschuss-Daten nutzen (siehe Lage & Datenquellen).
