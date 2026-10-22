# PPWR-Assist v0.8.0

Streamlit-Prototyp zur Erfassung von Unternehmen, Verpackungseinheiten und Bestandteilen sowie zur regelbasierten Anzeige von Rollen- und Sonderpfad-Prüfhinweisen.

## Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Unter Windows kann die virtuelle Umgebung mit `.venv\\Scripts\\activate` aktiviert werden.

## v0.8.0

- Ergänzt die spezifizierten Eingaben für Lebensmittelkontakt, Wiederverwendungssysteme, Tragetaschen, Kompostierbarkeit, Getränkeverpackungen, Gefahrgut, sensible Verpackungskategorien und innovative Verpackungen.
- Fügt ein scope-basiertes Pflichtregister mit stabilen `obligation_id`, `trigger_ids`, Rechtsquellen und Prüfstatus hinzu. Doppelte Art.-29-Hinweise werden innerhalb derselben Verpackungseinheit zusammengeführt.
- Nutzt das Prüfdatum für ausdrücklich festgelegte Geltungsdaten. Unbekannte Termine bleiben als Prüfhinweis gekennzeichnet.
- Erhält die v0.7.2-Datenstruktur und migriert fehlende Felder mit sicheren Standardwerten.

## Bewusste Grenzen dieser Version

- Das Register ist eine erste Pflichtvorschau. Wo die übergebene Spezifikation keine vollständigen Tatbestände oder Detailpflichten enthält, zeigt die Anwendung „Klärung / Prüfung erforderlich“ statt einer abschließenden Rechtsbewertung.
- Art. 29 Abs. 1–19 ist noch nicht vollständig absatzweise umgesetzt. Die allgemeinen Regeln für Rezyklat, Sammlung/Pfand und Wiederverwendung bleiben Prüfhinweise.
- Das Leerraumverhältnis wird nicht berechnet. Die Anwendbarkeit hängt bei gruppierten, Transport- und E-Commerce-Verpackungen außerdem von Befüllung/Verwendung ab; bei unklarer Zuordnung bleibt es ein Klärungspunkt.
- Wiederverwendungssysteme speichern nur Name und Systemart. Governance, Rückführung, Rekonditionierung und Kreislaufdaten sind nicht Teil dieser Version.
- Es gibt keine dauerhafte Speicherung; der Prüffall liegt während der Sitzung in `st.session_state`.

## Prüfung

```bash
python -m py_compile app.py src/models.py src/special_rules.py
python -m unittest discover -s tests -v
```

Die Regeltests benötigen nur die Python-Standardbibliothek. Für den Lauf der Oberfläche wird Streamlit benötigt.

## Regelgrundlage

Die Sonderpfade folgen der vom Nutzer bereitgestellten Übergabe „12 Sonderpfade für PPWR-Assist“. Für die Definition der sehr leichten Kunststofftragetasche wird die Wandstärke unter 15 µm verwendet. Die Anwendung ersetzt keine vollständige Rechtsprüfung.
