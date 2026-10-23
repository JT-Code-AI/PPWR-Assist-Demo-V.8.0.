"""Consolidated assessment register for role and packaging duties.

The engine consumes the existing role results; it does not recalculate roles.
Unresolved facts remain visible as clarification items.
"""

from datetime import date

from src.models import (
    AssessmentCase,
    ObligationAssessment,
    ObligationDefinition,
    RoleAssessment,
)
from src.special_rules import build_obligations


RULES_APPLY_FROM = date(2026, 8, 12)
WORK_STATUSES = ("Klärung erforderlich", "In Bearbeitung", "Erfüllt")
ARTICLE21_DUTY_TITLE = "Art. 21: Übernahme der Erzeugerpflichten nach Art. 15"

ROLE_DEFINITIONS = {
    "producer": ObligationDefinition(
        obligation_id="PPWR_ART15_MANUFACTURER_OBLIGATIONS",
        title="Pflichten des Erzeugers nach Art. 15",
        trigger_type="role",
        trigger_ids=["ROLE_PRODUCER"],
        legal_basis=["PPWR Art. 15", "PPWR Art. 38–39", "PPWR Anhang VII"],
        applicable_from=RULES_APPLY_FROM.isoformat(),
        time_rule="Anwendung der PPWR ab 12.08.2026.",
        requirement_text=(
            "Vor dem Inverkehrbringen die Konformitätsbewertung durchführen oder "
            "durchführen lassen, die technische Dokumentation nach Anhang VII "
            "erstellen und bei nachgewiesener Konformität die EU-Konformitätserklärung "
            "nach Art. 39 ausstellen. Die weiteren Herstellerpflichten, insbesondere "
            "Kennzeichnung, Rückverfolgbarkeit und Korrekturmaßnahmen, sind ebenfalls "
            "zu bearbeiten."
        ),
        exceptions=["Die EU-Konformitätserklärung wird erst nach nachgewiesener Konformität ausgestellt."],
    ),
    "importer": ObligationDefinition(
        obligation_id="PPWR_ART18_IMPORTER_OBLIGATIONS",
        title="Pflichten des Importeurs nach Art. 18",
        trigger_type="role",
        trigger_ids=["ROLE_IMPORTER"],
        legal_basis=["PPWR Art. 18"],
        applicable_from=RULES_APPLY_FROM.isoformat(),
        time_rule="Anwendung der PPWR ab 12.08.2026.",
        requirement_text=(
            "Vor dem Inverkehrbringen prüfen, ob der Hersteller die erforderliche "
            "Konformitätsbewertung und technische Dokumentation erstellt hat und die "
            "Verpackung die einschlägigen Anforderungen erfüllt. Importeurangaben, "
            "Begleitunterlagen sowie ordnungsgemäße Lagerung und Beförderung sicherstellen; "
            "Konformitätserklärung und technische Unterlagen für die vorgeschriebene "
            "Aufbewahrungsfrist bereithalten."
        ),
        exceptions=["Bei begründeten Zweifeln oder Nichtkonformität gelten die in Art. 18 geregelten Folgemaßnahmen; Einzelfallprüfung erforderlich."],
    ),
    "distributor": ObligationDefinition(
        obligation_id="PPWR_ART19_DISTRIBUTOR_OBLIGATIONS",
        title="Pflichten des Vertreibers nach Art. 19",
        trigger_type="role",
        trigger_ids=["ROLE_DISTRIBUTOR"],
        legal_basis=["PPWR Art. 19"],
        applicable_from=RULES_APPLY_FROM.isoformat(),
        time_rule="Anwendung der PPWR ab 12.08.2026.",
        requirement_text=(
            "Vor der Bereitstellung mit der gebotenen Sorgfalt prüfen, ob die "
            "EPR-pflichtige Person registriert ist, die Kennzeichnung vorliegt und "
            "Hersteller bzw. Importeur ihre einschlägigen Pflichten erfüllen. Bei "
            "begründeten Konformitätszweifeln die Verpackung nicht bereitstellen, bis "
            "der Sachverhalt geklärt oder die Konformität hergestellt ist."
        ),
        exceptions=["Bei begründeten Konformitätszweifeln darf die Verpackung bis zur Klärung oder Herstellung der Konformität nicht bereitgestellt werden."],
    ),
}


