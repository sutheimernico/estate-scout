# Domänen-Wissensbasis: Deutsches Immobilien-Analyse-Tool

**Zielgruppe:** privater Käufer / angehender Kleininvestor, Fokusregionen Niedersachsen und NRW.
**Zweck:** faktische Grundlage für (a) RAG-Wissensbasis, (b) Scoring-/Bewertungs-Engine, (c) Finanzrechner.
**Recherchestand:** 2026-07-05. Alle marktabhängigen Zahlen (Zinsen, Steuersätze, Preise, KfW-Konditionen) veralten — inline mit Stand/Quelle versehen, im Tool als konfigurierbare Werte mit sichtbarem Datumsstempel führen, nicht hart codieren.

**Zwei laufende Gesetzesänderungen im Auge behalten** (beide zum Recherchestand nur Entwurf/Kabinettsbeschluss, noch NICHT geltendes Recht):
- Gebäudemodernisierungsgesetz (GModG/GMG) soll die GEG-65%-Heizungspflicht und § 72 GEG (30-Jahres-Kesseltauschpflicht) ablösen, geplant zum 1.11.2026. Kabinettsbeschluss 13.5.2026.
- Vor Produktivsetzung auf [bbsr-geg.bund.de](https://www.bbsr-geg.bund.de) und [bundesregierung.de](https://www.bundesregierung.de/breg-de/aktuelles/neues-gebaeudemodernisierungsgesetz-2430284) prüfen, ob verabschiedet.

---

## 1. Immobilienbewertung

### 1.1 Wertfaktoren einer Wohnimmobilie

**Lage (wichtigster Einzelfaktor für Marktwert, Wertentwicklung, Vermietbarkeit)**
- **Makrolage:** Region/Stadt/Landkreis, Wirtschaftskraft, Arbeitsmarkt, demografische Perspektive, Verkehrsanbindung.
- **Mikrolage:** unmittelbare Umgebung — Straße/Viertel, ÖPNV-Nähe, Nahversorgung, soziales Umfeld, Lärm, Sicherheit.
- Signal-Detailkatalog siehe Bereich 2.

**Zustand / Baujahr / Sanierungsstand** — quantifiziert v.a. über die **Alterswertminderung** im Sachwertverfahren. Gesetzlich angesetzte **Gesamtnutzungsdauer 80 Jahre** für Ein-/Zweifamilienhäuser und ETW, lineare Wertminderung ca. **1,25 %/Jahr**. Modernisierungen verlängern die Restnutzungsdauer und mindern die Alterswertminderung. (Grundsatz in ImmoWertV/Anlagen; erläuternde Quellen: [certa-gutachten.de](https://www.certa-gutachten.de/ratgeber/alterswertminderung-sachwertverfahren-tabelle), [heid-immobilienbewertung.de](https://www.heid-immobilienbewertung.de/ratgeber/alterswertminderung/) — Gutachterportale, keine amtliche Primärquelle.)

**Energieeffizienzklasse / GEG-Pflichten** (Stand 07/2026, Detailregelungen siehe Bereich 5): Energieausweis (Bedarfs- vs. Verbrauchsausweis) liefert die Kennzahl; GEG-Nachrüst- und Betriebsverbotspflichten (§§ 47, 71, 72 GEG) beeinflussen Investitionsbedarf und damit Wert. **Frist bei Eigentümerwechsel: 2 Jahre ab Grundbucheintragung** für Nachrüstpflichten.

**Grundstück:** Größe (größere Fläche = höherer Gesamtwert, kleinere Fläche pro m² teurer), Zuschnitt (rechteckig vorteilhafter als schmal/unregelmäßig), Erschließungsgrad (voller Ver-/Entsorgungsanschluss wertsteigernd). ([korte-immobilien.de](https://www.korte-immobilien.de/grundstueck-bewerten-was-den-wert-von-bauland-bestimmt/) — Gutachterportal.)

**Wohnfläche nach WoFlV** (amtlich: [gesetze-im-internet.de/woflv](https://www.gesetze-im-internet.de/woflv/BJNR234610003.html), gültig seit 1.1.2004; im Streitfall gerichtlicher Standard):
- Deckenhöhe ≥ 2 m → 100 % Anrechnung; 1–2 m → 50 %; < 1 m → 0 %.
- Balkone/Terrassen/Loggien: 25–50 % (üblich 25 %, bei hochwertiger Lage/Ausstattung bis 50 %).
- Nicht anrechenbar: Keller-/Abstell-/Heizungs-/Trockenräume außerhalb der Wohnung, Garagen, gewerblich genutzte Räume.

**Ausstattung** — dreistufige Marktkonvention (keine Norm): **einfach / gehoben / luxuriös**, bewertet nach Material-/Verarbeitungsqualität von Böden, Sanitär, Küche, Heizungstechnik, Smart-Home. ([immobilienscout24.de](https://www.immobilienscout24.de/wissen/verkaufen/ausstattung.html).)

### 1.2 Bewertungsverfahren nach ImmoWertV 2022

Amtlicher Volltext: [gesetze-im-internet.de/immowertv_2022](https://www.gesetze-im-internet.de/immowertv_2022/BJNR280500021.html).

| Verfahren | §§ ImmoWertV | Prinzip | Typische Anwendung |
|---|---|---|---|
| **Vergleichswertverfahren** | §§ 24–25 | Wert aus ausreichender Anzahl tatsächlich erzielter Vergleichspreise ähnlicher Objekte | Eigentumswohnungen, unbebaute Baugrundstücke — gilt als präziseste Methode (bildet reales Marktniveau direkt ab) |
| **Ertragswertverfahren** | §§ 27–30 | Nachhaltig erzielbare Mieteinnahmen minus Bewirtschaftungskosten, kapitalisiert mit dem **Liegenschaftszinssatz** (§ 21 Abs. 2) | Vermietete Wohn-/Renditeobjekte, Mehrfamilienhäuser, Gewerbe |
| **Sachwertverfahren** | § 35 (Boden § 40) | Bodenwert + (Herstellungskosten − Alterswertminderung), angepasst mit **Sachwertfaktor** (§ 21 Abs. 3, von Gutachterausschüssen veröffentlicht) | Selbstgenutzte Ein-/Zweifamilienhäuser, individuelle Objekte ohne ausreichende Vergleichspreise |

**Faustregel Verfahrenswahl:** ETW → Vergleichswert; Eigenheim (Eigennutzung) → Sachwert; vermietetes Renditeobjekt → Ertragswert. In der Praxis oft mehrere Verfahren zur Plausibilisierung.

### 1.3 Kennzahlen für Scoring/Bewertung

**Kaufpreisfaktor / Vervielfältiger (Preis-Miete-Verhältnis)**
```
Kaufpreisfaktor (KPF) = Kaufpreis / Jahreskaltmiete
Bruttorendite % ≈ 100 / KPF
```
| KPF | ≈ Bruttorendite | Einordnung (Marktkonvention, keine Norm) |
|---|---|---|
| < 20 | > 5,0 % | attraktiv für Rendite-Investoren |
| 20–25 | 4,0–5,0 % | marktüblich |
| > 30 | < 3,3 % | nur bei Wertsteigerungsstrategie (Cashflow negativ); Metropolen (München, Hamburg) aktuell 30–45 |

Quelle: [homeday.de](https://www.homeday.de/de/immobilienbewertung/vervielfaeltiger-kaufpreisfaktor/) (Stand 2026), [immoverkauf24.de](https://www.immoverkauf24.de/immobilienverkauf/immobilienverkauf-a-z/kaufpreisfaktor/) — Marktportale, als Faustwert behandeln.

**Mietrendite (formelgenau bestätigt via [sparkasse.de](https://www.sparkasse.de/pk/ratgeber/wohnen/immobilie-erwerben/mietrendite.html) und [finanztip.de](https://www.finanztip.de/baufinanzierung/mietrendite-berechnen/)):**
```
Bruttomietrendite % = (Jahreskaltmiete / Kaufpreis) × 100

Nettomietrendite % = (Jahreskaltmiete − nicht umlegbare Bewirtschaftungskosten)
                     / (Kaufpreis + Kaufnebenkosten) × 100
```
Kaufnebenkosten üblich **10–15 %** des Kaufpreises. Richtwerte: Bruttorendite ab 4 % solide, Nettorendite ab 3 % lohnend; Netto liegt typ. 1–2 Prozentpunkte unter Brutto.

**Quadratmeterpreise (mit klarer Quellentrennung):**
- **Trend/Index (belastbar, amtlich):** Destatis Häuserpreisindex, PM Nr. 219 vom **25.06.2026** ([destatis.de](https://www.destatis.de/DE/Presse/Pressemitteilungen/2026/06/PD26_219_61262.html)): Wohnimmobilien Q1 2026 **+1,4 %** ggü. Vorjahr. Regionale Divergenz: ländliche Kreise +3,6 % (ETW) vs. TOP-7-Metropolen nur +0,3 %. **Destatis liefert nur Indizes, keine absoluten €/m².** Ergänzend vdp-Immobilienpreisindex (12.05.2026): Wohnimmobilien +2,3 % ggü. Vorjahr ([vdpresearch.de](https://www.vdpresearch.de/immobilienpreise-steigen-zu-jahresbeginn-2026-weiter/)).
- **Absolute €/m² (Portaldaten = Angebotspreise aus Inseraten, NICHT Transaktionspreise, methodisch uneinheitlich, tendenziell zu hoch — nur als grobe Orientierung):**
  - Niedersachsen: Häuser Ø ~2.710 €/m², ETW Ø ~2.277–2.624 €/m² ([immowelt.de](https://www.immowelt.de/immobilienpreise/niedersachsen/ad04de3), Stand 3/2026). Amtlicher Vergleich: [NIPIX Niedersächsischer Immobilienpreisindex](https://immobilienmarkt.niedersachsen.de/immobilienpreisindex).
  - NRW: Gesamt Ø ~2.846 €/m², ETW Ø ~2.895 €/m², Häuser Ø ~2.917 €/m² ([immowelt.de](https://www.immowelt.de/immobilienpreise/nordrhein-westfalen/ad04de5), Stand 6/2026).
- **Empfehlung fürs Tool:** für Trend Destatis/vdp; für absolute lokale Niveaus amtliche Gutachterausschuss-Daten (Bereich 2). Portaldaten mit "Stand: [Datum]"-Tag, regelmäßig neu abrufen statt statisch cachen.

---

## 2. Lage-/Standortqualität + Datenquellen

### 2.1 Signale für eine "gute Lage"

- **Infrastruktur/ÖPNV:** fußläufige Haltestellendistanz (bundesweit 93 % der Bevölkerung haben Haltestelle im 1000-m-Radius); U-/S-Bahn-Nähe bringt Wertaufschläge ~10–15 %. Nahversorgung (Supermarkt/Arzt/Grundschule im 1-km-Radius, für ~75 % der Bevölkerung erfüllt) ist harter Standortfaktor. ([poschmann-immobilien.com](https://www.poschmann-immobilien.com/blog/standortfaktoren-lage/), [hausundgrund-wesseling.de](https://www.hausundgrund-wesseling.de/aktuelles/einzelansicht/wichtiger-standortfaktor-fuer-wohnimmobilien-so-steht-es-um-die-nahversorgung/) — Fachportale.)
- **Demografie:** Bevölkerungswachstum vs. -schrumpfung ist stärkster Preis-/Leerstandstreiber; Altersstruktur steuert Nachfrage nach Wohnungstyp. Granular über Zensus/Regionalstatistik (2.2.6).
- **Leerstand:** Referenz CBRE-empirica-Leerstandsindex (marktaktiver Leerstand): Ende 2024 **522.000 Einheiten / 2,2 %** (West 1,7 %, Ost o. Berlin 5,4 %); wachsende Regionen 1,4 % vs. schrumpfende 6,9 % ([empirica-regio.de](https://www.empirica-regio.de/news/251216_cbre_empirica_leerstandsindex_2025/)). Rohleerstandsquote je Gemeinde aus Zensus.
- **Mietspiegel-Trend:** Verlauf aufeinanderfolgender Mietspiegel-Fortschreibungen einer Stadt = direktes, amtlich legitimiertes Nachfragesignal (z.B. Dortmund +5,01 % zur Vorerhebung).

### 2.2 Datenquellen (öffentlich/legal) — Übersicht

| Quelle | Was | Kostenlos? | API/Zugriff | Aktualität |
|---|---|---|---|---|
| **BORIS-D** | Bundesweite Bodenrichtwerte (teilnehmende Länder in einer Karte, inkl. NI + NRW) | ja, keine Registrierung | Web-Kartenviewer; teils länderseitig WMS/WFS, keine einheitl. REST-API | jährlich (Stichtag i.d.R. 1.1.) |
| **BORIS.NI** | Bodenrichtwerte Niedersachsen | Viewer kostenlos; amtl. Auszüge kostenpflichtig (GOGut, Registrierung) | WebGIS, PDF-Auszüge; keine dokumentierte API | jährlich (9 regionale Gutachterausschüsse) |
| **BORIS.NRW** | Bodenrichtwerte NRW | Online kostenlos; schriftl. Auszüge ~15–50 € | Web-Viewer; teils WMS (Open.NRW); keine dok. REST-API | jährlicher Stichtag |
| **Gutachterausschüsse / Grundstücksmarktberichte** | Transaktionsvolumen, reale Kaufpreise, Preisentwicklung je Segment | ja, PDF | Download | jährlich |
| **Mietspiegel** | ortsübliche Vergleichsmiete je Stadt | ja (kommunal) | pro Kommune einzeln; keine zentrale DB | qualifiziert: alle 2 J. Fortschreibung, alle 4 J. neu |
| **Zensus 2022** | Bevölkerung, Gebäude, Wohnungen (Leerstand, Baujahr) bis Gemeinde-/Rasterebene | ja | CSV/Excel-Export; API + Großabrufe nach kostenloser Registrierung | Zensus-Stichtag 2022 |
| **GENESIS / Regionalstatistik.de** | Zeitreihen Bevölkerung/Wohnen bis Gemeindeebene | ja | RESTful/JSON-Webservice (Registrierung Pflicht seit 5/2025, ab 27.11.2025 nur POST) | laufend |
| **empirica-Preisdatenbank** | größte Inserats-Sammlung (Kauf+Miete) ab 2004 | **nein, kommerziell** | Marktstudio, REST-API, nur auf Anfrage | quartalsweise |
| **EUROSTAT HPI** | Häuserpreisindex Deutschland (nur national) | ja | Data Browser, Bulk, SDMX, REST-API | Lag ~1 Quartal |

### 2.3 Details zu den zentralen Quellen

**BORIS (Bodenrichtwerte):**
- BORIS-D: [bodenrichtwerte-boris.de](https://www.bodenrichtwerte-boris.de/) — bündelt Werte teilnehmender Länder (inkl. NI + NRW) direkt in einer Karte; Lizenz "Datenlizenz Deutschland – Namensnennung 2.0"; nur informativ, ersetzt kein Wertgutachten.
- BORIS.NI: freier Viewer [immobilienmarkt.niedersachsen.de/bodenrichtwerte](https://immobilienmarkt.niedersachsen.de/bodenrichtwerte); rechtsverbindliche Auszüge kostenpflichtig über [boris.niedersachsen.de/boris/register](https://www.boris.niedersachsen.de/boris/register) (Betreiber LGLN).
- BORIS.NRW: [boris.nrw.de](https://www.boris.nrw.de/) (Betreiber IT.NRW); WMS-Geodatensatz teils über [open.nrw](https://open.nrw/dataset/bodenrichtwerte-nrw-w). Beispiel Auszugsgebühr Dortmund ~50 € ([gars.nrw](https://www.gars.nrw/dortmund/produkte-do/bodenrichtwert-do)).

**Gutachterausschüsse (§§ 192 ff. BauGB):** unabhängige Gremien, ermitteln Bodenrichtwerte + veröffentlichen jährliche Grundstücksmarktberichte (reale Transaktionsdaten).
- Niedersachsen: 9 Ausschüsse, Berichte als interaktive Dashboards kostenlos ([immobilienmarkt.niedersachsen.de](https://immobilienmarkt.niedersachsen.de), [gag.niedersachsen.de](https://www.gag.niedersachsen.de/startseite/grundstucksmarktberichte/)); "Niedersächsischer Landesgrundstücksmarktbericht 2025".
- NRW: "Grundstücksmarktbericht NRW 2025" (Berichtsjahr 2024: 113.144 Kaufverträge, 40,72 Mrd. € Umsatz, +16 %) via [boris.nrw.de](https://www.boris.nrw.de) / [im.nrw](https://www.im.nrw/grundstuecksmarktbericht-nordrhein-westfalen-2025-der-markt-erholt-sich-wieder); lokale Berichte je Ausschuss.

**Mietspiegel (§§ 558c einfach / 558d qualifiziert BGB):** qualifizierter Mietspiegel hat gesetzliche Richtigkeitsvermutung. Status abgefragter Städte:

| Stadt | Typ | Stand |
|---|---|---|
| Hannover | qualifiziert | ab 18.12.2025 |
| Braunschweig | qualifiziert | seit 08.04.2025 |
| Osnabrück | einfach (qual. für 01/2027 geplant) | 2025/2026 |
| Köln | einfach | 04/2025 |
| Düsseldorf | einfach | seit 01.04.2024 |
| Dortmund | qualifiziert | 2025/2026 (+5,01 %) |
| Münster | qualifiziert | 04/2025–03/2027 (nicht direkt verifiziert) |

Zentrale Meta-Übersicht (nur Statistik, keine Downloads): [BBSR-Mietspiegelsammlung](https://www.bbsr.bund.de/BBSR/DE/forschung/fachbeitraege/wohnen-immobilien/mieten-preise/Mietspiegel/Mietspiegel.html) — aktuell 715 Mietspiegel für 1.391 Gemeinden, 461 qualifiziert. **Kein zentraler Download je Stadt — jede Kommune einzeln.**

**Zensus / Regionalstatistik (bester Weg für kleinräumige Demografie/Wohnungsdaten):**
- Zensus 2022: [ergebnisse.zensus2022.de/datenbank/online](https://ergebnisse.zensus2022.de/datenbank/online/) — Tabellen bis Gemeindeebene + Rasterdaten (100m-Zellen), CSV/Excel; API + Großabrufe nach kostenloser Registrierung.
- GENESIS/Regionalstatistik: [regionalstatistik.de/genesis/online](https://www.regionalstatistik.de/genesis/online/) — RESTful/JSON-Webservice (Registrierung Pflicht seit 5/2025, ab 27.11.2025 nur noch POST).
- Landesämter: LSN Niedersachsen ([statistik.niedersachsen.de](https://www.statistik.niedersachsen.de/startseite/datenangebote/lsn_online_datenbank/), Tool "Meine Gemeinde, meine Stadt") und IT.NRW Kommunalprofile ([statistik.nrw](https://statistik.nrw/regionale-profile/datendownloads-kommunalprofile)) — beide kostenlos, Excel/CSV.

**empirica / EUROSTAT:**
- empirica-Immobilienpreisindex: Presseartikel mit Kernzahlen frei ([empirica-institut.de](https://www.empirica-institut.de/nachrichten/details/nachricht/empirica-immobilienpreisindex-i2026/)); Rohdaten/API kommerziell.
- EUROSTAT HPI Deutschland: nur nationale Ebene, ungeeignet für lokale Analysen, gut als Makro-Referenz. REST-API-Beispiel: `https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/prc_hpi_q?format=JSON&geo=DE`.

---

## 3. Datenzugriff Listings (rechtliche Lage) — KRITISCHSTER PUNKT

**Kernfrage:** Ist automatisiertes Scouting/Scraping von ImmoScout24, Immowelt, Kleinanzeigen für eine Privatperson legal machbar?

**Kurzantwort:** Nicht eindeutig verboten (kein Straftatbestand beim reinen Auslesen öffentlicher Seiten ohne Umgehung echter Zugangssicherung), aber **riskant** — nicht wegen Strafrecht, sondern wegen der Kombination aus AGB-Bruch (zivilrechtlich), Datenbankschutzrecht (§ 87a UrhG) bei systematischem Vollabgriff, aktivem Bot-Schutz (Cloudflare/Akamai) und DSGVO-Exposition durch mitgescrapte Kontaktdaten Dritter.

### 3.1 Der zentrale Präzedenzfall

**BGH, 30.04.2014, Az. I ZR 224/12 ("Screen Scraping"/Ryanair):**
- Automatisiertes Auslesen ist **nicht per se unlauterer Wettbewerb (§ 4 UWG)**.
- Zulässig, **solange**: keine Umgehung technischer Schutzvorrichtungen, keine Serverüberlastung, keine irreführende Darstellung.
- **Reine AGB-Verstöße allein rechtfertigen kein gerichtliches Verbot** — wichtigste Erkenntnis. AGB-Klauseln binden zivilrechtlich (→ Accountsperrung, ggf. Unterlassung), begründen aber keinen eigenständigen Wettbewerbsverstoß.
- Literatur überträgt das ausdrücklich auf Immobilien-/Job-/Preisvergleichsportale.
- Quellen: [lto.de](https://www.lto.de/recht/hintergruende/h/bgh-urteil-izr22412-screen-scraping-flugdaten-automatisiert-auslesen-ryanair-reiseportal), [ra-plutte.de](https://www.ra-plutte.de/bgh-zum-automatisierten-auslesen-fremder-websites-via-screen-scraping/).

### 3.2 Portal-für-Portal

**ImmoScout24** ([Verbraucher-AGB](https://www.immobilienscout24.de/agb/verbraucher-agb.html)):
- Ziff. 8.2 verbietet explizit "automatisierte Abfrage durch Skripte, Bots, Crawler ... Data Mining, Data Extraction". Ziff. 8.3 verbietet Aufbau eigener Datenbank aus den Daten. Sanktion: Accountsperrung/Kündigung (Ziff. 5.6) — zivilrechtlich, kein Straftatbestand.
- Bot-Schutz: Cloudflare mit TLS-/JA3-Fingerprinting, JS-Challenges, Turnstile-CAPTCHAs, Trust-Scoring, Rate-Limiting — **echte technische Schutzmaßnahme**.
- API: [api.immobilienscout24.de](https://api.immobilienscout24.de/) nur für gewerbliche Anbieter/Makler + "Content Partner" via OAuth mit Freigabe eines IS24-Kunden. **Kein offener Privatpersonen-Zugang zu Sucher-Daten.**
- Keine Gerichtsurteile speziell zu IS24-Scraping gefunden (aktuelles LG-Berlin-Urteil 06/2025 betraf SCHUFA-Werbung/DSGVO, nicht Scraping).

**Immowelt** ([AGB](https://www.immowelt.de/immoweltag/agb)): AGB schließen Zugriff über Crawler/skriptgesteuerte Systeme aus. API nur für **Anbieter** (eigene Objekte), Aggregation Dritter braucht ausdrückliche Zustimmung der AVIV Germany GmbH. Bot-Schutz praxisüblich (Cloudflare/Akamai-Klasse).

**Kleinanzeigen.de** ([Nutzungsbedingungen](https://themen.kleinanzeigen.de/nutzungsbedingungen/)): untersagt "Roboter, Crawler, Spider, Scraper ... automatisierte Mechanismen" ohne schriftliche Zustimmung. Bot-Schutz: Akamai (Fingerprinting, TLS-Analyse, blockiert Rechenzentrums-IPs). Keine öffentliche Endnutzer-API.

### 3.3 Datenbankschutz und Strafrecht

- **§ 87a ff. UrhG (Sui-generis-Datenbankschutz):** Immobilienportale mit tausenden strukturierten Datensätzen qualifizieren als geschützte Datenbank. Geschützt ist Entnahme **wesentlicher Teile** (Literatur-Richtwert ~20 %) oder wiederholt-systematische Entnahme unwesentlicher Teile. → **Einzelabruf für Eigenbedarf unkritisch; systematischer Vollabgriff zum Aufbau eigener DB berührt echtes Immaterialgüterrecht** (nicht nur AGB). ([gesetze-im-internet.de/urhg/__87a](https://www.gesetze-im-internet.de/urhg/__87a.html))
- **§ 202a/202c StGB (Ausspähen):** nur bei Überwindung einer "besonderen Sicherung" (Passwort/Verschlüsselung) einschlägig. Öffentlich ohne Login einsehbare Anzeigen erfüllen das i.d.R. nicht; reines Umgehen von Cloudflare-Bot-Detection ist meist keine Zugangssicherung i.S.d. § 202a. Restrisiko gering, aber nicht null bei echten Login-/Captcha-Walls.

### 3.4 DSGVO — der oft unterschätzte Punkt

- Anzeigen enthalten personenbezogene Daten (Name, Telefon, teils Adresse der Anbieter). Wer diese scraped/speichert, wird datenschutzrechtlich Verantwortlicher (Art. 4 Nr. 7 DSGVO).
- **Haushaltsausnahme (Art. 2 Abs. 2 lit. c DSGVO)** wird eng ausgelegt; sobald Daten Dritter systematisch in eigener DB verarbeitet werden, fraglich ob sie trägt. Für Einzelperson ohne kommerziellen Zweck niedrigschwelliges Risiko, aber kein Freifahrtschein.
- BGH 2024/25 (Facebook-Scraping): schon kurzzeitiger Kontrollverlust kann immateriellen Schaden nach Art. 82 DSGVO begründen; OLG München (13.02.2025, 24 U 3020/24) lehnte in anderem Fall ab — Rechtslinie uneinheitlich.
- **Tool-Design-Konsequenz:** Kontaktdaten der Anbieter (Name/Telefon/E-Mail) **NICHT persistent speichern** — nur objektbezogene Merkmale (Preis, Größe, Lage, Ausstattung, Link zum Original). Reduziert DSGVO-Exposition erheblich, unabhängig von der AGB-Frage sinnvoll.
- Quellen: [noerr.com](https://www.noerr.com/de/insights/bgh-urteil-zum-immateriellen-schadensersatz-der-dsgvo-wegen-scraping), [dr-datenschutz.de](https://www.dr-datenschutz.de/die-haushaltsausnahme-der-dsgvo/).

### 3.5 Legale Alternativen

- **zvg-portal.de** (Zwangsversteigerungen): amtliches Justizportal der Länder, öffentlich-rechtliche Publikationspflicht → **rechtlich deutlich unkritischer** (kein privates AGB-Scraping-Verbot, kein Datenbankherstellerrecht eines Wettbewerbers). Aber: **kein API**, komplexe Session-Cookies erschweren Standard-Scraper; Gutachten/Exposés uneinheitlich je Amtsgericht. ([zvg-portal.de](https://www.zvg-portal.de/))
- **OpenImmo-Standard** ([openimmo.de](https://www.openimmo.de/)): XML-Branchenstandard für Datenaustausch **zwischen Maklersoftware und Portalen** (Anbieterseite), nicht für Sucher-Aggregation. Kein öffentlicher Privatpersonen-Zugang.
- **RSS-Feeds:** IS24 und Immowelt boten historisch offizielle RSS-Suchfeeds (Presseartikel 2007–2009), heute vermutlich zugunsten von E-Mail-Suchagenten zurückgebaut. **Wäre der rechtssicherste automatisierte Weg — vor Implementierung live prüfen, ob Endpunkte noch existieren.**
- **Manuell/halbautomatisch:** offizielle Merkzettel-/Suchauftrag-Funktionen + E-Mail-Benachrichtigungen ins eigene Tool einspeisen (rechtlich unbedenklich, vom Portal vorgesehene Nutzung); einzelne Objekt-URLs manuell einfügen; Browser-Erweiterung, die nur die vom Nutzer selbst geladene Seite ausliest ("manuelle Nutzung mit Werkzeug", nicht automatisiertes Crawling).

### 3.6 Ampel-Bewertung + pragmatischer Rat

- **Grün (unkritisch):** manuelle Nutzung, offizielle Suchagenten/E-Mail-Benachrichtigungen, ggf. aktive RSS-Feeds, gelegentlicher Einzelabruf von Objektseiten.
- **Gelb (vertretbar, Restrisiko):** moderates automatisiertes Abrufen öffentlicher Suchergebnisseiten OHNE Bot-Schutz-Umgehung, ohne Serverlast, ohne Vollspiegelung, ohne Speicherung personenbezogener Daten. Größtes reales Risiko: **Accountsperrung/IP-Bann** (zivilrechtlich), kein Verfahren.
- **Rot (eindeutig riskant):** aktive Umgehung von Cloudflare/Akamai per Stealth-Browser/Fingerprint-Spoofing, systematischer Vollabgriff zur Konkurrenz-DB, gewerbliche Verwertung, dauerhafte Speicherung personenbezogener Verkäuferdaten.

**Rat:** Für ein privates Tool primär zvg-portal.de + offizielle RSS-/Suchagent-Funktionen nutzen. Falls doch Portal-Abruf: keine Bot-Schutz-Umgehung, niedrige Rate (< 1 req/s, menschenähnlich), nur eigenbedarfsrelevante Objektdaten speichern (keine Vollspiegelung, keine personenbezogenen Daten). Rechtlich wasserdicht (kein Restrisiko) ist ausschließlich der manuelle/RSS-/offizielle-API-Weg.

---

## 4. Finanzierungsmathematik

### 4.1 Annuitätendarlehen

**Monatsrate (deutsche Baufinanzierungspraxis):**
```
Monatsrate = K₀ × (Sollzins_p.a. + Anfangstilgung_p.a.) / 12
```
K₀ = Darlehenssumme; Zins und Tilgung als Dezimal (z.B. 0,035).

**Exakte Restschuld** (monatliche Verzinsung, für Anschlussfinanzierung):
```
i_m = Sollzins_p.a. / 12
Restschuld(n) = K₀ × (1+i_m)ⁿ − A × [((1+i_m)ⁿ − 1) / i_m]
```
n = gezahlte Monatsraten, A = konstante Monatsrate.

- **Zins-Tilgungs-Mechanik:** bei konstanter Annuität sinkt der Zinsanteil (auf sinkende Restschuld), Tilgungsanteil steigt um denselben Betrag — Rate bleibt konstant.
- **Sollzins ≠ Effektivzins:** Effektivzins berücksichtigt unterjährige Zinseszinsen, Auszahlungskurs, Bereitstellungszinsen (Differenz meist 0,07–0,1 Prozentpunkte).
- **Anfängliche Tilgung:** marktüblich 1/2/3 % (bis 5 %). Höhere Tilgung → deutlich kürzere Gesamtlaufzeit. Rechner-Default oft 2 %.

**Aktuelle Zinsen nach Zinsbindung (Stand 05.07.2026, Topkonditionen, [drklein.de](https://www.drklein.de/aktuelle-bauzinsen.html), Basis 350.000 €):**

| Zinsbindung | Sollzins | Effektivzins |
|---|---|---|
| 5 Jahre | 3,45 % | 3,52 % |
| 10 Jahre | 3,32 % | 3,39 % |
| 15 Jahre | 3,59 % | 3,67 % |
| 20 Jahre | 3,79 % | 3,88 % |
| 30 Jahre | 4,07 % | 4,16 % |

Achtung: "beste Zinsen", nicht Durchschnitt — reale Angebote je nach Bonität/LTV 0,2–0,5 Punkte höher. Empfehlung in Quellen: 10 Jahre = guter Kompromiss. Offizielle Referenz (statt Vermittlerportal): Bundesbank MFI-Zinsstatistik unter [bundesbank.de/statistik-zeitreihen](https://www.bundesbank.de/statistik-zeitreihen).

### 4.2 Restschuld, Sondertilgung, Sonderkündigung — WICHTIGE KORREKTUR

**§ 489 BGB gibt KEIN "5 %/Jahr"-Sondertilgungsrecht** (verbreiteter Irrtum). Sauber trennen:
- **Gesetzliches Sonderkündigungsrecht (§ 489 BGB):** Nach Ablauf von **10 Jahren** seit vollständiger Auszahlung kann der Kreditnehmer mit **6 Monaten Frist ganz oder teilweise** ohne Vorfälligkeitsentschädigung kündigen/ablösen — unabhängig von vereinbarter Zinsbindung und Tilgungshöhe. ([gesetze-im-internet.de/bgb/__489](https://www.gesetze-im-internet.de/bgb/__489.html))
- **Vertragliche Sondertilgung (5 % oder 10 %/Jahr):** optionale, bankabhängige Vertragsklausel, KEIN gesetzlicher Anspruch.
→ Im Rechner beide getrennt modellieren.

### 4.3 Beleihungsauslauf (LTV) und Zinseffekt

Risikoabhängige Marktpraxis (nicht gesetzlich fixiert, bankindividuell):

| LTV | Konditionen |
|---|---|
| bis 60 % | günstigste (minimales Ausfallrisiko) |
| 60–80 % | sehr gut, geringe Aufschläge |
| > 80 % | spürbarer Aufschlag ~+0,1 bis +0,8 Prozentpunkte |
| ≥ 90 % | oft Zusatzsicherheiten/Bürgschaften, deutlich teurer |

Größenordnung: Zinsdifferenz 60 % vs. 90 % LTV ca. 1,3 Prozentpunkte. ([interhyp.de](https://www.interhyp.de/ratgeber/lexikon/beleihungsauslauf/))

**Eigenkapitalbedarf:** Minimum = Kaufnebenkosten aus EK (~10 % des Kaufpreises); empfohlen **20–30 %** EK-Quote für gute Konditionen. 110%-Vollfinanzierung möglich, aber deutlich teurer/riskanter. ([interhyp.de](https://www.interhyp.de/baufinanzierung/eigenkapital/))

### 4.4 Kaufnebenkosten

**Grunderwerbsteuer — alle 16 Bundesländer (Stand 05.07.2026, cross-verifiziert via kommerzielle Portale [finanz-tools.de](https://www.finanz-tools.de/grunderwerbsteuer/bundeslaender-tabelle) u.a.; für Produktivnutzung mit Landesfinanzministerium gegenchecken):**

| Bundesland | Satz | gültig seit |
|---|---|---|
| Bayern | 3,5 % | 1997 |
| **Niedersachsen** | **5,0 %** | 01.01.2014 |
| Baden-Württemberg | 5,0 % | 2011 |
| Rheinland-Pfalz | 5,0 % | 2012 |
| Sachsen-Anhalt | 5,0 % | 2012 |
| Thüringen | 5,0 % | 2024 (von 6,5 % gesenkt) |
| Sachsen | 5,5 % | 2023 |
| Hamburg | 5,5 % | 2023 |
| Bremen | 5,5 % | 01.07.2025 (von 5,0 % erhöht) |
| Berlin | 6,0 % | 2014 |
| Hessen | 6,0 % | 2014 |
| Mecklenburg-Vorpommern | 6,0 % | 2019 |
| **Nordrhein-Westfalen** | **6,5 %** | 01.01.2015 |
| Brandenburg | 6,5 % | 2015 |
| Saarland | 6,5 % | 2015 |
| Schleswig-Holstein | 6,5 % | 2014 |

→ **Fokusregionen: Niedersachsen 5,0 %, NRW 6,5 %.** Auf 300.000 € macht der Unterschied 4.500 € aus (5,0 % = 15.000 € vs. 6,5 % = 19.500 €).

**Notar + Grundbuch:** gesamt ca. **1,5–2 %** des Kaufpreises (Notar ~1,0–1,5 %, Grundbuch ~0,5 %), bundeseinheitlich nach GNotKG, nicht verhandelbar, i.d.R. Käufer. **Zum 01.06.2025 Gebühren erhöht** (Wertgebühren +6 %, Festgebühren +9 %). ([finanztip.de](https://www.finanztip.de/baufinanzierung/notarkosten-haus/))

**Maklerprovision:** Gesetz über die Verteilung der Maklerkosten, in Kraft seit **23.12.2020** — gilt für Kauf von Wohnungen/Einfamilienhäusern durch Verbraucher (nicht unbebaute Grundstücke/Mehrfamilienhäuser/Gewerbe). Beauftragt der Verkäufer, zahlt der Käufer **max. 50 %** (hälftige Teilung = Normalfall). Übliche Gesamtprovision 2026 **5,95–7,14 % inkl. MwSt.**, oft je 3,57 % für Käufer/Verkäufer. ([drklein.de/maklerprovision](https://www.drklein.de/maklerprovision.html), [immobilienscout24.de/bestellerprinzip](https://www.immobilienscout24.de/wissen/verkaufen/bestellerprinzip.html))

**Nebenkosten-Gesamtquote Fokusregionen:** NI ≈ 5,0 % GrESt + ~2 % Notar/GB + ggf. ~3,57 % Makler ≈ **~10,5 %** (ohne Makler) bis **~10,5 %+**. NRW analog mit 6,5 % GrESt ≈ **~8,5 %** ohne Makler, **~12 %** mit Makler.

### 4.5 Leistbarkeit / Affordability

**Haushaltsrechnung:** Nettoeinkommen (alle Haushaltsmitglieder) − laufende Lebenshaltungskosten − bestehende Kreditraten − künftige Bewirtschaftungskosten (Banken kalkulieren pauschal **2,50–3,00 €/m²** Wohnfläche) = Haushaltsüberschuss, muss die Kreditrate decken.

**Bank-Faustregel:** Kreditrate max. **35–40 %** des monatlichen Netto-Haushaltseinkommens; oberhalb 40 % meist keine Zusage. Praxis-Faustregel, keine regulatorische Vorgabe. ([baufimanufaktur.de](https://www.baufimanufaktur.de/fachwissen/warum-die-haushaltsrechnung-beim-hauskauf-deine-finanzierung-entscheidet/))

### 4.6 KfW-Förderprogramme (Stand Anfang Juli 2026)

**Achtung: KfW-Zinsen sind extrem volatil (teils tagesaktuell) — nur als Richtwert mit Datum, im Rechner konfigurierbar, Live-Zins von kfw.de zum Zusagetag.**

| Programm | Zielgruppe | Max. Kredit | Kondition (Stand-Hinweis) |
|---|---|---|---|
| **Wohneigentumsprogramm (124)** | selbstgenutztes Wohneigentum, keine Energieauflagen | 100.000 € | Zins marktorientiert, am Zusagetag fix; ~3,4–3,8 % (10 J.), Drittquelle 3/2026 |
| **Klimafreundlicher Neubau (297/298)** | Neubau/Ersterwerb klimafreundl. Gebäude | 150.000 €/WE | ab 0,6 % (EH40) / ab 1,0 % (EH55), Stand 02.03.2026; EH55 befristet bis 31.12.2026 |
| **Wohngebäude-Kredit Sanierung (261)** | energet. Sanierung Bestand | 120.000–150.000 €/WE | **Tilgungszuschuss 5–45 %**; Zins ~1 Punkt unter Markt (6/2026) |
| **Jung kauft Alt (308)** | Familien ≥1 Kind, Kauf sanierungsbed. Bestand (Klasse F/G/H), Sanierung auf EH85 in 4,5 J. | 100.000–150.000 € (Einkommensgrenze 90.000–110.000 €/J.) | Zins am Zusagetag fix (Quellen widersprüchlich: 0,57 % vs. 1,12 % für 26–35 J.); **Höchstsätze ab 03.08.2026 auf 140.000/160.000/180.000 € angehoben** |
| **Wohneigentum für Familien Neubau (300)** | Familien, Neubau EH40 ohne fossile Heizung | 170.000–270.000 € (Einkommensgrenze 90.000 € +10.000/Kind) | Zins am Zusagetag fix |

Quellen: [kfw.de Wohneigentumsprogramm 124](https://www.kfw.de/inlandsfoerderung/Privatpersonen/Neubau/F%C3%B6rderprodukte/Wohneigentumsprogramm-(124)/), [KfW-PM 02.03.2026](https://www.kfw.de/%C3%9Cber-die-KfW/Newsroom/Aktuelles/Pressemitteilungen-Details_883456.html), [kfw.de 261/262](https://www.kfw.de/inlandsfoerderung/Privatpersonen/Bestehende-Immobilie/F%C3%B6rderprodukte/Bundesf%C3%B6rderung-f%C3%BCr-effiziente-Geb%C3%A4ude-Wohngeb%C3%A4ude-Kredit-(261-262)/), [finanztip.de Jung kauft Alt](https://www.finanztip.de/kfw-foerderung/jung-kauft-alt/), [BMWSB-PM](https://www.bmwsb.bund.de/SharedDocs/pressemitteilungen/DE/2025/10/JkA.html).

---

## 5. Risiken & Fallstricke

### 5.1 Sanierungsstau

Summe unterlassener Reparatur-/Modernisierungsmaßnahmen. **Erkennung:** Fassadenrisse, Dach-/Fensterzustand, Kesselalter, Sicherungskasten, Feuchtigkeit/Salzausblühungen; Wartungsnachweise Heizung + Schornsteinfegerprotokolle anfordern. Energieausweis: Objekte vor 1978 ohne energet. Sanierung brauchen bei ≤4 WE einen Bedarfsausweis. ([immobilienscout24.de](https://www.immobilienscout24.de/wissen/kaufen/so-erkennst-du-sanierungsstau-15-warnsignale.html))

**Kostenrichtwerte 2025 (Fachportale, Orientierung, keine Norm — [demrex.de](https://www.demrex.de/wissen/sanierungskosten-2025-was-kostet-die-modernisierung-pro-m2)):**
- Dach (Dämmung + Neueindeckung): ~200–350 €/m²
- Heizung (Austausch): 18.000–35.000 €
- Fenster: 500–900 €/Fenster (Alters-Indikator U-Wert: Einfachverglasung ~5,0; modern 0,5–1,1 W/(m²K))
- Elektrik: ~80–120 €/m² (Aluminiumleitungen aus 1960/70ern = Brandrisiko, teils Versicherungsausschluss)
- Wasserleitungen: 5.000–12.000 € (80 m²); **Bleileitungen: ab Januar 2026 nach Trinkwasserverordnung stillzulegen/entfernen**

### 5.2 GEG-Sanierungspflichten (Stand 05.07.2026)

- **§ 47 GEG — Dämmung oberste Geschossdecke:** U-Wert ≤ 0,24 W/(m²K), regulär bis 31.12.2015 fällig. ([gesetze-im-internet.de/geg/__47](https://www.gesetze-im-internet.de/geg/__47.html))
- **§ 72 GEG — Betriebsverbot Altkessel:** Öl-/Gaskessel vor 1.1.1991 dürfen nicht mehr betrieben werden; ab 1991 eingebaute nach 30 Jahren. Ausnahmen: Niedertemperatur-/Brennwertkessel, <4 kW oder >400 kW. Fossile Brennstoffe längstens bis 31.12.2044. ([gesetze-im-internet.de/geg/__72](https://www.gesetze-im-internet.de/geg/__72.html))
- **§ 73 GEG — der zentrale Käufer-Fallstrick:** Selbstnutzer von Ein-/Zweifamilienhäusern, die am 1.2.2002 bereits dort wohnten, sind von §§ 69/72-Pflichten befreit. **Bei Eigentümerwechsel beginnt für den NEUEN Eigentümer eine eigene Frist von 2 Jahren ab erstem Eigentumsübergang** — unabhängig vom tatsächlichen Kesselalter. Wird bei Preisverhandlung/Rücklagenplanung oft übersehen. ([gesetze-im-internet.de/geg/__73](https://www.gesetze-im-internet.de/geg/__73.html))
- **Bußgelder:** bis 50.000 €.
- **Novelle GModG (Kabinettsbeschluss 13.5.2026, geplant 1.11.2026):** soll § 72 GEG streichen (Ende der Kesseltauschpflicht). **Noch kein geltendes Recht — vor Nutzung prüfen.** § 47 nicht betroffen. ([bundesregierung.de](https://www.bundesregierung.de/breg-de/aktuelles/neues-gebaeudemodernisierungsgesetz-2430284))

### 5.3 Erbbaurecht

Käufer erwirbt nur befristetes Nutzungsrecht am fremden Grundstück, nicht das Grundstück (Gebäude gehört Erbbauberechtigtem). Rechtsgrundlage ErbbauRG ([gesetze-im-internet.de/erbbauv](https://www.gesetze-im-internet.de/erbbauv/)).
- **Erbbauzins:** ~3–5 % des Bodenwerts p.a. (Kommunen 3–4 %, Kirchen/Private 4–5 %); Anpassung nach § 9a ErbbauRG frühestens alle 3 Jahre.
- **Laufzeit:** üblich 50–99 Jahre.
- **Heimfall/Ablauf:** §§ 2, 32–34 ErbbauRG (Rückübertragung bei Vertragsverletzung); bei Zeitablauf Entschädigung nach § 27 (Mindestentschädigung 2/3 Zeitwert nur bei einkommensschwachen Gruppen zwingend, sonst frei vereinbar).
- **Finanzierbarkeit/Wert:** Banken verlangen meist Restlaufzeit ≥ Kreditlaufzeit + 10 J. (faktisch ≥40 J.); Beleihungswert oft nur 60–80 % → 20–40 % EK nötig. Mit sinkender Restlaufzeit sinkt der Wiederverkaufswert. ([drklein.de](https://www.drklein.de/erbbaurecht-finanzierung-beantragen-faq.html))

### 5.4 Altlasten

**Definition (§ 2 BBodSchG):** Altablagerungen + Altstandorte mit Gefahrenpotenzial. **Prüfung:** Auskunft aus Altlastenkataster bei unterer Bodenschutzbehörde (Landkreis/kreisfreie Stadt); Bebauungsplan, Grundbuch-Altlastenvermerk, historische Nutzung (Tankstelle, Industrie, chem. Reinigung).
- **Haftungsrisiko (wichtigster Fallstrick, § 4 Abs. 3 BBodSchG):** Zustandsstörer-Haftung — auch der **gutgläubige neue Eigentümer** haftet für Sanierung, unabhängig vom Verursacher (BVerfG begrenzt Höhe auf Verkehrswert des unbelasteten Grundstücks). Ausnahme § 4 Abs. 6 nur für Voreigentümer.
- **Vertraglicher Haftungsausschluss** wirkt nur Käufer↔Verkäufer, **NICHT gegenüber der Behörde**. Empfehlung: Bodengutachten vor Kauf. ([gesetze-im-internet.de/bbodschg/__4](https://www.gesetze-im-internet.de/bbodschg/__4.html))

### 5.5 Denkmalschutz

- **Genehmigungspflicht:** jede bauliche Veränderung (auch Fassadenanstrich/Fenstertausch) genehmigungspflichtig bei unterer Denkmalschutzbehörde. Landesrecht → Fristen/Gebühren variieren. Ohne Genehmigung: Bußgelder + Rückbauverfügungen.
- **Steuervorteile Vermieter (§ 7i EStG):** erhöhte AfA **9 % (Jahr + folgende 7 J.) + 7 % (folgende 4 J.)** = 100 % über 12 Jahre. **Zwingend: Abstimmung mit Behörde VOR Maßnahmenbeginn** (nachträglich reicht nicht → Förderung entfällt vollständig). ([gesetze-im-internet.de/estg/__7i](https://www.gesetze-im-internet.de/estg/__7i.html))
- **Selbstnutzer (§ 10f EStG):** 9 % jährlich über 10 Jahre (90 % Gesamtvolumen) als Sonderausgaben.

### 5.6 Mietrecht (für Kapitalanleger)

- **Mietpreisbremse (§ 556d BGB):** in Verordnungsgebieten max. **10 % über ortsüblicher Vergleichsmiete** bei Neuvermietung. Ausnahmen: Erstvermietung nach umfassender Modernisierung, Neubau (Erstbezug nach 1.10.2014). Bundesermächtigung 07/2025 verlängert — Landesverordnungen bis **31.12.2029** möglich.
  - **Niedersachsen:** seit 1.1.2025 **57 Kommunen** (Hannover, Braunschweig, Oldenburg, Göttingen, Wolfsburg, Osnabrück u.a.), verlängert bis 31.12.2029; **Kündigungssperrfrist bei Umwandlung: 5 Jahre** (bis 31.12.2031). ([stk.niedersachsen.de](https://www.stk.niedersachsen.de/startseite/presseinformationen/niedersachsen-verlangert-die-gebietsbestimmung-fur-umwandlungsschutz-und-mietpreisbremse-bis-ende-2029-246795.html))
  - **NRW:** seit 1.3.2025 **57 Kommunen** (Köln, Düsseldorf, Dortmund, Bonn, Aachen, Münster, Bielefeld u.a.); abgesenkte Kappungsgrenze 15 %/3 J.; **Kündigungssperrfrist bei Umwandlung: 8 Jahre**. ([mhkbd.nrw](https://www.mhkbd.nrw/presse-und-medien/pressemitteilungen/aus-18-werden-57-nordrhein-westfalen-weitet-mieterschutzverordnung-aus))
- **Eigenbedarfskündigung (§ 573 Abs. 2 Nr. 2 BGB):** möglich für Vermieter/Familien-/Haushaltsangehörige; BGH verlangt namentliche Benennung + konkrete Gründe. Missbrauch (vorgetäuscht/vorhersehbar verschwiegen) → Schadensersatzrisiko.
- **Kündigungssperrfrist nach Umwandlung (§ 577a BGB):** Grundregel **3 Jahre** ab Veräußerung, per Landesverordnung bis **10 Jahre**. Konkret: 3 J. (Grundregel), 5 J. (NI-Gebiete), 8 J. (NRW-Gebiete), bis 10 J. (z.B. Berlin, München). ([gesetze-im-internet.de/bgb/__577a](https://www.gesetze-im-internet.de/bgb/__577a.html))

### 5.7 Instandhaltungs-/Erhaltungsrücklage bei ETW (WEG)

- **Grundlage:** WEMoG (in Kraft 1.12.2020) ersetzte "Instandhaltungsrückstellung" durch "Erhaltungsrücklage" (§ 19 Abs. 2 Nr. 4 WEG: "Ansammlung einer angemessenen Erhaltungsrücklage"). **Keine gesetzliche Mindesthöhe** — nur "angemessen". ([gesetze-im-internet.de/woeigg/__19](https://www.gesetze-im-internet.de/woeigg/__19.html))
- **Berechnungsansätze:**
  - **Peterssche Formel:** Herstellungskosten × 1,5 ÷ 80 Jahre = jährl. Bedarf, davon 65–70 % auf Gemeinschaftseigentum (Bsp.: 100 m² × 1.500 €/m² → ~1.969 €/Jahr).
  - **§ 28 II. BV:** 7,10 €/m²/J. (<22 J.), 9,00 (≥22 J.), 11,50 (≥32 J.), +1,00 bei Aufzug.
  - Einfache Faustregeln: 0,8–1,0 % der Herstellungskosten p.a. bzw. 1,00–1,50 €/m²/Monat.
- **Zu niedrige Rücklage** → Beitragserhöhung/Sonderumlage bei Großmaßnahmen. **Vor Kauf: Wirtschaftsplan, Versammlungsprotokolle, Rücklagenstand prüfen.** ([immobilienscout24.de](https://www.immobilienscout24.de/wissen/vermieten/instandhaltungsruecklage.html))

### 5.8 Klumpenrisiko

Konzentration auf wenige Objekte/eine Region → Abhängigkeit von lokalen Bedingungen; verschärft durch geringe Immobilien-Liquidität und wenn Gesamtvermögen in einem Objekt gebunden ist. **Risikofaktoren:** politische Eingriffe (Mietpreisbremse, Steuern), regionale Wirtschaftseinbrüche, demografischer Wandel, Zinsänderungsrisiko bei Anschlussfinanzierung, Mietausfall, Sanierungsstau. **Empfehlung:** Streuung über Regionen/Typen; REITs/Fonds als kapitalschonende Ergänzung (Verbraucherzentrale bewertet offene Immobilienfonds kritisch); Puffer mind. 20 % EK-Quote + Liquiditätsreserve 2–3 Nettomonatsgehälter. **Keine belastbare Prozent-Faustregel** für max. Immobilienanteil gefunden — nur qualitative Warnungen. ([immowelt.de](https://www.immowelt.de/ratgeber/news/klumpenrisiko-bei-immobilieninvestitionen-warum-diversifikation-unerlaesslich-ist), [finanztip.de](https://www.finanztip.de/baufinanzierung/eigenkapital-hauskauf/))

---

## Offene Punkte / Vorbehalte für die Wissensbasis

1. **GEG-Novelle (GModG):** § 72 GEG (Kesseltauschpflicht) und die 65%-Heizungsregel stehen vor Änderung (geplant 1.11.2026, noch nicht verabschiedet). Vor Produktivsetzung neu prüfen.
2. **Grunderwerbsteuer-Tabelle:** aus kommerziellen Portalen cross-verifiziert, keine Primärquelle (Landesfinanzministerium) — für rechtsverbindliche Nutzung gegenchecken. Sätze ändern sich per Landesgesetz.
3. **KfW-Konditionen:** extrem volatil (teils tagesaktuell), Drittquellen teils widersprüchlich (Jung kauft Alt 0,57 % vs. 1,12 %). Als konfigurierbaren Default mit sichtbarem Stand-Datum führen, Live-Werte von kfw.de.
4. **Quadratmeterpreis-Portaldaten:** Angebotspreise, nicht Transaktionspreise, methodisch uneinheitlich — mit "Stand: [Datum]"-Tag versehen, regelmäßig neu abrufen.
5. **RSS-Feeds der Portale:** historisch belegt, aktueller Status unklar (vermutl. zugunsten E-Mail-Suchagenten zurückgebaut) — vor Implementierung live verifizieren.
6. **BORIS-API-Verfügbarkeit (WMS/WFS vs. nur Viewer):** uneinheitlich dokumentiert — vor Implementierung direkt bei LGLN (NI) / IT.NRW (NRW) nachfragen.
7. **Mietpreisbremse-Städtelisten (NI/NRW):** aus Sekundärquellen — für rechtsverbindliche Nutzung gegen amtliche Verordnungen (Nds. GVBl., GV. NRW.) verifizieren.

---

## Quellen

### Bereich 1 — Immobilienbewertung
- https://www.gesetze-im-internet.de/immowertv_2022/BJNR280500021.html
- https://www.gesetze-im-internet.de/woflv/BJNR234610003.html
- https://www.gesetze-im-internet.de/geg/
- https://www.bbsr-geg.bund.de/GEGPortal/DE/GEGRegelungen/Gebaeudebestand/Nachruestungspflichten/obersteGeschossdecke/OGD-node.html
- https://www.destatis.de/DE/Presse/Pressemitteilungen/2026/06/PD26_219_61262.html
- https://www.vdpresearch.de/immobilienpreise-steigen-zu-jahresbeginn-2026-weiter/
- https://immobilienmarkt.niedersachsen.de/immobilienpreisindex
- https://www.sparkasse.de/pk/ratgeber/wohnen/immobilie-erwerben/mietrendite.html
- https://www.finanztip.de/baufinanzierung/mietrendite-berechnen/
- https://www.homeday.de/de/immobilienbewertung/vervielfaeltiger-kaufpreisfaktor/
- https://www.immoverkauf24.de/immobilienverkauf/immobilienverkauf-a-z/kaufpreisfaktor/
- https://www.immobilienscout24.de/wissen/vermieten/mietrendite-berechnen.html
- https://www.immobilienscout24.de/wissen/verkaufen/vergleichswertverfahren.html
- https://www.immobilienscout24.de/wissen/verkaufen/ausstattung.html
- https://www.certa-gutachten.de/ratgeber/alterswertminderung-sachwertverfahren-tabelle
- https://www.heid-immobilienbewertung.de/ratgeber/alterswertminderung/
- https://www.korte-immobilien.de/grundstueck-bewerten-was-den-wert-von-bauland-bestimmt/
- https://www.immowelt.de/immobilienpreise/deutschland
- https://www.immowelt.de/immobilienpreise/niedersachsen/ad04de3
- https://www.immowelt.de/immobilienpreise/nordrhein-westfalen/ad04de5
- https://www.mcmakler.de/immobilienpreise/niedersachsen
- https://ivd.net/ivd-wohn-preisspiegel-mitgliederschranke/

### Bereich 2 — Standortqualität + Datenquellen
- https://www.bodenrichtwerte-boris.de/
- https://immobilienmarkt.niedersachsen.de/bodenrichtwerte
- https://www.boris.niedersachsen.de/boris/register
- https://www.boris.nrw.de/
- https://open.nrw/dataset/bodenrichtwerte-nrw-w
- https://www.gars.nrw/dortmund/produkte-do/bodenrichtwert-do
- https://www.gag.niedersachsen.de/startseite/grundstucksmarktberichte/
- https://www.im.nrw/grundstuecksmarktbericht-nordrhein-westfalen-2025-der-markt-erholt-sich-wieder
- https://gutachterausschuss.duesseldorf.de/produkte/grundstuecksmarktbericht
- https://www.gesetze-im-internet.de/bgb/__558d.html
- https://www.bbsr.bund.de/BBSR/DE/forschung/fachbeitraege/wohnen-immobilien/mieten-preise/Mietspiegel/Mietspiegel.html
- https://www.hannover.de/content/download/957295/file/Mietspiegel%202025%20-%20Hannover-final.pdf
- https://www.braunschweig.de/mietspiegel
- https://bauen.osnabrueck.de/de/aktuelles/osnabruecker-mietspiegel-2025-2026-liegt-vor/
- https://www.rheinische-immobilienboerse.de/Mietspiegel_Koeln_2025.AxCMS
- https://miete-duesseldorf.de/
- https://www.dortmund.de/themen/wohnen/mietspiegel/
- https://www.zensus2022.de/
- https://ergebnisse.zensus2022.de/datenbank/online/
- https://www.regionalstatistik.de/genesis/online/
- https://www.destatis.de/EN/Service/OpenData/api-webservice.html
- https://www.statistik.niedersachsen.de/startseite/datenangebote/lsn_online_datenbank/
- https://statistik.nrw/regionale-profile/datendownloads-kommunalprofile
- https://www.empirica-regio.de/produkte/api/
- https://www.empirica-institut.de/nachrichten/details/nachricht/empirica-immobilienpreisindex-i2026/
- https://www.empirica-regio.de/news/251216_cbre_empirica_leerstandsindex_2025/
- https://ec.europa.eu/eurostat/databrowser/view/prc_hpi_q/default/bar
- https://ec.europa.eu/eurostat/web/user-guides/data-browser/api-data-access/api-introduction
- https://www.poschmann-immobilien.com/blog/standortfaktoren-lage/
- https://www.hausundgrund-wesseling.de/aktuelles/einzelansicht/wichtiger-standortfaktor-fuer-wohnimmobilien-so-steht-es-um-die-nahversorgung/

### Bereich 3 — Datenzugriff Listings (Recht)
- https://www.immobilienscout24.de/agb/verbraucher-agb.html
- https://www.immobilienscout24.de/agb/b2b-agb.html
- https://api.immobilienscout24.de/
- https://api.immobilienscout24.de/main/api-products/
- https://www.immowelt.de/immoweltag/agb
- https://www.immowelt.de/meineimmowelt/apinutzungsbedingungen.aspx
- https://themen.kleinanzeigen.de/nutzungsbedingungen/
- https://www.frag-einen-anwalt.de/Kleinanzeigen-Web-Scraping-legal--f349307.html
- https://www.lto.de/recht/hintergruende/h/bgh-urteil-izr22412-screen-scraping-flugdaten-automatisiert-auslesen-ryanair-reiseportal
- https://www.ra-plutte.de/bgh-zum-automatisierten-auslesen-fremder-websites-via-screen-scraping/
- https://www.nbs-partners.de/recht/das-bgh-grundsatzurteil-zum-scraping/
- https://www.gesetze-im-internet.de/urhg/__87a.html
- https://www.dury.de/onlinerecht-blog-menue/731-webscraping-screenscraping-und-das-datenbankurheberrecht
- https://www.wbs.legal/urheberrecht/ist-screen-scraping-legal-15081/
- https://www.gesetze-im-internet.de/stgb/__202a.html
- https://www.noerr.com/de/insights/bgh-urteil-zum-immateriellen-schadensersatz-der-dsgvo-wegen-scraping
- https://www.kanzlei.biz/kein-dsgvo-anspruch-in-scraping-faellen-olg-muenchen-13-02-2025-24-u-3020-24-e/
- https://www.dr-datenschutz.de/die-haushaltsausnahme-der-dsgvo/
- https://www.zvg-portal.de/
- https://www.openimmo.de/
- https://www.immobilienportale.com/2008647-immobiliensuche-per-rss-bei-immobilienscout24/
- https://www.immobilienportale.com/20091616-rss-suchauftrage-bei-immowelt/

### Bereich 4 — Finanzierungsmathematik
- https://www.drklein.de/aktuelle-bauzinsen.html
- https://www.finanztip.de/baufinanzierung/hypothekenzinsen/
- https://www.interhyp.de/ratgeber/lexikon/beleihungsauslauf/
- https://www.interhyp.de/baufinanzierung/eigenkapital/
- https://www.gesetze-im-internet.de/bgb/__489.html
- https://www.finanz-tools.de/grunderwerbsteuer/bundeslaender-tabelle
- https://www.finanz-tools.de/grunderwerbsteuer/nordrhein-westfalen
- https://www.estador.de/grunderwerbsteuer/niedersachsen
- https://www.finanztip.de/baufinanzierung/notarkosten-haus/
- https://www.immoverkauf24.de/immobilienverkauf/immobilienverkauf-a-z/notarkosten-und-grundbuchkosten/
- https://www.drklein.de/maklerprovision.html
- https://www.immobilienscout24.de/wissen/verkaufen/bestellerprinzip.html
- https://www.baufimanufaktur.de/fachwissen/warum-die-haushaltsrechnung-beim-hauskauf-deine-finanzierung-entscheidet/
- https://www.kfw.de/inlandsfoerderung/Privatpersonen/Neubau/F%C3%B6rderprodukte/Wohneigentumsprogramm-(124)/
- https://www.kfw.de/inlandsfoerderung/Privatpersonen/Neubau/F%C3%B6rderprodukte/Klimafreundlicher-Neubau-Wohngeb%C3%A4ude-(297-298)/
- https://www.kfw.de/%C3%9Cber-die-KfW/Newsroom/Aktuelles/Pressemitteilungen-Details_883456.html
- https://www.kfw.de/inlandsfoerderung/Privatpersonen/Bestehende-Immobilie/F%C3%B6rderprodukte/Bundesf%C3%B6rderung-f%C3%BCr-effiziente-Geb%C3%A4ude-Wohngeb%C3%A4ude-Kredit-(261-262)/
- https://www.finanztip.de/kfw-foerderung/jung-kauft-alt/
- https://www.bmwsb.bund.de/SharedDocs/pressemitteilungen/DE/2025/10/JkA.html
- https://www.kfw.de/inlandsfoerderung/Privatpersonen/Neubau/F%C3%B6rderprodukte/Wohneigentum-f%C3%BCr-Familien-(300)/

### Bereich 5 — Risiken & Fallstricke
- https://www.gesetze-im-internet.de/geg/__47.html
- https://www.gesetze-im-internet.de/geg/__72.html
- https://www.gesetze-im-internet.de/geg/__73.html
- https://www.gesetze-im-internet.de/erbbauv/
- https://www.gesetze-im-internet.de/erbbauv/__27.html
- https://www.gesetze-im-internet.de/bbodschg/__2.html
- https://www.gesetze-im-internet.de/bbodschg/__4.html
- https://www.gesetze-im-internet.de/estg/__7i.html
- https://www.gesetze-im-internet.de/estg/__10f.html
- https://www.gesetze-im-internet.de/bgb/__556d.html
- https://www.gesetze-im-internet.de/bgb/__577a.html
- https://www.gesetze-im-internet.de/bgb/__573.html
- https://www.gesetze-im-internet.de/woeigg/__19.html
- https://www.gesetze-im-internet.de/bvo_2/__28.html
- https://www.bundesregierung.de/breg-de/aktuelles/neues-gebaeudemodernisierungsgesetz-2430284
- https://energie-m.de/info/gmodg-2026.html
- https://www.lfu.bayern.de/altlasten/altlastenkataster/altlastenauskuenfte/index.htm
- https://www.stk.niedersachsen.de/startseite/presseinformationen/niedersachsen-verlangert-die-gebietsbestimmung-fur-umwandlungsschutz-und-mietpreisbremse-bis-ende-2029-246795.html
- https://www.mhkbd.nrw/presse-und-medien/pressemitteilungen/aus-18-werden-57-nordrhein-westfalen-weitet-mieterschutzverordnung-aus
- https://www.mieterverein-duesseldorf.de/aktuelles/mietpreisbremse-in-nrw-bis-2029-verlaengert
- https://www.immowelt.de/ratgeber/news/mieten/niedersachsen-erweitert-mietpreisbremse-diese-staedte-und-gemeinden-sind-ab-2025-dabei
- https://www.immobilienscout24.de/wissen/kaufen/so-erkennst-du-sanierungsstau-15-warnsignale.html
- https://www.demrex.de/wissen/sanierungskosten-2025-was-kostet-die-modernisierung-pro-m2
- https://www.goas-altbausanierung.com/blog/wasserleitungen-altbau-austausch-sanierung/
- https://www.heid-immobilienbewertung.de/ratgeber/erbbauzins/
- https://www.drklein.de/erbbaurecht-finanzierung-beantragen-faq.html
- https://kanzlei-franz.com/ratgeber-kaufrecht/altlasten-immobilie-rechte/
- https://www.haufe.de/id/beitrag/erhoehte-absetzungen-nach-7hund7iestg-25-abstimmung-mit-der-denkmalschutzbehoerde-HI2080002.html
- https://www.nwb-experten-blog.de/verlaengerung-der-mietpreisbremse-beschlossen/
- https://www.hvrk-rechtsanwaelte.de/rechtsanwalt/eigenbedarf573/
- https://www.dnotv.de/nachrichten/wemog-tritt-zum-1-12-2020-in-kraft/
- https://www.liebert-roeth.de/de/rechtsgebiete/wohnungseigentumsrecht/erhaltungsruecklage-im-weg-recht
- https://de.wikipedia.org/wiki/Peterssche_Formel
- https://www.immobilienscout24.de/wissen/vermieten/instandhaltungsruecklage.html
- https://www.immowelt.de/ratgeber/news/klumpenrisiko-bei-immobilieninvestitionen-warum-diversifikation-unerlaesslich-ist
- https://www.verbraucherzentrale.de/wissen/geld-versicherungen/sparen-und-anlegen/offene-immobilienfonds-eine-langfristig-sichere-anlage-11429
- https://www.finanztip.de/baufinanzierung/eigenkapital-hauskauf/
