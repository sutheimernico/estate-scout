# Datenzugriff auf Immobilien-Listings (rechtliche Lage)

Der kritischste Punkt für ein "Auto-Scouting"-Feature. Grundlage für die Stage-2-Entscheidung
(ADR-0001). Rechtsstand 2026-07-05, keine Rechtsberatung.

## Kernaussage

Automatisiertes Scouting/Scraping von ImmoScout24, Immowelt oder Kleinanzeigen ist für eine
Privatperson **nicht eindeutig verboten, aber riskant** — nicht wegen Strafrecht, sondern wegen der
Kombination aus AGB-Bruch (zivilrechtlich), Datenbankschutz (§ 87a UrhG) bei systematischem
Vollabgriff, aktivem Bot-Schutz (Cloudflare/Akamai) und DSGVO-Exposition durch mitgescrapte
Kontaktdaten Dritter.

## Präzedenzfall

**BGH, 2014-04-30, I ZR 224/12 ("Screen Scraping"/Ryanair):** Automatisiertes Auslesen ist nicht per
se unlauterer Wettbewerb, zulässig solange keine technischen Schutzvorrichtungen umgangen werden, kein
Server überlastet und nichts irreführend dargestellt wird. **Reine AGB-Verstöße allein rechtfertigen
kein gerichtliches Verbot** — sie binden zivilrechtlich (Accountsperrung), begründen aber keinen
eigenständigen Wettbewerbsverstoß. (lto.de, ra-plutte.de)

## Portale

- **ImmoScout24:** AGB Ziff. 8.2 verbietet Bots/Crawler/Data-Mining explizit; Ziff. 8.3 verbietet
  eigene DB-Aufbau. Bot-Schutz: Cloudflare (TLS-/JA3-Fingerprinting, JS-Challenges, Turnstile-CAPTCHAs)
  — echte technische Schutzmaßnahme. API nur für gewerbliche Anbieter/Makler + Content-Partner via
  OAuth. Kein offener Privatpersonen-Zugang.
- **Immowelt:** AGB schließen Crawler/skriptgesteuerte Systeme aus. API nur für Anbieter (eigene
  Objekte). Bot-Schutz praxisüblich.
- **Kleinanzeigen.de:** untersagt automatisierte Mechanismen ohne schriftliche Zustimmung. Bot-Schutz:
  Akamai (blockiert Rechenzentrums-IPs). Keine öffentliche Endnutzer-API.

## Weitere Rechtsdimensionen

- **§ 87a ff. UrhG (Datenbankschutz):** Portale mit tausenden Datensätzen sind geschützte Datenbanken.
  Einzelabruf für Eigenbedarf unkritisch; systematischer Vollabgriff zum DB-Aufbau berührt echtes
  Immaterialgüterrecht (nicht nur AGB).
- **§ 202a/202c StGB:** nur bei Überwindung einer "besonderen Sicherung" (Passwort/Verschlüsselung)
  einschlägig; öffentlich einsehbare Anzeigen erfüllen das i.d.R. nicht. Restrisiko gering.
- **DSGVO:** Anzeigen enthalten personenbezogene Daten (Name/Telefon der Anbieter). Wer diese
  scraped/speichert, wird Verantwortlicher. **Tool-Konsequenz: Kontaktdaten der Anbieter NICHT
  persistent speichern — nur objektbezogene Merkmale** (Preis, Größe, Lage, Ausstattung, Link zum
  Original). Reduziert DSGVO-Exposition erheblich.

## Legale Alternativen

- **zvg-portal.de** (Zwangsversteigerungen): amtliches Justizportal, öffentlich-rechtliche
  Publikationspflicht → rechtlich deutlich unkritischer. Aber: keine API, komplexe Session-Cookies,
  uneinheitliche Exposés je Amtsgericht.
- **RSS-Feeds:** IS24/Immowelt boten historisch offizielle Such-RSS-Feeds — heute vermutlich zugunsten
  von E-Mail-Suchagenten zurückgebaut. Wäre der rechtssicherste automatisierte Weg — vor Implementierung
  live prüfen, ob Endpunkte noch existieren.
- **Manuell/halbautomatisch:** offizielle Merkzettel-/Suchauftrag-Funktionen + E-Mail-Benachrichtigungen
  ins Tool einspeisen (vom Portal vorgesehen); einzelne Objekt-URLs manuell einfügen; Browser-Erweiterung,
  die nur die vom Nutzer selbst geladene Seite ausliest.

## Ampel-Bewertung

- **Grün (unkritisch):** manuelle Nutzung, offizielle Suchagenten/E-Mail, ggf. aktive RSS-Feeds,
  gelegentlicher Einzelabruf.
- **Gelb (Restrisiko):** moderates Abrufen öffentlicher Suchseiten ohne Bot-Schutz-Umgehung, ohne
  Serverlast, ohne Vollspiegelung, ohne personenbezogene Daten. Größtes reales Risiko: Accountsperrung/
  IP-Bann.
- **Rot (klar riskant):** aktive Umgehung von Cloudflare/Akamai, systematischer Vollabgriff,
  gewerbliche Verwertung, dauerhafte Speicherung personenbezogener Verkäuferdaten.

**Rat fürs private Tool:** primär zvg-portal.de + offizielle RSS-/Suchagent-Funktionen; falls
Portal-Abruf, dann ohne Bot-Schutz-Umgehung, niedrige Rate, nur objektbezogene Daten. Rechtlich
wasserdicht ist ausschließlich der manuelle/RSS-/offizielle-API-Weg. **estate-scout verzichtet in allen
Stufen auf AGB-widriges Scraping.**
