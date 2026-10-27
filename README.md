# PPWR-Assist v0.8.10

Streamlit-Prototyp für die Erfassung von Unternehmen und Verpackungen sowie die regelbasierte Ableitung von PPWR-Pflichten.

## Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Unter Windows: `.venv\\Scripts\\activate`.

## Änderungen in v0.8.10

- Die Pflicht „Wiederverwendbarkeit der Verpackung“ enthält die Kriterien nach Art. 11 Abs. 1 Buchst. a–i und verlangt deren Nachweis in der technischen Dokumentation.
- Die Art.-11-Kriterien gelten unabhängig von offenem oder geschlossenem Umlaufsystem; die Mindestzahl der Umläufe wird nicht vorweggenommen.
- Systemteilnahme und Anforderungen nach Art. 26–27 und Anhang VI erscheinen als eigene Pflicht, auch wenn noch kein System zugeordnet wurde.
- Offene und geschlossene Umlaufsysteme werden in der Systempflicht unterschieden. Bei offenen Systemen wird der Status eines Systembetreibers als Klärungspunkt ausgewiesen.
- Das Dokumentationsregister leitet Verpackungs- und Systemnachweise getrennt ab.
- Prüffall-Schema bleibt bei `0.8.2` und ist rückwärtskompatibel.

## Änderungen in v0.8.9

- Beim Import werden alte Streamlit-Widget-Zustände verworfen und die importierten Unternehmens-, VE-, Komponenten- und Marktflusswerte neu angezeigt.
- IDs und Nummernkreise werden aus dem geladenen Prüffall wiederhergestellt.
- Ein fehlerhafter Import ersetzt den aktuell geöffneten Prüffall nicht.

## Änderungen in v0.8.8

- Art.-21-Pflichten werden mit eigenständigem Pflichttext und separater Pflicht-ID geführt, getrennt von der allgemeinen Erzeugerpflicht nach Art. 15.
- Das Nachweisregister leitet die Art.-15-Dokumentation weiterhin aus dem Art.-21-Sonderpfad ab.

## Änderungen in v0.8.7

- Der Bereich „Verpackungseinheit löschen“ steht in der VE-Übersicht direkt unter „Grunddaten“ und vor „Bestandteile“.
- Für jeden Marktfluss kann eine eigene Bezeichnung eingegeben werden. Die interne eindeutige Flow-ID und Nummernverwaltung bleiben erhalten.
- Die Bezeichnung wird in Rollen und Pflichten sowie in „Dokumentation & Ausblick“ einschließlich künftiger Anforderungen angezeigt.
- Bestehende Prüffälle ohne Flow-Bezeichnung bleiben importierbar.

## Änderungen in v0.8.6

- Art. 21 wird mit dem amtlichen Artikeltitel angezeigt; die Eingabe prüft den Fall nach Absatz 1.
- Die Kleinstunternehmensregel nach Art. 21 Abs. 2 wird anhand des Unternehmensstatus und der Lieferantenangaben der Verpackungsbestandteile berücksichtigt.
- Bei Kleinstunternehmen mit EU-Verpackungslieferant werden die Erzeugerpflichten nach Art. 15 nicht dem Importeur/Vertreiber zugewiesen. Unklare oder gemischte Lieferantenangaben erzeugen Klärungsbedarf.
- Der Sonderpfad erhält die Überschrift „Art. 21: Übernahme der Erzeugerpflichten nach Art. 15“.
- Datenformat bleibt kompatibel mit Schema-Version `0.8.2`.

## Prüfung

```bash
python -m py_compile app.py src/*.py
python -m unittest discover -s tests -v
```

## Änderungen in v0.8.5