def _applicability(role_status: str) -> str:
    if role_status == "yes":
        return "applicable"
    if role_status == "no":
        return "not_applicable"
    return "clarification_required"


def _merge(target: dict, item: ObligationAssessment) -> None:
    key = (item.obligation_id, item.scope_type, item.scope_id, item.country)
    current = target.get(key)
    if current is None:
        target[key] = item
        return
    for trigger in item.trigger_ids:
        if trigger not in current.trigger_ids:
            current.trigger_ids.append(trigger)
    if any(trigger.startswith("ROLE_ART21_") for trigger in item.trigger_ids):
        current.title = ARTICLE21_DUTY_TITLE
    for source in item.sources:
        if source not in current.sources:
            current.sources.append(source)
    for fact in item.missing_facts:
        if fact not in current.missing_facts:
            current.missing_facts.append(fact)
    for note in item.rule_notes:
        if note not in current.rule_notes:
            current.rule_notes.append(note)
    for exception in item.exceptions:
        if exception not in current.exceptions:
            current.exceptions.append(exception)
    if item.applicability == "applicable":
        current.applicability = "applicable"
    elif (
        item.applicability == "clarification_required"
        and current.applicability not in {"applicable", "future"}
    ):
        current.applicability = "clarification_required"
    if item.depends_on_act:
        current.depends_on_act = True
        current.time_rule = item.time_rule or current.time_rule
    if item.requirement_text and item.requirement_text not in current.requirement_text:
        current.requirement_text += "\n\n" + item.requirement_text
    if item.notes and item.notes not in current.notes:
        current.notes = "\n".join(filter(None, (current.notes, item.notes)))


def _scope_for_special(case: AssessmentCase, scope_id: str) -> tuple[str, str]:
    if scope_id == case.company.company_id:
        return "company", ""
    for ve in case.company.packaging_units:
        if scope_id == ve.ve_id:
            return "VE", ""
        if any(pkg.pkg_id == scope_id for pkg in ve.components):
            return "PKG", ""
        if any(flow.flow_id == scope_id for flow in ve.market_flows):
            flow = next(flow for flow in ve.market_flows if flow.flow_id == scope_id)
            return "flow", flow.target_country
    return "VE", ""


def _date_applicability(assessment_date: date) -> str:
    return "applicable" if assessment_date >= RULES_APPLY_FROM else "future"


def _article21_microenterprise_exception(company, ve) -> str:
    """Return yes/no/clarification for the Art. 21(2) supplier rule.

    Art. 21(2) requires both a micro-enterprise and a packaging supplier
    established in the Union. Supplier countries are recorded on VE components.
    """
    if company.micro_enterprise_status == "no":
        return "no"
    if company.micro_enterprise_status != "yes":
        return "clarification_required"

    suppliers = [
        component for component in ve.components
        if component.procurement_type != "self_manufactured"
    ]
    if not suppliers:
        return "clarification_required"

    countries = [component.supplier_country for component in suppliers]
    if any(country in {"", "clarification_required", None} for country in countries):
        return "clarification_required"
    in_union = [country != "THIRD_COUNTRY" for country in countries]
    if all(in_union):
        return "yes"
    if not any(in_union):
        return "no"
    # A VE with suppliers inside and outside the Union needs component-level review.
    return "clarification_required"


