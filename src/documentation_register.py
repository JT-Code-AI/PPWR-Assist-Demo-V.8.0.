"""Derive evidence and clarification items exclusively from assessed obligations.

This module does not create legal duties. It maps each obligation produced by
``obligation_engine`` to the evidence or clarification work stated in that
obligation and the supplied PPWR implementation specification.
"""

from __future__ import annotations

from src.models import ObligationAssessment


# Explicit mapping prevents a triggered obligation from silently disappearing
# from the documentation/outlook register. Text stays within the supplied
# obligation descriptions; no unknown thresholds or legal-act dates are added.
OBLIGATION_DOCUMENTS: dict[str, tuple[str, list[str]]] = {
    "PPWR_ART15_MANUFACTURER_OBLIGATIONS": (
        "Erzeugerunterlagen nach Art. 15",
        [
            "Konformitätsbewertung nach Art. 38 dokumentieren.",
            "Technische Dokumentation nach Anhang VII: allgemeine Beschreibung und Verwendungszweck; Entwürfe, Fertigungszeichnungen und Materialien; angewandte Normen/Spezifikationen; erforderliche Bewertungen, insbesondere Art. 6, 10 und 11 soweit einschlägig; Prüfberichte.",
            "EU-Konformitätserklärung nach Art. 39 / Anhang VIII erst nach nachgewiesener Konformität erstellen.",
            "Technische Unterlagen und Erklärung aufbewahren: 5 Jahre bei Einweg-, 10 Jahre bei wiederverwendbaren Verpackungen.",
            "Weitere in der Pflicht genannte Herstelleranforderungen (Kennzeichnung, Rückverfolgbarkeit, Korrekturmaßnahmen) bearbeiten.",
        ],
    ),
    "PPWR_ART18_IMPORTER_OBLIGATIONS": (
        "Importeurprüfung und Unterlagen nach Art. 18",
        [
            "Vorhandensein der Konformitätsbewertung, technischen Dokumentation und einschlägigen Konformitätsnachweise des Herstellers prüfen.",
            "Importeurangaben und Begleitunterlagen prüfen.",
            "Lagerung und Beförderung sowie erforderliche Folgemaßnahmen bei Zweifeln/Nichtkonformität dokumentieren.",
            "Konformitätserklärung und technische Unterlagen für die vorgeschriebene Aufbewahrungsfrist bereithalten.",
        ],
    ),
    "PPWR_ART19_DISTRIBUTOR_OBLIGATIONS": (
        "Vertreiberprüfung nach Art. 19",
        [
            "Registrierung der EPR-pflichtigen Person, Kennzeichnung und einschlägige Erfüllung der Hersteller-/Importeurpflichten prüfen.",
            "Bei begründeten Konformitätszweifeln die Klärung bzw. Herstellung der Konformität vor Bereitstellung dokumentieren.",
        ],
    ),
    "PPWR_ART44_PRODUCER_REGISTRATION": (
        "Herstellerregistrierung im Zielmitgliedstaat",
        ["Registrierung und nationale Verfahrensanforderungen je ausgelöstem Zielmitgliedstaat klären und belegen."],
    ),
    "PPWR_ART45_EPR_COUNTRY_REQUIREMENTS": (
        "EPR-Unterlagen im Zielmitgliedstaat",
        ["Anwendbares nationales EPR-System, zuständige Stelle und konkrete Anforderungen je Zielmitgliedstaat klären; Erfüllungsnachweise dort zuordnen."],
    ),
    "PPWR_ART5_5_PFAS_COMPLIANCE": (
        "PFAS-Nachweis nach Art. 5 Abs. 5",
        ["PFAS-Konformität und die im Pflichttext genannten Grenzwerte 25 ppb, 250 ppb und 50 ppm prüfen; erforderliche Nachweise in der technischen Dokumentation führen."],
    ),
    "PPWR_ART11_REUSABILITY_REVIEW": (
        "Wiederverwendbarkeit nach Art. 11",
        ["Erfüllung der Anforderungen an Wiederverwendbarkeit prüfen und die hierfür erforderlichen Nachweise in der technischen Dokumentation führen. Die Auswahl ‚vorgesehen‘ ist kein Erfüllungsnachweis."],
    ),
    "PPWR_REUSE_SYSTEM_ASSIGNMENT_REVIEW": (
        "Zuordnung zu einem Wiederverwendungssystem",
        ["Fehlende Zuordnung klären; die Pflichtanzeige nach Art. 26/27 und Anhang VI bleibt davon abhängig."],
    ),
    "PPWR_ART26_27_REUSE_SYSTEM_REVIEW": (
        "Wiederverwendungssystem nach Art. 26/27 und Anhang VI",
        ["Für das zugeordnete System einschlägige Anforderungen prüfen. Detaillierte Governance-, Rückführungs- und Rekonditionierungsdaten sind laut Vorgabe zurückgestellt."],
    ),
    "PPWR_ART25_ANNEX_V_VERY_LIGHT_BAG": (
        "Kunststofftragetaschen nach Art. 25 / Anhang V",
        ["Wandstärke und Anwendbarkeit des Verbots sehr leichter Kunststofftragetaschen prüfen; eine gegebenenfalls beanspruchte Hygiene- oder Lebensmittelverschwendungsausnahme belegen."],
    ),
    "PPWR_ART9_COMPOSTABLE_FORMAT": (
        "Kompostierbarkeit des EU-Formats nach Art. 9",
        ["Für das ausgelöste EU-Format die einschlägigen Kompostierbarkeitsanforderungen und erforderlichen technischen Nachweise bearbeiten."],
    ),
    "PPWR_NATIONAL_COMPOSTABILITY_REVIEW": (
        "Nationale Regelung zur Kompostierbarkeit",
        ["Einschlägige Länderregelung für das ausgewählte sonstige Format klären; diese Pflicht erzeugt keinen EU-Nachweis ohne Rechtsgrundlage."],
    ),
    "PPWR_COMPOSTABILITY_CLASSIFICATION_REVIEW": (
        "Kompostierbarkeitsformat klären",
        ["Formatangabe klären. Dies ist ein interner Klärungspunkt und kein zusätzlicher gesetzlicher Nachweis."],
    ),
    "PPWR_ART7_BEVERAGE_RECYCLATE_REVIEW": (
        "Rezyklatvorgaben für Getränkeverpackungen nach Art. 7",
        ["Einschlägige Vorgaben anhand von Verpackungsmaterial und Verpackungsart prüfen; verwendete Materialangaben und zugrunde gelegte Nachweise zuordnen."],
    ),
    "PPWR_ART29_REUSE_REQUIREMENTS_REVIEW": (
        "Mehrwegvorgaben nach Art. 29",
        ["Art. 29 Abs. 1–19 absatzweise anhand von Verpackungsformat, Marktfluss und Absatz prüfen; einschlägige Prüfergebnisse und Nachweise festhalten.", "Getränke-Verkaufsverpackungen für Abs. 6 ff. sowie Umverpackungen für Abs. 5 berücksichtigen, wenn der jeweilige Trigger vorliegt."],
    ),
    "PPWR_ART50_BEVERAGE_COLLECTION_REVIEW": (
        "Sammlung, Pfand und Rücknahme nach Art. 50",
        ["Anhand der Getränkeverpackungsart und des Marktflusses klären, welche Anforderungen zu Sammlung, Pfand oder Rücknahme einschlägig sind; zugehörige Nachweise zuordnen."],
    ),
    "PPWR_ART6_10_INNOVATIVE_PACKAGING_REVIEW": (
        "Prüfung innovativer Verpackung nach Art. 6 Abs. 10",
        ["Kriterien, technische Begründung, Umweltvorteil, Behördeninformation und Recyclingpfad prüfen und belegen. Die Auswahl begründet keine automatische Ausnahme."],
    ),
    "PPWR_SENSITIVE_PACKAGING_EXCEPTION_REVIEW": (
        "Ausnahmeprüfung für sensible Verpackung",
        ["Für jede betroffene Einzelpflicht prüfen und dokumentieren, ob für die konkret erfasste Kategorie eine gesetzliche Ausnahme gilt. Keine pauschale Befreiung."],
    ),
    "PPWR_SENSITIVE_CATEGORY_CLASSIFICATION_REVIEW": (
        "Sensible Verpackungskategorie klären",
        ["Kategorie klären; bis dahin keine Ausnahme annehmen. Interner Klärungspunkt, kein zusätzlicher gesetzlicher Nachweis."],
    ),
    "PPWR_DANGEROUS_GOODS_EXCEPTION_REVIEW": (
        "Gefahrgutausnahme je Einzelpflicht prüfen",
        ["Tatsächliche Gefahrgutverwendung und eine konkrete Ausnahme je betroffener Einzelpflicht prüfen. UN-Zulassung allein genügt nicht; keine pauschale Befreiung."],
    ),
    "PPWR_ART24_1_VOIDSPACE_50_PERCENT": (
        "Leerraumprüfung bis höchstens 50 % nach Art. 24",
        ["Leerraumverhältnis einschließlich Füllmaterial dokumentieren.", "Geltungsbeginn: 1. Januar 2030 oder drei Jahre nach Inkrafttreten des Durchführungsrechtsakts, je nachdem, welcher Zeitpunkt später liegt; unbekanntes Datum nicht schätzen.", "Eine Ausnahme nach Art. 24 Abs. 5 nur nach konkreter Prüfung dokumentieren."],
    ),
    "PPWR_ART24_SALES_MINIMUM_VOIDSPACE": (
        "Leerraum bei Verkaufsverpackungen nach Art. 24",
        ["Erforderliches Minimum und Leerraum einschließlich Füllmaterial dokumentieren.", "Eine Ausnahme nach Art. 24 Abs. 5 nur nach konkreter Prüfung dokumentieren."],
    ),
    "PPWR_ART24_FILLING_STATUS_REVIEW": (
        "Befüllung/Verwendung für Art. 24 klären",
        ["Klären und festhalten, ob das Unternehmen die Verpackung im Sinne von Art. 24 befüllt/verwendet. Interner Klärungspunkt, kein zusätzlicher gesetzlicher Nachweis."],
    ),
    "PPWR_PRIMARY_PRODUCTION_ROLE_REVIEW": (
        "Primärproduktionsverpackung: Rolle und Marktfluss klären",
        ["Erzeuger-/Herstellerrolle und Marktfluss anhand der erfassten führenden Verpackungsart prüfen. Befüllen allein begründet nicht automatisch die Erzeugerrolle."],
    ),
    "PPWR_ART29_1_3_INDIVIDUAL_DESIGN_EXCEPTION_REVIEW": (
        "Individuelle Gestaltung nach Art. 29 Abs. 1–3",
        ["Individuelle Gestaltung für große Maschinen, Ausrüstung oder Rohstoffe nachweisen. Die mögliche Ausnahme ist auf Art. 29 Abs. 1–3 begrenzt und keine allgemeine PPWR-Befreiung."],
    ),
    "PPWR_ART32_OWN_CONTAINERS": (
        "Eigene Behältnisse der Verbraucher nach Art. 32",
        ["Gut sichtbare Hinweise sowie die Gleichbehandlung bei Preis und Bedingungen prüfen; die Annahme eigener Behältnisse darf nicht verweigert werden."],
    ),
    "PPWR_ART33_REUSE_OFFER": (
        "Wiederverwendungsangebot nach Art. 33 Abs. 1–4",
        ["Wiederverwendungsangebot innerhalb eines Wiederverwendungssystems und Hinweise prüfen; Preis und Bedingungen dürfen nicht ungünstiger sein. Kleinstunternehmen-Ausnahme nur nach geklärtem Status berücksichtigen."],
    ),
    "PPWR_ART33_5_REUSE_10_PERCENT_EFFORT": (
        "Bemühenspflicht zu Mehrwegangeboten nach Art. 33 Abs. 5",
        ["Ab 2030 die Bemühenspflicht zu wiederverwendbarer Verpackung bearbeiten und die zugrunde gelegten Maßnahmen festhalten; Kleinstunternehmen-Ausnahme nur nach geklärtem Status berücksichtigen."],
    ),
}


