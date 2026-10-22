# Änderungen

## v0.9.0

- Gemeinsames Pflichtenregister für bestehende Rollenbewertungen sowie VE-/PKG-/Unternehmenspfade.
- Pflichtanwendbarkeit und Bearbeitungsstatus getrennt; Nachweise und Notizen werden pro Pflichtinstanz gespeichert und exportiert.
- Art. 21 wird vor der Pflichtgenerierung abgefragt und in Art.-15-Pflichten dedupliziert; Art.-21(2)-Kleinstunternehmensfall bleibt ohne ausreichende Lieferantendaten in Klärung.
- Erste Pflichtenanzeigen für Art. 15, 18, 19, 44 und 45; EPR-Pflichten bleiben je Mitgliedstaat/Marktfluss getrennt.
- Deduplizierung nach Pflicht-ID, sachlichem Geltungsbereich und Land; Anzeige im konsolidierten Register und auf VE-Ebene.
- Prüffallimport aus älteren JSON-Ständen migriert neue Datenfelder und erhält gespeicherte Pflichtbearbeitung.
- 18 automatisierte Tests bestehen.

## v0.8.0

- Neue Sonderpfad-Datenfelder mit migrationssicheren Standardwerten.
- Pflichtvorschau mit Geltungsstatus, Rechtsgrundlagen, Auslösern und eindeutigen Pflicht-IDs.
- HORECA-Hinweise auf Unternehmensebene unter Wiederverwendung bestehender Tätigkeits-, Gastgewerbe- und Kleinstunternehmensangaben.
- PFAS-Hinweis auf PKG-Ebene; Wiederverwendungssysteme als Unternehmens-Hintergrundobjekte.
- Keine pauschale PPWR-Ausnahme bei Gefahrgut oder sensiblen Verpackungen.
- Spezialisierte Prüfhinweise für Leerraum, Getränke, Kompostierbarkeit, Tragetaschen, Primärproduktion und innovative Verpackungen.
- Zusätzliche Prüfung der individuellen Gestaltungsausnahme ausschließlich für Art. 29 Abs. 1–3.
- Neu: zehn automatisierte Regeltests.
- JSON-Export/Import für Prüffälle, einschließlich Laden älterer direkter Prüffall-JSONs mit migrierten Standardwerten; drei Serialisierungstests ergänzt.

## Weiterhin offen

- Vollständige Detailpflichten für Art. 11, 26–27, 29 Abs. 1–19, 7 und 50.
- Berechnung des Leerraumverhältnisses und dynamische Ermittlung des Termins aus dem Durchführungsrechtsakt.
- Technische Dokumentation, Registrierungs-/Meldeprozesse und Konformitätserklärung.
