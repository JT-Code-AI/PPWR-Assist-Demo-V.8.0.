from dataclasses import dataclass, field
from datetime import date
from typing import Optional


# =========================================================
# Verpackungsbestandteil
# =========================================================

@dataclass
class PackagingComponent:
    pkg_id: str

    name: str = ""
    material: str = ""
    material_subtypes: list[str] = field(default_factory=list)
    weight_g: Optional[float] = None

    # Beschaffung
    procurement_type: str = "clarification_required"

    supplier_name: str = ""
    supplier_country: str = "clarification_required"
    supplier_country_other: str = ""

    # Gegenstand der Lieferung / Herstellung
    supplied_object_type: str = "clarification_required"

    # Kann der Gegenstand bereits für sich eine
    # Verpackungsfunktion erfüllen?
    independent_packaging_function: str = (
        "clarification_required"
    )

    # Wer fügt den Bestandteil ein / bringt ihn an?
    integration_actor: str = "clarification_required"

    # PFAS-Sonderpfad: nur auf PKG-Ebene
    food_contact: bool = False


# =========================================================
# Marktfluss
# =========================================================

@dataclass
class MarketFlow:
    flow_id: str

    # Tatsächlicher Ausgangsstaat des Marktflusses.
    # Muss keine eigene Niederlassung sein.
    dispatch_country: str = "clarification_required"
    dispatch_country_other: str = ""

    # Staat der Bereitstellung
    target_country: str = "clarification_required"
    target_country_other: str = ""

    # Empfängerart
    recipient_type: str = "clarification_required"

    # Wurde die VE / das verpackte Produkt bereits vor
    # der Abgabe durch das geprüfte Unternehmen von
    # einem anderen Unternehmen im Zielland angeboten
    # oder abgegeben?
    prior_supply_in_target_country: str = (
        "clarification_required"
    )

    # Aus Kompatibilitätsgründen vorerst erhalten.
    # Wird ab v0.7.2 nicht mehr in der Marktfluss-UI
    # abgefragt.
    distance_sale: str = "clarification_required"


# =========================================================
# Ergebnis einer Rollenprüfung
# =========================================================

@dataclass
class RoleAssessment:
    role_key: str
    title: str
    status: str

    scope: str = ""
    country: str = ""

    summary: str = ""

    facts: list[str] = field(default_factory=list)
    rationale: list[str] = field(default_factory=list)

    legal_basis: str = ""
    interpretation_basis: str = ""

    # legal
    # commission
    # mixed
    basis_kind: str = "legal"


@dataclass
class ObligationDefinition:
    """Ruleset definition; behavior is implemented in rule functions."""

    obligation_id: str
    title: str
    trigger_type: str
    trigger_ids: list[str] = field(default_factory=list)
    legal_basis: list[str] = field(default_factory=list)
    interpretation_basis: list[str] = field(default_factory=list)
    requirement_text: str = ""
    applicable_from: Optional[str] = None
    depends_on_act: bool = False
    time_rule: str = ""
    country_scope: str = "EU"


@dataclass
class ObligationAssessment:
    """Current, scoped result with separate applicability and work status."""

    obligation_id: str
    title: str
    scope_type: str
    scope_id: str
    trigger_ids: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    applicability: str = "clarification_required"
    status: str = "Klärung erforderlich"
    requirement_text: str = ""
    country: str = ""
    applicable_from: Optional[str] = None
    depends_on_act: bool = False
    time_rule: str = ""
    missing_facts: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    notes: str = ""
    rule_notes: list[str] = field(default_factory=list)


# =========================================================
# Verpackungseinheit
# =========================================================

@dataclass
class PackagingUnit:
    ve_id: str

    # Grunddaten
    name: str = ""
    product_name: str = ""
    product_group: str = ""
    description: str = ""
    annual_units: Optional[int] = None

    # Bezugsweg der bereits vorhandenen VE bzw.
    # des bereits verpackten Produkts
    #
    # clarification_required
    # created_by_company
    # same_member_state
    # other_eu
    # third_country
    packaged_product_source: str = (
        "clarification_required"
    )

    # Auftragsentwicklung / Auftragsherstellung
    # unter eigenem Namen / eigener Marke
    own_name_or_brand: str = "clarification_required"

    # Verpackungsfunktionen
    packaging_functions: list[str] = field(
        default_factory=list
    )

    # Verpackungsart
    classification_answers: dict[str, str] = field(
        default_factory=dict
    )

    clarification_answers: dict[str, str] = field(
        default_factory=dict
    )

    packaging_type_candidates: list[str] = field(
        default_factory=list
    )

    packaging_types: list[str] = field(
        default_factory=list
    )

    primary_packaging_type: Optional[str] = None

    classification_status: str = (
        "clarification_required"
    )

    classification_reasons: dict[str, list[str]] = field(
        default_factory=dict
    )

    # Zusatzmerkmal der Transportverpackung
    is_ecommerce_packaging: str = (
        "clarification_required"
    )

    # Verkaufs-/Umverpackung
    self_filling_sales_grouped: str = (
        "clarification_required"
    )

    additional_processing_steps: list[str] = field(
        default_factory=list
    )

    # Transportverpackung
    transport_function_created_by_assembly: str = (
        "clarification_required"
    )

    # Marktflüsse
    market_flows: list[MarketFlow] = field(
        default_factory=list
    )

    # Auspacken ohne Endabnehmer zu sein
    unpacked_without_being_end_user: str = (
        "clarification_required"
    )

    # Bestandteile
    components: list[PackagingComponent] = field(
        default_factory=list
    )

    # Sonderpfade aus der abgestimmten Spezifikation
    intended_for_reuse: bool = False
    reuse_system_id: Optional[str] = None
    is_plastic_carrier_bag: bool = False
    compostable_format: str = "no"
    is_beverage_packaging: bool = False
    beverage_packaging_type: str = "other_beverage"
    used_for_dangerous_goods: bool = False
    sensitive_packaging_category: str = "no"
    potentially_innovative: bool = False
    individually_designed_large_goods: bool = False
    # Article 21 trigger for importers/distributors; asked only where relevant.
    article21_manufacturer_trigger: str = "clarification_required"


# =========================================================
# Unternehmen
# =========================================================

@dataclass
class Company:
    company_id: str

    name: str = ""

    country: str = "DE"
    country_other: str = ""

    has_other_eu_establishments: bool = False

    eu_establishments: list[str] = field(
        default_factory=list
    )

    micro_enterprise_status: str = (
        "clarification_required"
    )

    activities: list[str] = field(
        default_factory=list
    )

    procurement_regions: list[str] = field(
        default_factory=list
    )

    sales_regions: list[str] = field(
        default_factory=list
    )

    customer_types: list[str] = field(
        default_factory=list
    )

    sales_channels: list[str] = field(
        default_factory=list
    )

    sector_triggers: list[str] = field(
        default_factory=list
    )

    reuse_systems: list["ReuseSystem"] = field(
        default_factory=list
    )

    packaging_units: list[PackagingUnit] = field(
        default_factory=list
    )


@dataclass
class ReuseSystem:
    system_id: str
    name: str = ""
    system_type: str = "clarification_required"


# =========================================================
# Prüffall
# =========================================================

@dataclass
class AssessmentCase:
    case_id: str

    schema_version: str = "0.9.0"
    ruleset_version: str = "development"

    created_at: date = field(
        default_factory=date.today
    )

    assessment_date: date = field(
        default_factory=date.today
    )

    company: Company = field(
        default_factory=lambda: Company(
            company_id="COMP-001"
        )
    )

    obligation_records: list[ObligationAssessment] = field(
        default_factory=list
    )