- Die zweispaltige Grundansicht bleibt unverändert.
- Nur der Verpackungsbaum scrollt; „Struktur“ und „Unternehmen“ bleiben außerhalb des Scrollbereichs.
- Nur der jeweilige Registerinhalt scrollt; Überschrift und Registerleiste bleiben darüber sichtbar.
- Die vorherige feste Höhen-/Flex-Regel für ganze Seitencontainer wurde entfernt.
- Auf schmalen Ansichten bleibt der normale Seiten-Scroll erhalten.
- Datenformat bleibt kompatibel mit Schema-Version `0.8.2`.

## Änderungen in v0.8.4

- Oberen Abstand über dem Anwendungstitel reduziert.
- Strukturkopf und Unternehmen bleiben sichtbar; der Verpackungsbaum scrollt separat.
- Überschrift und Register der VE-Detailansicht bleiben beim Scrollen sichtbar; der Detailinhalt scrollt separat.
- Auf schmalen Ansichten bleibt der normale Seiten-Scroll erhalten.
- Datenformat bleibt kompatibel mit Schema-Version `0.8.2`.

## Änderungen in v0.8.3

- Das Register „Dokumentation & Ausblick“ ordnet jeder erzeugten Pflicht eine explizite Dokumentations- oder Klärungsableitung zu, einschließlich Erzeuger-, Importeur-, Vertreiber- und EPR-Pflichten sowie aller derzeit implementierten Sonderpfade.
- Art.-15-Unterlagen werden getrennt als Konformitätsbewertung, technische Dokumentation, EU-Konformitätserklärung, Aufbewahrung und weitere Herstellerpflichten angezeigt.
- Künftige Pflichten bleiben im Ausblick; nicht anwendbare Pflichten und nicht ausgelöste Trigger erzeugen keine Nachweise.
- Neue, noch nicht zugeordnete Pflicht-IDs erscheinen als interner Klärungspunkt, ausdrücklich ohne eine neue gesetzliche Pflicht zu behaupten.
- Das gespeicherte Prüffall-Schema bleibt `0.8.2`; ein Datenformatwechsel ist nicht erforderlich.

## Änderungen in v0.8.2

- Pflichtbewertungen führen Pflicht-ID, Trigger, Rechtsgrundlagen, Geltungsbeginn, Pflichttext und Ausnahmen/Abgrenzungen getrennt.
- Die Geltung künftiger Regeln wird gegen das Prüfstichtagsdatum bewertet. Noch nicht geltende Pflichten erscheinen in „Dokumentation & Ausblick“.
- Dokumentationspunkte werden ausschließlich aus ausgelösten Pflichten abgeleitet. Erzeugerpflichten verknüpfen Konformitätsbewertung, technische Dokumentation (Anhang VII), EU-Konformitätserklärung (Art. 39 / Anhang VIII) und Aufbewahrung.
- PFAS-, Wiederverwendungs-, Kompostierbarkeits-, Leerraum-, Getränke-, Gefahrgut-, Sensitivitäts- und Art.-29-Nachweise erscheinen nur, wenn ein zugehöriger Trigger eine Pflicht erzeugt.
- Unbekannte Geltungsdaten oder nicht ausreichende Fakten bleiben als Klärung sichtbar; Termine werden nicht geschätzt.
- JSON-Import bleibt rückwärtskompatibel; Schema-Version ist `0.8.2`.

## Fachliche Grenzen

Die Regeln und Dokumentationszuordnungen folgen den beiden übergebenen Übergaben „Konzept für die Pflichtenverarbeitung“ und „12 Sonderpfade für PPWR-Assist“. Art. 29 Abs. 1–19 wird als Absatzprüfung ausgelöst; die Anwendung behauptet mangels vollständig festgelegter Einzeltrigger keine abschließende Einzelfallentscheidung. Nationale EPR-Verfahren sowie nicht spezifizierte Durchführungs-/delegierte Rechtsakte sind nicht hinterlegt. Die Software ersetzt keine Rechtsprüfung.

## Prüfung

```bash
python -m py_compile app.py src/*.py
python -m unittest discover -s tests -v
```

Die Tests benötigen die Python-Standardbibliothek. Für die Oberfläche wird Streamlit benötigt.
