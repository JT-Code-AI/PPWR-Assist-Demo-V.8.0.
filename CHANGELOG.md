# Änderungen

## v0.8.7

- VE-Löschen-Bereich in „Übersicht“ direkt unter „Grunddaten“ und vor „Bestandteile“ verschoben.
- Marktflüsse erhalten eine frei bearbeitbare Bezeichnung; FLOW-IDs und Nummernverwaltung bleiben unverändert.
- Marktflussbezeichnungen erscheinen in Hersteller-Rollen, Rollen- und Pflichten, Dokumentation und Ausblick.
- Bestehende Prüffälle behalten ihre Marktflüsse; bei fehlender Bezeichnung wird ein leerer Standardwert ergänzt.

## v0.8.6

- Art.-21-Eingabe mit dem amtlichen Titel „Fälle, in denen die Pflichten der Erzeuger auch für Importeure und Vertreiber gelten“ beschriftet; Abfrage erläutert nun ausdrücklich Art. 21 Abs. 1.
- Art. 21 Abs. 2 wird vor der Zuweisung der Erzeugerpflichten geprüft: Kleinstunternehmen mit Verpackungslieferant in der EU erhalten die Art.-15-Pflicht nicht selbst zugewiesen.
- Lieferantenstandorte werden aus den Verpackungsbestandteilen ausgewertet; unklare oder gemischte Lieferantenlagen bleiben als Klärungsbedarf sichtbar.
- Art.-21-Sonderpfad wird in „Rollen & Pflichten“ mit einer eigenen, treffenderen Überschrift angezeigt.
- Prüffall-Schema bleibt rückwärtskompatibel bei `0.8.2`.

## v0.8.5

- Zweispaltige Grundansicht wiederhergestellt; feste Höhenregeln für ganze Spalten entfernt.
- Scrollbereich auf den Verpackungsbaum bzw. den aktiven Registerinhalt begrenzt.
- Strukturkopf/Unternehmen sowie Detailüberschrift/Registerleiste bleiben außerhalb dieser Scrollbereiche sichtbar.
- Schmale Ansichten behalten den normalen Seiten-Scroll.
- Prüffall-Schema bleibt rückwärtskompatibel bei `0.8.2`.

## v0.8.4

- Oberen Seitenabstand reduziert.
- Strukturüberschrift und Unternehmenskarte fixiert; Verpackungsbaum separat scrollbar.
- VE-Überschrift und Registerleiste fixiert; Detailbereich separat scrollbar.
- Schmale Ansichten verwenden normalen Seiten-Scroll.
- Prüffall-Schema bleibt rückwärtskompatibel bei `0.8.2`.

## v0.8.3

- Dokumentationsregister explizit für alle in v0.8.2 erzeugten Pflicht-IDs ergänzt.
- Erzeuger-, Importeur-, Vertreiber-, Herstellerregistrierungs- und EPR-Pflichten leiten jeweils passende Dokumentations- oder Klärungspunkte ab.
- Art.-15-Unterlagen getrennt dargestellt; die EU-Konformitätserklärung bleibt an den Nachweis der Konformität gebunden.
- Sonderpfade leiten Nachweise nur aus ausgelösten Pflichten ab; zukünftige Anforderungen bleiben im Ausblick.
- Unbekannte Pflicht-IDs werden als interne Zuordnungsklärung sichtbar, ohne eine neue gesetzliche Pflicht zu erzeugen.
- Prüffall-Schema bleibt rückwärtskompatibel bei `0.8.2`.

## v0.8.2

- Strukturierte Pflichtfelder inklusive Ausnahmen/Abgrenzungen ergänzt.
- Zukunftspflichten anhand des Prüfstichtags datiert und aus „Rollen & Pflichten“ nach „Dokumentation & Ausblick“ verlagert.
- Dokumentationsnachweise werden aus den tatsächlich ausgelösten Pflichten abgeleitet.
- Erzeugerunterlagen nach Art. 38/39 und Anhang VII sowie Aufbewahrungsfristen werden im Nachweisregister geführt.
- JSON-Schema auf `0.8.2` gesetzt; ältere Prüffälle bleiben importierbar.
- 19 automatisierte Tests.

## v0.8.1

Vorherige Zwischenversion, intern als v0.9.0 bezeichnet.