def build_register(
    case: AssessmentCase,
    role_results: list[RoleAssessment] | None = None,
) -> list[ObligationAssessment]:
    """Build one register, deduplicated per ID + scope + country."""
    merged: dict[tuple[str, str, str, str], ObligationAssessment] = {}
    assessment_date = case.assessment_date

    for item in build_obligations(case):
        scope_type, country = _scope_for_special(case, item["scope_id"])
        old_status = item["status"]
        applicability = {
            "applicable": "applicable",
            "upcoming": "future",
            "scheduled_review": "future",
            "review": "clarification_required",
            "exempt": "not_applicable",
        }.get(old_status, "clarification_required")
        effective = item.get("effective_date")
        depends = bool(item.get("depends_on_act", old_status == "scheduled_review"))
        if old_status == "scheduled_review":
            applicability = "future"
        elif old_status in {"applicable", "upcoming"} and not item.get("effective_date"):
            applicability = _date_applicability(assessment_date)
        missing = (
            list(item.get("notes", [])) or [item.get("summary", "")]
            if applicability == "clarification_required" else []
        )
        assessment = ObligationAssessment(
            obligation_id=item["obligation_id"],
            title=item["title"],
            scope_type=scope_type,
            scope_id=item["scope_id"],
            country=country,
            trigger_ids=list(item.get("trigger_ids", [])),
            sources=list(item.get("legal_basis", [])),
            applicability=applicability,
            requirement_text=item.get("summary", ""),
            applicable_from=effective,
            depends_on_act=depends,
            time_rule=(
                item.get("time_rule") or "Geltungsbeginn absatzweise anhand des Durchführungs-/delegierten Rechtsakts klären; kein unbekannter Termin wird geschätzt."
                if depends else (f"PPWR-Anwendung ab {effective}." if effective else "Geltungsbeginn in der übergebenen Spezifikation nicht festgelegt." )
            ),
            missing_facts=missing,
            rule_notes=list(item.get("notes", [])),
            exceptions=list(item.get("exceptions", [])),
        )
        _merge(merged, assessment)

    by_scope = {(r.role_key, r.scope): r for r in role_results or []}
    for ve in case.company.packaging_units:
        role_by_key = {
            key: by_scope.get((key, ve.ve_id))
            for key in ("producer", "importer", "distributor")
        }
        for role_key, definition in ROLE_DEFINITIONS.items():
            result = role_by_key.get(role_key)
            if result is None or result.status == "no":
                continue
            status = _applicability(result.status)
            applicability = status if status == "clarification_required" else _date_applicability(assessment_date)
            _merge(merged, ObligationAssessment(
                obligation_id=definition.obligation_id,
                title=definition.title,
                scope_type="VE",
                scope_id=ve.ve_id,
                trigger_ids=definition.trigger_ids.copy(),
                sources=definition.legal_basis.copy(),
                applicability=applicability,
                requirement_text=definition.requirement_text,
                applicable_from=RULES_APPLY_FROM.isoformat(),
                exceptions=definition.exceptions.copy(),
                missing_facts=[result.summary] if status == "clarification_required" else [],
                notes=("Die Rollenbewertung ist noch nicht abschließend." if status == "clarification_required" else ""),
            ))

        # Article 21(1) can attribute producer duties to an importer/distributor.
        # Paragraph 2 is evaluated before creating that duty: a micro-enterprise
        # with a Union-established packaging supplier is not the producer for Art. 15.
        trigger_value = ve.article21_para1_trigger
        if trigger_value == "no":
            continue
        micro_exception = _article21_microenterprise_exception(case.company, ve)
        for role_key in ("importer", "distributor"):
            result = role_by_key.get(role_key)
            if result is None or result.status == "no":
                continue
            # Under Art. 21(2), the packaging supplier is deemed the producer.
            # Therefore no Art. 15 producer duty is assigned to this company,
            # even if the Art. 21(1) trigger itself has not yet been resolved.
            if micro_exception == "yes":
                continue

            definition = ROLE_DEFINITIONS["producer"]
            unresolved = (
                trigger_value != "yes"
                or micro_exception == "clarification_required"
                or result.status == "clarification_required"
            )
            missing_facts = []
            if trigger_value != "yes":
                missing_facts.append(
                    "Klären, ob der Importeur oder Vertreiber Verpackungen unter eigenem Namen/eigener Marke in Verkehr bringt oder sie so verändert, dass die Konformität beeinträchtigt werden kann (Art. 21 Abs. 1)."
                )
            if micro_exception == "clarification_required":
                if case.company.micro_enterprise_status != "yes":
                    missing_facts.append(
                        "Kleinstunternehmensstatus des Importeurs oder Vertreibers klären (Art. 21 Abs. 2)."
                    )
                missing_facts.append(
                    "Klären, ob der Verpackungslieferant in der Union ansässig ist (Art. 21 Abs. 2)."
                )
            if result.status == "clarification_required":
                missing_facts.append(result.summary)

            _merge(merged, ObligationAssessment(
                obligation_id=definition.obligation_id,
                title=ARTICLE21_DUTY_TITLE,
                scope_type="VE",
                scope_id=ve.ve_id,
                trigger_ids=[f"ROLE_ART21_{role_key.upper()}"],
                sources=["PPWR Art. 21 Abs. 1–2", *definition.legal_basis],
                applicability=(
                    "clarification_required" if unresolved
                    else _date_applicability(assessment_date)
                ),
                requirement_text=definition.requirement_text,
                applicable_from=RULES_APPLY_FROM.isoformat(),
                exceptions=[
                    *definition.exceptions,
                    "Nach Art. 21 Abs. 2 gilt bei einem Kleinstunternehmen mit einem in der Union ansässigen Verpackungslieferanten der Lieferant als Erzeuger für die Zwecke des Art. 15.",
                ],
                missing_facts=missing_facts,
                notes=(
                    "Die Zuordnung der Erzeugerpflichten nach Art. 21 ist noch nicht abschließend."
                    if unresolved else ""
                ),
            ))

    # EPR duties stay separate for each relevant Member State / market flow.
    for result in role_results or []:
        if result.role_key != "manufacturer" or result.status == "no":
            continue
        flow_id = result.scope
        flow = next(
            (f for ve in case.company.packaging_units for f in ve.market_flows if f.flow_id == flow_id),
            None,
        )
        country = flow.target_country if flow else result.country
        applicability = _applicability(result.status)
        if applicability != "clarification_required":
            applicability = _date_applicability(assessment_date)
        common = dict(
            scope_type="company",
            scope_id=case.company.company_id,
            country=country,
            trigger_ids=["ROLE_MANUFACTURER_EPR", flow_id],
            applicable_from=RULES_APPLY_FROM.isoformat(),
            applicability=applicability,
            missing_facts=[result.summary] if applicability == "clarification_required" else [],
        )
        _merge(merged, ObligationAssessment(
            obligation_id="PPWR_ART44_PRODUCER_REGISTRATION",
            title="Herstellerregistrierung im Zielmitgliedstaat",
            sources=["PPWR Art. 44"],
            requirement_text=(
                "Vor der erstmaligen Bereitstellung oder dem Auspacken ohne Endnutzereigenschaft "
                "im jeweiligen Mitgliedstaat die erforderliche Registrierung im dortigen "
                "Herstellerregister sicherstellen. Nationale Angaben und Verfahren sind "
                "gesondert zu klären."
            ),
            **common,
        ))
        _merge(merged, ObligationAssessment(
            obligation_id="PPWR_ART45_EPR_COUNTRY_REQUIREMENTS",
            title="Erweiterte Herstellerverantwortung im Zielmitgliedstaat",
            sources=["PPWR Art. 45"],
            requirement_text=(
                "Die Anforderungen der erweiterten Herstellerverantwortung im Zielmitgliedstaat "
                "ermitteln und erfüllen. Umfang, Meldungen und Beiträge richten sich nach dem "
                "anwendbaren nationalen EPR-System."
            ),
            missing_facts=(
                [*common["missing_facts"], "Nationale EPR-Regelung und zuständige Stelle ermitteln."]
                if applicability == "clarification_required"
                else ["Nationale EPR-Regelung, zuständige Stelle und konkrete Anforderungen ermitteln."]
            ),
            **{k: v for k, v in common.items() if k != "missing_facts"},
        ))

    # Preserve the user's work status, evidence and notes across recalculation.
    stored = {
        (r.obligation_id, r.scope_type, r.scope_id, r.country): r
        for r in case.obligation_records
    }
    results = []
    for key, item in merged.items():
        progress = stored.get(key)
        if progress:
            item.status = progress.status if progress.status in WORK_STATUSES else "Klärung erforderlich"
            item.evidence = list(progress.evidence)
            item.notes = "\n".join(filter(None, (item.notes, progress.notes)))
        else:
            item.status = "Klärung erforderlich"
        results.append(item)
    return sorted(results, key=lambda x: (x.scope_type, x.country, x.scope_id, x.obligation_id))
