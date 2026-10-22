# PPWR-Assist v0.9.0

Streamlit-Prototyp zur Erfassung von Unternehmen, Verpackungseinheiten und Bestandteilen sowie zur regelbasierten Anzeige von Rollen- und Sonderpfad-Prüfhinweisen.

## Start

Nach dem Entpacken zuerst in den Projektordner `PPWR-Assist-v0.9.0` wechseln und dort die folgenden Befehle ausführen:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Unter Windows kann die virtuelle Umgebung mit `.venv\\Scripts\\activate` aktiviert werden.

## v0.9.0

- Verarbeitet Rollenpflichten und Verpackungs-/Sonderpfade in einem konsolidierten Register. Rollen werden weiterhin von der bestehenden Rollen-Engine geliefert.
- Trennt Anwendbarkeit (`applicable`, `future`, `clarification_required`, `not_applicable`) vom Bearbeitungsstatus (`Klärung erforderlich`, `In Bearbeitung`, `Erfüllt`). „Erfüllt“ ist eine Anwenderbestätigung, keine Zertifizierung.
- Ergänzt erste Pflichttexte für Art. 15, 18, 19 sowie Art. 44/45 je Marktfluss und Zielland. Art. 21 wird vor der Erzeugung von Art.-15-Pflichten als eigener Prüftrigger berücksichtigt.
- Führt Pflichten innerhalb von ID, Sachbereich und Land zusammen und zeigt sie auf VE- und Unternehmensebene. Auslöser, Quellen und offene Tatsachen bleiben sichtbar.
- Ermöglicht Bearbeitungsstatus, Nachweisverweise und Notizen im Register. Diese Angaben bleiben im JSON-Export/Import erhalten.
- Migriert Prüffälle aus v0.8.0 mit Standardwerten für die neuen Felder und Arbeitsstände.

## Übernommene v0.8.0-Funktionen

- Ergänzt die spezifizierten Eingaben für Lebensmittelkontakt, Wiederverwendungssysteme, Tragetaschen, Kompostierbarkeit, Getränkeverpackungen, Gefahrgut, sensible Verpackungskategorien und innovative Verpackungen.
- Fügt ein scope-basiertes Pflichtregister mit stabilen `obligation_id`, `trigger_ids`, Rechtsquellen und Prüfstatus hinzu. Doppelte Art.-29-Hinweise werden innerhalb derselben Verpackungseinheit zusammengeführt.
- Ergänzt JSON-Export und -Import eines Prüffalls. Ältere direkte Prüffall-JSONs werden mit Standardwerten für neue Felder geladen.
- Nutzt das Prüfdatum für ausdrücklich festgelegte Geltungsdaten. Unbekannte Termine bleiben als Prüfhinweis gekennzeichnet.
- Erhält die v0.7.2-Datenstruktur und migriert fehlende Felder mit sicheren Standardwerten.

## Bewusste Grenzen dieser Version

- Das Register ist eine erste Umsetzung der übergebenen Pflichtenarchitektur. Detailtatbestände oder nationale Anforderungen, die in den bereitgestellten Vorgaben nicht vollständig festgelegt sind, bleiben als Klärung markiert.
- Art. 29 Abs. 1–19 ist noch nicht vollständig absatzweise umgesetzt. Rezyklat-, Sammlung/Pfand- und Wiederverwendungspflichten sind teilweise Prüfhinweise.
- Art. 21 fragt den kombinierten Herstellerpflicht-Trigger ab; bei Kleinstunternehmen bleibt die Lieferanten-Ausnahme prüfbedürftig.
- Die Art.-44/45-Ausgabe zeigt die Länderzuordnung pro Marktfluss. Konkrete nationale Register, Meldeverfahren und EPR-Beiträge sind nicht hinterlegt.
- Das Leerraumverhältnis wird nicht berechnet. Die Anwendbarkeit hängt bei gruppierten, Transport- und E-Commerce-Verpackungen außerdem von Befüllung/Verwendung ab; bei unklarer Zuordnung bleibt es ein Klärungspunkt.
- Wiederverwendungssysteme speichern nur Name und Systemart. Governance, Rückführung, Rekonditionierung und Kreislaufdaten sind nicht Teil dieser Version.
- Es gibt keine dauerhafte Speicherung; der Prüffall liegt während der Sitzung in `st.session_state`.
- Der JSON-Export dient der manuellen Sicherung und Übertragung; eine automatische Speicherung ist nicht vorgesehen.

## Prüfung

```bash
python -m py_compile app.py src/models.py src/special_rules.py src/obligation_engine.py src/serialization.py
python -m unittest discover -s tests -v
```

Die Regeltests benötigen nur die Python-Standardbibliothek. Für den Lauf der Oberfläche wird Streamlit benötigt.

## Regelgrundlage

Die Sonderpfade folgen der vom Nutzer bereitgestellten Übergabe „12 Sonderpfade für PPWR-Assist“. Für die Definition der sehr leichten Kunststofftragetasche wird die Wandstärke unter 15 µm verwendet. Die Anwendung ersetzt keine vollständige Rechtsprüfung.
