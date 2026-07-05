# Lage-/Standortqualität und öffentliche Datenquellen

## Signale für eine "gute Lage"

- **Infrastruktur/ÖPNV:** fußläufige Haltestellendistanz (bundesweit haben 93 % der Bevölkerung eine
  Haltestelle im 1000-m-Radius); U-/S-Bahn-Nähe bringt Wertaufschläge ~10–15 %. Nahversorgung
  (Supermarkt/Arzt/Grundschule im 1-km-Radius) ist ein harter Standortfaktor.
- **Demografie:** Bevölkerungswachstum vs. -schrumpfung ist der stärkste Preis- und Leerstandstreiber;
  die Altersstruktur steuert die Nachfrage nach Wohnungstyp.
- **Leerstand:** Referenz CBRE-empirica-Leerstandsindex (marktaktiver Leerstand): Ende 2024 ~2,2 %
  bundesweit (West 1,7 %, Ost o. Berlin 5,4 %); wachsende Regionen 1,4 % vs. schrumpfende 6,9 %.
- **Mietspiegel-Trend:** der Verlauf aufeinanderfolgender Mietspiegel-Fortschreibungen einer Stadt ist
  ein direktes, amtlich legitimiertes Nachfragesignal (z.B. Dortmund +5,01 % zur Vorerhebung).

Quellen: poschmann-immobilien.com, empirica-regio.de (Leerstandsindex 2025).

## Öffentliche/legale Datenquellen (Übersicht)

- **BORIS-D** (bodenrichtwerte-boris.de): bundesweite Bodenrichtwerte teilnehmender Länder (inkl. NI +
  NRW) in einer Karte, kostenlos, keine Registrierung. Web-Kartenviewer; teils länderseitig WMS/WFS,
  keine einheitliche REST-API. Jährlicher Stichtag (i.d.R. 1.1.). Nur informativ, ersetzt kein
  Wertgutachten (Datenlizenz Deutschland – Namensnennung 2.0).
- **BORIS.NI** (immobilienmarkt.niedersachsen.de/bodenrichtwerte): Viewer kostenlos; rechtsverbindliche
  Auszüge kostenpflichtig (Registrierung, Betreiber LGLN). Keine dokumentierte API.
- **BORIS.NRW** (boris.nrw.de, Betreiber IT.NRW): online kostenlos; WMS teils über open.nrw;
  schriftliche Auszüge ~15–50 €. Keine dokumentierte REST-API.
- **Gutachterausschüsse / Grundstücksmarktberichte (§§ 192 ff. BauGB):** unabhängige Gremien,
  veröffentlichen jährlich reale Transaktionsdaten kostenlos als PDF/Dashboard. Niedersachsen: 9
  Ausschüsse (immobilienmarkt.niedersachsen.de). NRW: "Grundstücksmarktbericht NRW 2025" (Berichtsjahr
  2024: 113.144 Kaufverträge, 40,72 Mrd. €). **Beste Quelle für reale lokale Preisniveaus.**
- **Mietspiegel (§§ 558c/558d BGB):** ortsübliche Vergleichsmiete je Stadt, kommunal, kostenlos. Kein
  zentraler Download — jede Kommune einzeln. Qualifizierter Mietspiegel hat gesetzliche
  Richtigkeitsvermutung. BBSR-Meta-Übersicht: 715 Mietspiegel für 1.391 Gemeinden, 461 qualifiziert.
- **Zensus 2022** (ergebnisse.zensus2022.de): Bevölkerung, Gebäude, Wohnungen (Leerstand, Baujahr) bis
  Gemeinde-/Rasterebene (100m-Zellen). CSV/Excel; API + Großabrufe nach kostenloser Registrierung.
- **GENESIS / Regionalstatistik.de:** Zeitreihen Bevölkerung/Wohnen bis Gemeindeebene. RESTful/JSON-
  Webservice (Registrierung Pflicht seit 5/2025, ab 2025-11-27 nur POST). **Bester Weg für
  kleinräumige Demografie per API.**
- **empirica-Preisdatenbank:** größte Inserats-Sammlung, aber kommerziell (REST-API nur auf Anfrage).
- **EUROSTAT HPI:** Häuserpreisindex nur national, gut als Makro-Referenz, REST-API vorhanden.

**Empfehlung fürs Tool:** für Trend Destatis/vdp; für absolute lokale Niveaus amtliche
Gutachterausschuss-Daten; für Demografie Zensus/GENESIS-API. Portaldaten immer mit "Stand: [Datum]".

## Vorbehalte (vor produktiver Nutzung prüfen)

BORIS-API-Verfügbarkeit (WMS/WFS vs. nur Viewer) ist uneinheitlich dokumentiert — direkt bei LGLN (NI)
/ IT.NRW (NRW) nachfragen. Mietpreisbremse-Städtelisten gegen amtliche Verordnungen verifizieren.
