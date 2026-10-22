# PPWR-Assist v0.8.2

Streamlit-Prototyp für die Erfassung von Unternehmen und Verpackungen sowie die regelbasierte Ableitung von PPWR-Pflichten.

## Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Unter Windows: `.venv\\Scripts\\activate`.

## Änderungen in v0.8.2

- Pflichtbewertungen führen Pflicht-ID, Trigger, Rechtsgrundlagen, Geltungsbeginn, Pflichttext und Ausnahmen/Abgrenzungen getrennt.
- Die Geltung künftiger Regeln wird gegen das Prüfstichtagsdatum bewertet. Noch nicht geltende Pflichten erscheinen in „Dokumentation & Ausblick“.
- Dokumentationspunkte werden ausschließlich aus ausgelösten Pflichten abgeleitet. Erzeugerpflichten verknüpfen Konformitätsbewertung, technische Dokumentation (Anhang VII), EU-Konformitätserklärung (Art. 39 / Anhang VIII) und Aufbewahrung.
- PFAS-, Wiederverwendungs-, Kompostierbarkeits-, Leerraum-, Getränke-, Gefahrgut-, Sensitivitäts- und Art.-29-Nachweise erscheinen nur, wenn ein zugehöriger Trigger eine Pflicht erzeugt.
- Unbekannte Geltungsdaten oder nicht ausreichende Fakten bleiben als Klärung sichtbar; Termine werden nicht geschätzt.
- JSON-Import bleibt rückwärtskompatibel; Schema-Version ist `0.8.2`.

## Fachliche Grenzen

Die Regeln folgen den beiden übergebenen Übergaben „Konzept für die Pflichtenverarbeitung“ und „12 Sonderpfade für PPWR-Assist“. Art. 29 Abs. 1–19 wird als Absatzprüfung ausgelöst; die Anwendung behauptet mangels vollständig festgelegter Einzeltrigger keine abschließende Einzelfallentscheidung. Nationale EPR-Verfahren sowie nicht spezifizierte Durchführungs-/delegierte Rechtsakte sind nicht hinterlegt. Die Software ersetzt keine Rechtsprüfung.

## Prüfung

```bash
python -m py_compile app.py src/*.py
python -m unittest discover -s tests -v
```

Die Tests benötigen die Python-Standardbibliothek. Für die Oberfläche wird Streamlit benötigt.
