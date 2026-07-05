# Kaufnebenkosten

Die exakte Aufschlüsselung berechnet `finance/purchase_costs` aus der versionierten Config
(`config/rates.yaml`). Dieser Text erklärt die Bestandteile. Alle Sätze Stand 2026-07-05.

## Grunderwerbsteuer (alle 16 Bundesländer)

Fraktion des Kaufpreises, per Landesgesetz festgelegt (Stand 2026-07-05, cross-verifiziert via
finanz-tools.de; für verbindliche Nutzung mit dem Landesfinanzministerium gegenprüfen):

| Bundesland | Satz |
|---|---|
| Bayern | 3,5 % |
| Niedersachsen, Baden-Württemberg, Rheinland-Pfalz, Sachsen-Anhalt, Thüringen | 5,0 % |
| Sachsen, Hamburg, Bremen | 5,5 % |
| Berlin, Hessen, Mecklenburg-Vorpommern | 6,0 % |
| Nordrhein-Westfalen, Brandenburg, Saarland, Schleswig-Holstein | 6,5 % |

**Fokusregionen: Niedersachsen 5,0 %, NRW 6,5 %.** Auf 300.000 € sind das 15.000 € (NI) vs. 19.500 €
(NRW) — Unterschied 4.500 €.

## Notar + Grundbuch

Gesamt ca. 1,5–2 % des Kaufpreises (Notar ~1,0–1,5 %, Grundbuch ~0,5 %), bundeseinheitlich nach
GNotKG, nicht verhandelbar, in der Regel vom Käufer getragen. Zum 2025-06-01 wurden die Gebühren
erhöht (Wertgebühren +6 %, Festgebühren +9 %). (finanztip.de) Der Rechner nutzt Notar 1,5 % +
Grundbuch 0,5 % als konfigurierbaren Default.

## Maklerprovision

Gesetz über die Verteilung der Maklerkosten (Bestellerprinzip), in Kraft seit 2020-12-23 — gilt für
den Kauf von Wohnungen/Einfamilienhäusern durch Verbraucher (nicht unbebaute Grundstücke,
Mehrfamilienhäuser, Gewerbe). Beauftragt der Verkäufer den Makler, zahlt der Käufer maximal 50 %
(hälftige Teilung = Normalfall). Übliche Gesamtprovision 2026: 5,95–7,14 % inkl. MwSt., oft je 3,57 %
für Käufer und Verkäufer. (drklein.de, immobilienscout24.de) Der Makleranteil ist im Rechner optional
(0, wenn kein Makler oder verkäuferseitig getragen).

## Nebenkosten-Gesamtquote (Fokusregionen)

- Niedersachsen: ~5,0 % GrESt + ~2 % Notar/Grundbuch + ggf. ~3,57 % Makler ≈ **~7 % ohne Makler,
  ~10,5 % mit Makler**.
- NRW: ~6,5 % GrESt + ~2 % Notar/Grundbuch + ggf. ~3,57 % Makler ≈ **~8,5 % ohne Makler, ~12 % mit
  Makler**.

Faustregel für die Renditerechnung: 10–15 % Kaufnebenkosten. Wichtig für die Eigenkapitalplanung: Die
Nebenkosten sollten aus Eigenkapital gedeckt sein (Banken finanzieren sie ungern mit).
