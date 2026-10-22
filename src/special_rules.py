"""Rule-based special-path register for PPWR-Assist v0.8.0.

The rule texts and triggers follow the supplied PPWR handover markdown.
Where that specification leaves a duty's detailed applicability open, the
output remains a review item instead of asserting a legal result.
"""

from __future__ import annotations

from datetime import date
from typing import Any


COMPOST_FORMATS = {
    "tea_coffee_bag",
    "single_serve_unit",
    "produce_sticker",
}

SENSITIVE_CATEGORIES = {
    "medicinal_primary": "Primärverpackung eines Arzneimittels",
    "medicinal_outer": "Äußere Umhüllung eines Arzneimittels zur Qualitätserhaltung",
    "medical_device": "Kontaktempfindliche Verpackung eines Medizinprodukts",
    "ivd": "Verpackung eines In-vitro-Diagnostikums (IVD)",
    "special_food": "Kontaktempfindliche Verpackung für Säuglings-/Kleinkindernahrung oder Lebensmittel für besondere medizinische Zwecke",
}


def _as_date(value: Any) -> date:
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return date.today()


def _dated_status(assessment_date: date, effective_date: date) -> str:
    return "applicable" if assessment_date >= effective_date else "upcoming"


def build_obligations(case: Any) -> list[dict[str, Any]]:
    """Build scoped notices/duties, merging duplicate obligations per scope."""
    company = case.company
    assessment_date = _as_date(case.assessment_date)
    items: dict[tuple[str, str], dict[str, Any]] = {}

    def add(
        obligation_id: str,
        scope_id: str,
        scope_label: str,
        title: str,
        status: str,
        summary: str,
        legal_basis: list[str],
        trigger_id: str | None,
        effective_date: str | None = None,
        notes: list[str] | None = None,
    ) -> None:
        key = (obligation_id, scope_id)
        if key not in items:
            items[key] = {
                "obligation_id": obligation_id,
                "scope_id": scope_id,
                "scope_label": scope_label,
                "title": title,
                "status": status,
                "summary": summary,
                "legal_basis": [],
                "trigger_ids": [],
                "effective_date": effective_date,
                "notes": [],
            }
        item = items[key]
        if summary != item["summary"]:
            extra = "Zusätzlicher Prüfhinweis: " + summary
            if extra not in item["notes"]:
                item["notes"].append(extra)
        if status == "review" or item["status"] == "review":
            item["status"] = "review"
        elif status == "applicable" or item["status"] == "applicable":
            item["status"] = "applicable"
        for source in legal_basis:
            if source not in item["legal_basis"]:
                item["legal_basis"].append(source)
        if trigger_id and trigger_id not in item["trigger_ids"]:
            item["trigger_ids"].append(trigger_id)
        for note in notes or []:
            if note not in item["notes"]:
                item["notes"].append(note)

    # HORECA is an enterprise-level trigger: end-recipient delivery + hospitality.
    horeca = (
        "direct_end_recipient" in (company.activities or [])
        and "hospitality_takeaway" in (company.sector_triggers or [])
    )
    if horeca:
        end_date = date(2027, 2, 12)
        add(
            "PPWR_ART32_OWN_CONTAINERS",
            company.company_id,
            "Unternehmen",
            "Eigene Behältnisse der Verbraucher",
            _dated_status(assessment_date, end_date),
            "Eigene Behältnisse der Verbraucher dürfen nicht verweigert werden. Gut sichtbare Hinweise sind erforderlich; es dürfen keine höheren Preise oder ungünstigeren Bedingungen gelten.",
            ["PPWR Art. 32"],
            "SPEC_HORECA_REFILL_REUSE",
            end_date.isoformat(),
        )
        art33_date = date(2028, 2, 12)
        art33_status = _dated_status(assessment_date, art33_date)
        if company.micro_enterprise_status == "yes":
            art33_status = "exempt"
        elif company.micro_enterprise_status == "clarification_required":
            art33_status = "review"
        add(
            "PPWR_ART33_REUSE_OFFER",
            company.company_id,
            "Unternehmen",
            "Wiederverwendungsangebot im Gastgewerbe",
            art33_status,
            "Angebot innerhalb eines Wiederverwendungssystems; Hinweise sowie keine höheren Preise oder ungünstigeren Bedingungen. Kleinstunternehmen-Ausnahme berücksichtigen.",
            ["PPWR Art. 33 Abs. 1–4"],
            "SPEC_HORECA_REFILL_REUSE",
            art33_date.isoformat(),
            ["Kleinstunternehmenstatus ist noch zu klären." ]
            if company.micro_enterprise_status == "clarification_required"
            else [],
        )
        art33_5_date = date(2030, 1, 1)
        art33_5_status = _dated_status(assessment_date, art33_5_date)
        if company.micro_enterprise_status == "yes":
            art33_5_status = "exempt"
        elif company.micro_enterprise_status == "clarification_required":
            art33_5_status = "review"
        add(
            "PPWR_ART33_5_REUSE_10_PERCENT_EFFORT",
            company.company_id,
            "Unternehmen",
            "Bemühenspflicht zu Mehrwegangeboten ab 2030",
            art33_5_status,
            "Ab 2030 sollen Endvertreiber sich bemühen, 10 % der Produkte in wiederverwendbarer Verpackung zum Verkauf anzubieten.",
            ["PPWR Art. 33 Abs. 5"],
            "SPEC_HORECA_REFILL_REUSE",
            art33_5_date.isoformat(),
            ["Kleinstunternehmenstatus ist noch zu klären." ]
            if company.micro_enterprise_status == "clarification_required"
            else [],
        )

    filling_activity = bool(
        set(company.activities or []).intersection(
            {"manufacture_and_pack", "fill_purchased_packaging"}
        )
    )

    for ve in company.packaging_units or []:
        scope = ve.ve_id
        label = ve.name or ve.ve_id
        types = set(ve.packaging_type_candidates or ve.packaging_types or [])

        for pkg in ve.components or []:
            if pkg.food_contact:
                add(
                    "PPWR_ART5_5_PFAS_COMPLIANCE",
                    pkg.pkg_id,
                    f"{label} / {pkg.name or pkg.pkg_id}",
                    "PFAS-Konformität bei Lebensmittelkontakt",
                    "applicable",
                    "PFAS-Konformität nachweisen und die Grenzwerte 25 ppb, 250 ppb und 50 ppm nach PPWR Art. 5 Abs. 5 prüfen; erforderliche Nachweise in der technischen Dokumentation führen.",
                    ["PPWR Art. 5 Abs. 5–6", "Kommissionsleitlinie C/2026/3084, S. 11–12"],
                    "SPEC_PFAS",
                )

        if ve.intended_for_reuse:
            add(
                "PPWR_ART11_REUSABILITY_REVIEW",
                scope,
                label,
                "Wiederverwendbarkeit der Verpackung",
                "review",
                "Die Auswahl aktiviert den Wiederverwendungspfad. Sie bedeutet nicht, dass die Anforderungen an Wiederverwendbarkeit bereits erfüllt sind.",
                ["PPWR Art. 11"],
                "SPEC_REUSE",
                notes=["Detaillierte Nachweise werden in dieser Version nicht erhoben."],
            )
            if not ve.reuse_system_id:
                add(
                    "PPWR_REUSE_SYSTEM_ASSIGNMENT_REVIEW",
                    scope,
                    label,
                    "Zuordnung zu einem Wiederverwendungssystem klären",
                    "review",
                    "Für die vorgesehene Wiederverwendung ist noch kein System zugeordnet.",
                    ["PPWR Art. 26–27, Anhang VI"],
                    "SPEC_REUSE",
                )
        system = next(
            (s for s in (company.reuse_systems or []) if s.system_id == ve.reuse_system_id),
            None,
        )
        if system and ve.intended_for_reuse:
            add(
                "PPWR_ART26_27_REUSE_SYSTEM_REVIEW",
                scope,
                label,
                "Anforderungen an das Wiederverwendungssystem",
                "review",
                "Pflichten aus Art. 26 und 27 sowie Anhang VI sind für das zugeordnete System zu prüfen.",
                ["PPWR Art. 26–27", "PPWR Anhang VI"],
                "SPEC_REUSE_SYSTEM",
                notes=[f"Systemart: {system.system_type}. Detaillierte Governance-, Rückführungs- und Rekonditionierungsdaten sind zurückgestellt."],
            )

        if ve.is_plastic_carrier_bag:
            bag_date = date(2030, 1, 1)
            add(
                "PPWR_ART25_ANNEX_V_VERY_LIGHT_BAG",
                scope,
                label,
                "Sehr leichte Kunststofftragetaschen",
                _dated_status(assessment_date, bag_date),
                "Ab 1. Januar 2030 sind sehr leichte Kunststofftragetaschen (Wandstärke unter 15 µm) nach Art. 25 und Anhang V verboten. Ausnahmen: erforderliche Hygienezwecke sowie Verkaufsverpackungen für lose Lebensmittel, wenn dies Lebensmittelverschwendung verhindert.",
                ["PPWR Art. 25", "PPWR Anhang V", "PPWR Art. 3 Abs. 1 Nr. 57"],
                "SPEC_BAG",
                bag_date.isoformat(),
            )

        if ve.compostable_format in COMPOST_FORMATS:
            compost_date = date(2028, 2, 12)
            add(
                "PPWR_ART9_COMPOSTABLE_FORMAT",
                scope,
                label,
                "Kompostierbarkeit des Verpackungsformats",
                _dated_status(assessment_date, compost_date),
                "Für das ausgewählte Format ist der Kompostierbarkeitspfad nach Art. 9 Abs. 1 zu beachten.",
                ["PPWR Art. 9 Abs. 1"],
                "SPEC_COMPOST",
                compost_date.isoformat(),
            )
        elif ve.compostable_format == "other_national":
            add(
                "PPWR_NATIONAL_COMPOSTABILITY_REVIEW",
                scope,
                label,
                "Nationale Regelung zur Kompostierbarkeit prüfen",
                "review",
                "Das ausgewählte sonstige Format kann national geregelt sein; die einschlägigen Länderregeln sind zu prüfen.",
                ["PPWR Art. 9"],
                "SPEC_COMPOST",
            )
        elif ve.compostable_format == "clarification_required":
            add(
                "PPWR_COMPOSTABILITY_CLASSIFICATION_REVIEW",
                scope,
                label,
                "Kompostierbarkeitsformat klären",
                "review",
                "Das Format wurde als klärungsbedürftig erfasst.",
                ["PPWR Art. 9"],
                "SPEC_COMPOST",
            )

        if ve.is_beverage_packaging:
            add(
                "PPWR_ART7_BEVERAGE_RECYCLATE_REVIEW",
                scope,
                label,
                "Rezyklatvorgaben für Getränkeverpackungen prüfen",
                "review",
                "Die einschlägigen Rezyklatvorgaben nach Art. 7 sind anhand des Verpackungsmaterials und der Verpackungsart zu prüfen.",
                ["PPWR Art. 7"],
                "SPEC_BEVERAGE",
                notes=[f"Erfasste Getränkeverpackungsart: {ve.beverage_packaging_type}."],
            )
            add(
                "PPWR_ART29_REUSE_REQUIREMENTS_REVIEW",
                scope,
                label,
                "Wiederverwendungsanforderungen für Getränkeverpackungen prüfen",
                "review",
                "Art. 29 Abs. 6 ff. ist anhand von Getränkekategorie, Marktfluss und 3-Liter-Prüfpunkt zu prüfen. Die 3-Liter-Grenze wird in dieser Version nicht als Eingabefeld erhoben.",
                ["PPWR Art. 29 Abs. 6 ff."],
                "SPEC_BEVERAGE",
                notes=[f"Erfasste Getränkeverpackungsart: {ve.beverage_packaging_type}."],
            )
            add(
                "PPWR_ART50_BEVERAGE_COLLECTION_REVIEW",
                scope,
                label,
                "Sammlung, Pfand und Rücknahme bei Getränkeverpackungen prüfen",
                "review",
                "Die einschlägigen Anforderungen zu Sammlung, Pfand oder Rücknahme nach Art. 50 sind anhand der Getränkeverpackungsart und des Marktflusses zu prüfen.",
                ["PPWR Art. 50"],
                "SPEC_BEVERAGE",
                notes=[f"Erfasste Getränkeverpackungsart: {ve.beverage_packaging_type}."],
            )

        if ve.potentially_innovative:
            add(
                "PPWR_ART6_10_INNOVATIVE_PACKAGING_REVIEW",
                scope,
                label,
                "Innovative Verpackung prüfen",
                "review",
                "Die Auswahl aktiviert nur einen Prüfpfad und begründet keine automatische Ausnahme. Kriterien, technische Begründung, Umweltvorteil, Behördeninformation und Recyclingpfad sind nach Art. 6 Abs. 10 zu prüfen.",
                ["PPWR Art. 6 Abs. 10"],
                "SPEC_INNOVATIVE",
            )

        if ve.sensitive_packaging_category in SENSITIVE_CATEGORIES:
            add(
                "PPWR_SENSITIVE_PACKAGING_EXCEPTION_REVIEW",
                scope,
                label,
                "Pflichtbezogene Ausnahme für sensible Verpackung prüfen",
                "review",
                "Keine Gesamtbefreiung: Für jede einschlägige Einzelpflicht ist zu prüfen, ob die konkrete Kategorie eine Ausnahme vorsieht.",
                ["PPWR Art. 6–7"],
                "SPEC_SENSITIVE",
                notes=[SENSITIVE_CATEGORIES[ve.sensitive_packaging_category]],
            )
        elif ve.sensitive_packaging_category == "clarification_required":
            add(
                "PPWR_SENSITIVE_CATEGORY_CLASSIFICATION_REVIEW",
                scope,
                label,
                "Sensible Verpackungskategorie klären",
                "review",
                "Die Kategorie ist noch nicht geklärt; eine Ausnahme darf nicht pauschal angenommen werden.",
                ["PPWR Art. 6–7"],
                "SPEC_SENSITIVE",
            )

        if ve.used_for_dangerous_goods:
            add(
                "PPWR_DANGEROUS_GOODS_EXCEPTION_REVIEW",
                scope,
                label,
                "Gefahrgutausnahme je Einzelpflicht prüfen",
                "review",
                "Tatsächliche Verwendung für Gefahrgut ist erfasst. Es gibt keinen globalen Befreiungsschalter; Ausnahmen sind für jede einschlägige Einzelpflicht gesondert zu prüfen. Eine UN-Zulassung allein löst diesen Pfad nicht aus.",
                ["PPWR Art. 2 Abs. 2", "PPWR Art. 6", "PPWR Art. 7", "PPWR Art. 29"],
                "SPEC_DANGEROUS",
            )

        # Art. 24: packaging type is taken from the existing classification;
        # filling status is only inferred from existing, explicit activity fields.
        voidspace_types = types.intersection({"grouped", "transport"})
        ecommerce = ve.is_ecommerce_packaging == "yes"
        if voidspace_types or ecommerce or "sales" in types:
            filled = filling_activity or ve.self_filling_sales_grouped == "yes"
            if filled:
                if voidspace_types or ecommerce:
                    add(
                        "PPWR_ART24_1_VOIDSPACE_50_PERCENT",
                        scope,
                        label,
                        "Höchstwert für Leerraum bei Um-, Transport- und E-Commerce-Verpackungen",
                        "scheduled_review",
                        "Der Leerraumanteil darf höchstens 50 % betragen. Anwendbar ab 1. Januar 2030 oder drei Jahre nach Inkrafttreten der Durchführungsrechtsakte, je nachdem, welcher Zeitpunkt später liegt. Füllmaterial zählt zum Leerraum.",
                        ["PPWR Art. 24 Abs. 1", "PPWR Art. 24 Abs. 5"],
                        "SPEC_VOIDSPACE",
                        notes=["Der spätere Termin hängt vom Durchführungsrechtsakt ab und wird hier nicht vorweggenommen.", "Ausnahme nach Art. 24 Abs. 5 im Einzelfall prüfen."],
                    )
                if "sales" in types:
                    sales_date = date(2028, 2, 12)
                    add(
                        "PPWR_ART24_SALES_MINIMUM_VOIDSPACE",
                        scope,
                        label,
                        "Leerraum bei Verkaufsverpackungen auf das erforderliche Minimum begrenzen",
                        _dated_status(assessment_date, sales_date),
                        "Ab 12. Februar 2028 ist der Leerraum bei Verkaufsverpackungen auf das erforderliche Minimum zu begrenzen. Füllmaterial zählt zum Leerraum.",
                        ["PPWR Art. 24 Abs. 1", "PPWR Art. 24 Abs. 5"],
                        "SPEC_VOIDSPACE",
                        sales_date.isoformat(),
                        ["Ausnahme nach Art. 24 Abs. 5 im Einzelfall prüfen."],
                    )
            else:
                add(
                    "PPWR_ART24_FILLING_STATUS_REVIEW",
                    scope,
                    label,
                    "Befüllung/Verwendung für Leerraumprüfung klären",
                    "review",
                    "Eine relevante Verpackungsart ist erfasst; die vorhandenen Angaben belegen aber nicht eindeutig, ob das Unternehmen die Verpackung im Sinne von Art. 24 befüllt/verwendet.",
                    ["PPWR Art. 24"],
                    "SPEC_VOIDSPACE",
                )

        if ve.primary_packaging_type == "primary_production":
            add(
                "PPWR_PRIMARY_PRODUCTION_ROLE_REVIEW",
                scope,
                label,
                "Primärproduktionsverpackung: Erzeuger-/Herstellerrolle prüfen",
                "review",
                "Der Pfad wird aus der führenden Verpackungsart abgeleitet. Er beeinflusst insbesondere Rollen- und Marktflussprüfungen und erzeugt keine pauschale Zusatzpflicht. Befüllen allein führt nicht automatisch zur Erzeugerrolle.",
                ["PPWR Art. 3 Abs. 1 Nr. 4, 13, 15"],
                "SPEC_PRIMARY",
            )

        # Art. 29 overview is a review item; detailed paragraph-by-paragraph
        # logic for paragraphs 1–19 remains a subsequent implementation step.
        art29_candidate = bool(
            "transport" in types
            or ("sales" in types and "transport" in ve.packaging_functions)
            or "grouped" in types
            or (ve.is_beverage_packaging and "sales" in types)
        )
        if art29_candidate:
            art29_triggers = []
            if ve.intended_for_reuse:
                art29_triggers.append("SPEC_REUSE")
            if ve.is_beverage_packaging:
                art29_triggers.append("SPEC_BEVERAGE")
            if not art29_triggers:
                art29_triggers = [None]
            for trigger_id in art29_triggers:
                add(
                    "PPWR_ART29_REUSE_REQUIREMENTS_REVIEW",
                    scope,
                    label,
                    "Mehrwegvorgaben nach Art. 29 absatzweise prüfen",
                    "review",
                    "Art. 29 Abs. 1–19 ist anhand von Verpackungsformat, Marktfluss und Absatz zu prüfen. Umverpackungen sind zusätzlich für Abs. 5 zu berücksichtigen; Getränke-Verkaufsverpackungen für Abs. 6 ff.",
                    ["PPWR Art. 29 Abs. 1–19"],
                    trigger_id,
                )
            if ve.individually_designed_large_goods:
                add(
                    "PPWR_ART29_1_3_INDIVIDUAL_DESIGN_EXCEPTION_REVIEW",
                    scope,
                    label,
                    "Individuelle Gestaltung für große Maschinen/Ausrüstung/Rohstoffe nachweisen",
                    "review",
                    "Die Ausnahme ist nur für Art. 29 Abs. 1–3 zu prüfen. Die Auswahl bewirkt keine allgemeine PPWR-Befreiung; der Nachweis der individuellen Gestaltung ist zu berücksichtigen.",
                    ["PPWR Art. 29 Abs. 1–3"],
                    None,
                )

    return sorted(items.values(), key=lambda item: (item["scope_label"], item["obligation_id"]))
