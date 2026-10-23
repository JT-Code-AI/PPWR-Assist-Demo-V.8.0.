"""JSON import/export helpers for portable assessment cases."""

import json
from dataclasses import fields
from datetime import date

from src.models import (
    AssessmentCase,
    Company,
    MarketFlow,
    ObligationAssessment,
    PackagingComponent,
    PackagingUnit,
    ReuseSystem,
)


FORMAT_ID = "ppwr-assist-case"
CURRENT_SCHEMA = "0.8.2"


def _construct(model, data):
    if not isinstance(data, dict):
        raise ValueError(f"{model.__name__} muss ein JSON-Objekt sein.")
    allowed = {item.name for item in fields(model)}
    try:
        return model(**{key: value for key, value in data.items() if key in allowed})
    except TypeError as exc:
        raise ValueError(f"Pflichtangaben für {model.__name__} fehlen.") from exc


def case_to_json(case: AssessmentCase) -> str:
    """Serialize a case with ISO dates and a stable format marker."""
    data = {
        "format": FORMAT_ID,
        "schema_version": CURRENT_SCHEMA,
        "case": {
            "case_id": case.case_id,
            "schema_version": CURRENT_SCHEMA,
            "ruleset_version": case.ruleset_version,
            "created_at": case.created_at.isoformat(),
            "assessment_date": case.assessment_date.isoformat(),
            "company": _company_dict(case.company),
            "obligation_records": [
                {item.name: getattr(record, item.name) for item in fields(ObligationAssessment)}
                for record in case.obligation_records
            ],
        },
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def _company_dict(company):
    result = {item.name: getattr(company, item.name) for item in fields(Company)}
    result["reuse_systems"] = [
        {item.name: getattr(obj, item.name) for item in fields(ReuseSystem)}
        for obj in company.reuse_systems
    ]
    result["packaging_units"] = []
    for unit in company.packaging_units:
        unit_data = {item.name: getattr(unit, item.name) for item in fields(PackagingUnit)}
        unit_data["market_flows"] = [
            {item.name: getattr(flow, item.name) for item in fields(MarketFlow)}
            for flow in unit.market_flows
        ]
        unit_data["components"] = [
            {item.name: getattr(pkg, item.name) for item in fields(PackagingComponent)}
            for pkg in unit.components
        ]
        result["packaging_units"].append(unit_data)
    return result


def case_from_json(raw: str) -> AssessmentCase:
    """Read current or older case JSON, filling absent fields with model defaults."""
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ValueError("Die Datei enthält kein gültiges JSON.") from exc

    if not isinstance(payload, dict):
        raise ValueError("Die Datei muss ein JSON-Objekt enthalten.")
    if payload.get("format") == FORMAT_ID:
        data = payload.get("case")
    else:
        # Accept the earlier direct-case JSON shape as well.
        data = payload
    if not isinstance(data, dict) or not data.get("case_id"):
        raise ValueError("Die Datei enthält keinen gültigen Prüffall.")

    company_data = data.get("company") or {}
    if not isinstance(company_data, dict) or not company_data.get("company_id"):
        raise ValueError("Im Prüffall fehlt die Unternehmens-ID.")

    company_fields = {item.name for item in fields(Company)}
    company_values = {
        key: value for key, value in company_data.items()
        if key in company_fields and key not in {"reuse_systems", "packaging_units"}
    }
    company_values["reuse_systems"] = [
        _construct(ReuseSystem, item)
        for item in company_data.get("reuse_systems", [])
    ]

    units = []
    for unit_data in company_data.get("packaging_units", []):
        if not isinstance(unit_data, dict):
            raise ValueError("Jede Verpackungseinheit muss ein JSON-Objekt sein.")
        unit_fields = {item.name for item in fields(PackagingUnit)}
        unit_values = {
            key: value for key, value in unit_data.items()
            if key in unit_fields and key not in {"market_flows", "components"}
        }
        # v0.8.5 and earlier used a misleading internal field name.
        if (
            "article21_para1_trigger" not in unit_values
            and "article21_manufacturer_trigger" in unit_data
        ):
            unit_values["article21_para1_trigger"] = unit_data[
                "article21_manufacturer_trigger"
            ]
        unit_values["market_flows"] = [
            _construct(MarketFlow, item)
            for item in unit_data.get("market_flows", [])
        ]
        unit_values["components"] = [
            _construct(PackagingComponent, item)
            for item in unit_data.get("components", [])
        ]
        units.append(_construct(PackagingUnit, unit_values))
    company_values["packaging_units"] = units
    company = _construct(Company, company_values)

    case_values = {
        key: value for key, value in data.items()
        if key in {item.name for item in fields(AssessmentCase)}
        and key not in {"company", "created_at", "assessment_date", "obligation_records"}
    }
    for key in ("created_at", "assessment_date"):
        raw_date = data.get(key)
        try:
            case_values[key] = date.fromisoformat(raw_date) if raw_date else date.today()
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Ungültiges Datum im Feld {key}.") from exc
    case_values["company"] = company
    case_values["schema_version"] = CURRENT_SCHEMA
    case_values["obligation_records"] = [
        _construct(ObligationAssessment, item)
        for item in data.get("obligation_records", [])
    ]
    return _construct(AssessmentCase, case_values)
