"""Documentation and outlook are derived from triggered obligations only."""

from __future__ import annotations

from src.models import ObligationAssessment


def build_documentation_register(
    obligations: list[ObligationAssessment],
) -> tuple[list[dict], list[ObligationAssessment]]:
    """Return evidence tasks and future duties; never create a duty of its own."""
    documents: list[dict] = []
    future: list[ObligationAssessment] = []
    def add(parent: ObligationAssessment, title: str, details: list[str] | None = None):
        documents.append({
            "parent": parent,
            "title": title,
            "details": details or [],
        })

    for obligation in obligations:
        if obligation.applicability == "future":
            future.append(obligation)
            continue
        if obligation.applicability == "not_applicable":
            continue

        oid = obligation.obligation_id
        triggers = set(obligation.trigger_ids)

        if oid == "PPWR_ART15_MANUFACTURER_OBLIGATIONS":
            add(obligation, "Konformitätsbewertung nach Art. 38")
            add(obligation, "Technische Dokumentation nach Anhang VII", [
                "Allgemeine Beschreibung und Verwendungszweck",
                "Entwürfe, Fertigungszeichnungen und Materialien",
                "Angewandte Normen und Spezifikationen",
                "Bewertungen nach Art. 6 und 10, soweit für die Verpackung einschlägig",
                "Prüfberichte",
            ])
            add(obligation, "EU-Konformitätserklärung nach Art. 39 / Anhang VIII", [
                "Erst nach nachgewiesener Konformität erstellen.",
            ])
            add(obligation, "Aufbewahrung der technischen Unterlagen und Erklärung", [
                "5 Jahre bei Einwegverpackungen; 10 Jahre bei wiederverwendbaren Verpackungen.",
            ])

        if "SPEC_PFAS" in triggers:
            add(obligation, "PFAS-Nachweis nach Art. 5 Abs. 5", [
                "Prüfergebnis und Nachweis der einschlägigen Grenzwerte in der technischen Dokumentation führen.",
            ])
        if "SPEC_REUSE" in triggers or oid in {
            "PPWR_ART11_REUSABILITY_REVIEW",
            "PPWR_REUSE_SYSTEM_ASSIGNMENT_REVIEW",
            "PPWR_ART26_27_REUSE_SYSTEM_REVIEW",
        }:
            add(obligation, "Nachweise zur Wiederverwendung", [
                "Anforderungen nach Art. 11 sowie, sofern ausgelöst, Art. 26/27 und Anhang VI prüfen.",
                "Detaillierte Systemnachweise bleiben entsprechend der Spezifikation Klärungs-/Bearbeitungspunkt.",
            ])
        if "SPEC_COMPOST" in triggers or "COMPOSTABILITY" in oid:
            add(obligation, "Nachweis zur Kompostierbarkeit", [
                "Nur für ein ausgelöstes EU-Format; bei sonstigem national geregeltem Format Länderregel klären.",
            ])
        if "SPEC_INNOVATIVE" in triggers:
            add(obligation, "Bewertung innovativer Verpackung nach Art. 6 Abs. 10", [
                "Kriterien, technische Begründung, Umweltvorteil, Behördeninformation und Recyclingpfad prüfen.",
            ])
        if "SPEC_VOIDSPACE" in triggers:
            add(obligation, "Nachweis zur Leerraumprüfung nach Art. 24", [
                "Leerraumverhältnis bzw. erforderliches Minimum dokumentieren; Füllmaterial berücksichtigen.",
                "Eine Ausnahme nach Art. 24 Abs. 5 nur bei konkreter Prüfung dokumentieren.",
            ])
        if "SPEC_BEVERAGE" in triggers:
            add(obligation, "Getränkeverpackungsnachweise", [
                "Nur die durch die zugehörigen Pflichten ausgelösten Prüfungen zu Art. 7, 29 und 50 bearbeiten.",
            ])
        if "SPEC_DANGEROUS" in triggers or "SPEC_SENSITIVE" in triggers:
            add(obligation, "Einzelpflichtbezogene Ausnahmeprüfung", [
                "Keine pauschale Befreiung; Ausnahme für jede betroffene Einzelpflicht gesondert prüfen.",
            ])
        if oid == "PPWR_ART29_1_3_INDIVIDUAL_DESIGN_EXCEPTION_REVIEW":
            add(obligation, "Nachweis der individuellen Gestaltung nach Art. 29 Abs. 1–3")
        if "SPEC_HORECA_REFILL_REUSE" in triggers:
            add(obligation, "Nachweise zu Hinweisen und Wiederverwendungsangebot", [
                "Nur soweit die jeweilige Art.-32-/Art.-33-Pflicht ausgelöst ist.",
            ])

    return documents, future