def build_documentation_register(
    obligations: list[ObligationAssessment],
) -> tuple[list[dict], list[ObligationAssessment]]:
    """Return evidence/clarification tasks and future duties from obligations."""
    documents: list[dict] = []
    future: list[ObligationAssessment] = []

    for obligation in obligations:
        if obligation.applicability == "future":
            future.append(obligation)
            continue
        if obligation.applicability == "not_applicable":
            continue

        mapping = OBLIGATION_DOCUMENTS.get(obligation.obligation_id)
        if mapping is None:
            # A defensive, explicitly non-legal clarification item ensures a
            # new engine obligation is visible until it receives a reviewed map.
            title = f"Pflichtzuordnung prüfen: {obligation.title}"
            details = [
                "Interner Klärungspunkt: Dokumentationsableitung fachlich ergänzen. Dies erzeugt keine zusätzliche gesetzliche Pflicht."
            ]
        else:
            title, details = mapping

        if obligation.obligation_id == "PPWR_ART15_MANUFACTURER_OBLIGATIONS":
            documents.extend([
                {
                    "parent": obligation,
                    "title": "Konformitätsbewertung nach Art. 38",
                    "details": ["Konformitätsbewertung durchführen oder durchführen lassen und Prüfergebnis dokumentieren."],
                },
                {
                    "parent": obligation,
                    "title": "Technische Dokumentation nach Anhang VII",
                    "details": [details[1]],
                },
                {
                    "parent": obligation,
                    "title": "EU-Konformitätserklärung nach Art. 39 / Anhang VIII",
                    "details": [details[2]],
                },
                {
                    "parent": obligation,
                    "title": "Aufbewahrung der technischen Unterlagen und Erklärung",
                    "details": [details[3]],
                },
                {
                    "parent": obligation,
                    "title": "Weitere Herstellerpflichten nach Art. 15",
                    "details": [details[4]],
                },
            ])
            continue

        documents.append({"parent": obligation, "title": title, "details": details})

    return documents, future
