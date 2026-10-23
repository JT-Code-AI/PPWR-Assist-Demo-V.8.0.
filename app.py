import streamlit as _streamlit


_WIDGET_APIS = {
    "button",
    "checkbox",
    "download_button",
    "file_uploader",
    "multiselect",
    "number_input",
    "radio",
    "selectbox",
    "text_area",
    "text_input",
}


def _widget_key(key):
    generation = _streamlit.session_state.get("widget_generation", 0)
    return f"case{generation}_{key}"


class _StreamlitWithScopedWidgetKeys:
    """Give form widgets new identities after a case import."""

    def __getattr__(self, name):
        api = getattr(_streamlit, name)
        if name not in _WIDGET_APIS:
            return api

        def scoped_widget(*args, **kwargs):
            if kwargs.get("key") is not None:
                kwargs["key"] = _widget_key(kwargs["key"])
            return api(*args, **kwargs)

        return scoped_widget


st = _StreamlitWithScopedWidgetKeys()

from src.models import (
    AssessmentCase,
    PackagingUnit,
    PackagingComponent,
    MarketFlow,
    RoleAssessment,
    ReuseSystem,
)
from src.serialization import case_from_json, case_to_json
from src.import_state import install_imported_case
from src.obligation_engine import build_register, WORK_STATUSES
from src.documentation_register import build_documentation_register
from src.models import ObligationAssessment


# =========================================================
# Seite
# =========================================================

st.set_page_config(
    page_title="PPWR-Assist",
    page_icon="📦",
    layout="wide",
)

st.markdown(
    """
    <style>
    /* Kompakterer Abstand oberhalb des Anwendungstitels. */
    header[data-testid="stHeader"] {
        height: 2.5rem;
    }
    section[data-testid="stMain"] > div[data-testid="stMainBlockContainer"] {
        padding-top: 0.5rem !important;
        padding-bottom: 0.35rem !important;
    }
    @media (min-width: 769px) {
        section[data-testid="stMain"] div[data-testid="stHorizontalBlock"] {
            flex-wrap: nowrap !important;
        }
        section[data-testid="stMain"] div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
            min-width: 0 !important;
        }
    }

    /* Nur die Liste scrollt; Strukturüberschrift und Unternehmen liegen darüber. */
    .st-key-structure_tree_items {
        height: calc(100dvh - 23rem);
        min-height: 14rem;
        overflow-y: auto;
        overscroll-behavior: contain;
        padding-right: 0.35rem;
    }

    /* Registerinhalt scrollt unabhängig; Überschrift und Register bleiben sichtbar. */
    section[data-testid="stMain"] [data-testid="stTabs"] [role="tabpanel"] {
        height: calc(100dvh - 19rem);
        min-height: 20rem;
        overflow-y: auto;
        overscroll-behavior: contain;
        padding-right: 0.35rem;
    }
    .st-key-detail_panel_heading {
        position: sticky;
        top: 2.5rem;
        z-index: 20;
        background: var(--background-color, white);
        padding-top: 0.2rem;
    }
    section[data-testid="stMain"] [data-testid="stTabs"] [role="tablist"] {
        position: sticky;
        top: 6rem;
        z-index: 19;
        background: var(--background-color, white);
    }

    /* Auf schmalen Ansichten wieder natürliche Seitenhöhe und Seiten-Scroll. */
    @media (max-width: 768px) {
        .st-key-structure_tree_items,
        section[data-testid="stMain"] [data-testid="stTabs"] [role="tabpanel"] {
            height: auto;
            min-height: 0;
            overflow: visible;
        }
        .st-key-detail_panel_heading,
        section[data-testid="stMain"] [data-testid="stTabs"] [role="tablist"] {
            position: static;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# Konstanten
# =========================================================

EU_COUNTRIES = {
    "AT": "Österreich",
    "BE": "Belgien",
    "BG": "Bulgarien",
    "HR": "Kroatien",
    "CY": "Zypern",
    "CZ": "Tschechien",
    "DK": "Dänemark",
    "EE": "Estland",
    "FI": "Finnland",
    "FR": "Frankreich",
    "DE": "Deutschland",
    "GR": "Griechenland",
    "HU": "Ungarn",
    "IE": "Irland",
    "IT": "Italien",
    "LV": "Lettland",
    "LT": "Litauen",
    "LU": "Luxemburg",
    "MT": "Malta",
    "NL": "Niederlande",
    "PL": "Polen",
    "PT": "Portugal",
    "RO": "Rumänien",
    "SK": "Slowakei",
    "SI": "Slowenien",
    "ES": "Spanien",
    "SE": "Schweden",
}


TRI_STATE_OPTIONS = [
    "yes",
    "no",
    "clarification_required",
]


TRI_STATE_LABELS = {
    "yes": "Ja",
    "no": "Nein",
    "clarification_required": "Klärung erforderlich",
}


ROLE_STATUS_LABELS = TRI_STATE_LABELS.copy()


MICRO_STATUS_LABELS = {
    "clarification_required": "Klärung erforderlich",
    "yes": "Ja",
    "no": "Nein",
}


ACTIVITIES = {
    "manufacture_packaging":
        "Verpackungen herstellen",

    "manufacture_and_pack":
        "Produkte herstellen und selbst verpacken",

    "fill_purchased_packaging":
        "Gekaufte Verpackungen befüllen",

    "commission_own_specs":
        "Verpackungen nach eigenen Vorgaben herstellen lassen",

    "commission_own_brand":
        "Verpackungen unter eigenem Namen / eigener Marke "
        "herstellen lassen",

    "commission_packed_product":
        "Verpackte Produkte unter eigenem Namen / eigener "
        "Marke herstellen lassen",

    "buy_empty_standard":
        "Leere Standardverpackungen einkaufen",

    "buy_packaged_goods":
        "Bereits verpackte Waren einkaufen",

    "resell_packaged_goods":
        "Verpackte Waren unverändert weiterverkaufen",

    "import_empty_third_country":
        "Leere Verpackungen aus Drittländern importieren",

    "import_packed_third_country":
        "Verpackte Waren aus Drittländern importieren",

    "source_from_eu":
        "Verpackungen oder verpackte Waren aus anderen "
        "EU-Mitgliedstaaten beziehen",

    "ship_goods":
        "Waren versenden",

    "online_distance_sales":
        "Onlinehandel / Fernabsatz",

    "direct_end_recipient":
        "Direkt an Endabnehmer liefern",

    "sell_to_resellers":
        "An Händler / Wiederverkäufer liefern",

    "unpack_goods":
        "Angelieferte verpackte Waren auspacken",

    "reuse_packaging":
        "Verpackungen erneut verwenden",

    "take_back_packaging":
        "Verpackungen zurücknehmen",

    "operate_reuse_system":
        "Wiederverwendungssystem betreiben / nutzen",

    "fill_at_point_of_sale":
        "Verpackungen an der Verkaufsstelle befüllen",
}


REGION_OPTIONS = {
    "DE": "Deutschland",
    "EU_OTHER": "Andere EU-Mitgliedstaaten",
    "THIRD_COUNTRY": "Drittstaaten",
}


CUSTOMER_TYPES = {
    "B2B": "B2B – gewerbliche Kunden",
    "B2C": "B2C – Verbraucher",
}


SALES_CHANNELS = {
    "direct": "Direktvertrieb",
    "reseller": "Händler / Wiederverkäufer",
    "online_distance": "Onlinehandel / Fernabsatz",
    "professional_end_recipient":
        "Direkt an berufliche Endabnehmer",
    "consumer_direct":
        "Direkt an Verbraucher",
}


SECTOR_TRIGGERS = {
    "production_craft": "Produktion / Handwerk",
    "trade": "Handel",
    "packaging_manufacturing": "Verpackungsherstellung",
    "logistics_fulfilment": "Logistik / Fulfilment",
    "online_shipping": "Onlinehandel / Versand",
    "hospitality_takeaway": "Gastronomie / Take-away",
    "food_processing":
        "Lebensmittelherstellung / -verarbeitung",
    "primary_production":
        "Primärproduktion / Landwirtschaft",
    "reuse_pool":
        "Mehrweg- / Pool- / Wiederverwendungssystem",
    "other": "Sonstige",
}


PACKAGING_FUNCTIONS = {
    "containment": "Aufnahme",
    "protection": "Schutz",
    "handling": "Handhabung",
    "delivery": "Lieferung",
    "storage": "Lagerung",
    "transport": "Transport",
    "presentation": "Darbietung",
}


PACKAGING_TYPE_LABELS = {
    "sales": "Verkaufsverpackung",
    "grouped": "Umverpackung",
    "transport": "Transportverpackung",
    "service": "Serviceverpackung",
    "primary_production": "Primärproduktionsverpackung",
}


PACKAGING_TYPE_SOURCES = {
    "sales": "PPWR Art. 3 Abs. 1 Nr. 5",
    "grouped": "PPWR Art. 3 Abs. 1 Nr. 6",
    "transport": "PPWR Art. 3 Abs. 1 Nr. 7",
    "service": "PPWR Art. 3 Abs. 1 Nr. 1 Buchst. d",
    "primary_production": "PPWR Art. 3 Abs. 1 Nr. 4",
}


CLASSIFICATION_DEFAULTS = {
    "sales_unit": "clarification_required",
    "grouped_sales_units": "clarification_required",
    "transport_function": "clarification_required",
    "service_point_of_sale": "clarification_required",
    "primary_production": "clarification_required",
    "ecommerce_delivery": "clarification_required",
}


CLARIFICATION_DEFAULTS = {
    "sales_transport_until_end_recipient":
        "clarification_required",

    "sales_transport_specific_transport_design":
        "clarification_required",
}


PROCESSING_STEP_LABELS = {
    "assembly":
        "Zusammenbauen / Montieren",

    "forming_cutting":
        "Formen / Schneiden",

    "sealing":
        "Verschließen / Versiegeln",

    "other":
        "Sonstige Verarbeitung",
}


PROCUREMENT_TYPE_LABELS = {
    "clarification_required":
        "Klärung erforderlich",

    "standard_product":
        "Standardausführung des Lieferanten",

    "custom_manufactured":
        "Speziell für unser Unternehmen oder unser Produkt "
        "angefertigt",

    "self_manufactured":
        "Vom eigenen Unternehmen hergestellt",

    "used":
        "Gebraucht / bereits verwendet übernommen",
}


SUPPLIER_COUNTRY_LABELS = {
    "clarification_required":
        "Klärung erforderlich",

    **EU_COUNTRIES,

    "THIRD_COUNTRY":
        "Drittstaat",
}


SUPPLIED_OBJECT_TYPE_LABELS = {
    "clarification_required":
        "Klärung erforderlich",

    "complete_ve":
        "Vollständige leere Verpackungseinheit (VE)",

    "component":
        "Einzelner Bestandteil / Nebenbestandteil der VE",

    "packaging_material":
        "Verpackungsmaterial / Ausgangsmaterial",
}


INTEGRATION_ACTOR_LABELS = {
    "clarification_required":
        "Klärung erforderlich",

    "own_company":
        "Eigenes Unternehmen",

    "supplier":
        "Lieferant",

    "third_party":
        "Anderes Unternehmen / Dienstleister",

    "already_integrated":
        "Bereits in die VE integriert bezogen",

    "not_applicable":
        "Nicht zutreffend",
}


PACKAGED_PRODUCT_SOURCE_LABELS = {
    "clarification_required":
        "Klärung erforderlich",

    "created_by_company":
        "Die VE bzw. das verpackte Produkt entsteht "
        "bei unserem Unternehmen",

    "same_member_state":
        "Bereits verpackt aus dem eigenen Mitgliedstaat bezogen",

    "other_eu":
        "Bereits verpackt aus einem anderen "
        "EU-Mitgliedstaat bezogen",

    "third_country":
        "Bereits verpackt unmittelbar aus einem "
        "Drittland bezogen",
}


FLOW_COUNTRY_LABELS = {
    "clarification_required":
        "Klärung erforderlich",

    **EU_COUNTRIES,

    "THIRD_COUNTRY":
        "Drittstaat",
}


FLOW_RECIPIENT_LABELS = {
    "clarification_required":
        "Klärung erforderlich",

    "consumer_end_user":
        "Verbraucher / privater Endabnehmer",

    "professional_end_user":
        "Beruflicher / gewerblicher Endabnehmer",

    "reseller":
        "Händler / Wiederverkäufer",

    "own_establishment":
        "Eigene Niederlassung / Betriebsstätte",

    "other":
        "Anderer Empfänger",
}


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
    <style>

    .st-key-structure_tree
    div[data-testid="stVerticalBlock"] {
        gap: 0.05rem !important;
    }

    .st-key-structure_tree
    div[data-testid="stHorizontalBlock"] {
        gap: 0.15rem !important;
    }

    .st-key-structure_tree
    div[data-testid="stVerticalBlockBorderWrapper"] {
        margin-top: 0.05rem !important;
        margin-bottom: 0.05rem !important;
    }

    .st-key-structure_tree
    div[data-testid="stButton"] {
        margin: 0 !important;
        padding: 0 !important;
    }

    .st-key-structure_tree
    div[data-testid="stButton"] button {
        margin: 0 !important;
        padding: 0.10rem 0.20rem !important;
        min-height: 1.55rem !important;
        text-align: left !important;
        justify-content: flex-start !important;
    }

    .st-key-structure_tree
    div[data-testid="stButton"] button p {
        margin: 0 !important;
        text-align: left !important;
        white-space: normal !important;
        line-height: 1.20 !important;
    }

    .st-key-structure_tree
    button[kind="tertiary"] {
        border: none !important;
        background: transparent !important;
        box-shadow: none !important;
    }

    .st-key-structure_tree
    button[kind="tertiary"]:hover {
        background-color:
            rgba(128, 128, 128, 0.08) !important;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# Session
# =========================================================

if "case" not in st.session_state:
    st.session_state.case = AssessmentCase(
        case_id="CASE-001"
    )


case = st.session_state.case
company = case.company

if "widget_generation" not in st.session_state:
    st.session_state.widget_generation = 0


# =========================================================
# Migration
# =========================================================

def ensure_company_fields():
    defaults = {
        "country_other": "",
        "has_other_eu_establishments": False,
        "eu_establishments": [],
        "micro_enterprise_status":
            "clarification_required",
        "activities": [],
        "procurement_regions": [],
        "sales_regions": [],
        "customer_types": [],
        "sales_channels": [],
        "sector_triggers": [],
        "reuse_systems": [],
    }

    for name, default in defaults.items():
        if not hasattr(company, name):
            if isinstance(default, list):
                value = default.copy()
            else:
                value = default

            setattr(
                company,
                name,
                value,
            )


def ensure_ve_fields():
    defaults = {
        "product_name": "",
        "product_group": "",
        "annual_units": None,

        "packaged_product_source":
            "clarification_required",

        "own_name_or_brand":
            "clarification_required",

        "packaging_functions": [],

        "classification_answers": {},
        "clarification_answers": {},

        "packaging_type_candidates": [],
        "packaging_types": [],

        "primary_packaging_type": None,

        "classification_status":
            "clarification_required",

        "classification_reasons": {},

        "is_ecommerce_packaging":
            "clarification_required",

        "self_filling_sales_grouped":
            "clarification_required",

        "additional_processing_steps": [],

        "transport_function_created_by_assembly":
            "clarification_required",

        "market_flows": [],

        "unpacked_without_being_end_user":
            "clarification_required",
        "intended_for_reuse": False,
        "reuse_system_id": None,
        "is_plastic_carrier_bag": False,
        "compostable_format": "no",
        "is_beverage_packaging": False,
        "beverage_packaging_type": "other_beverage",
        "used_for_dangerous_goods": False,
        "sensitive_packaging_category": "no",
        "potentially_innovative": False,
        "individually_designed_large_goods": False,
        "article21_para1_trigger": "clarification_required",
    }

    for ve in company.packaging_units:
        for name, default in defaults.items():
            if not hasattr(ve, name):
                if isinstance(default, list):
                    value = default.copy()

                elif isinstance(default, dict):
                    value = default.copy()

                else:
                    value = default

                setattr(
                    ve,
                    name,
                    value,
                )

        for key, value in CLASSIFICATION_DEFAULTS.items():
            if key not in ve.classification_answers:
                ve.classification_answers[key] = value

        for key, value in CLARIFICATION_DEFAULTS.items():
            if key not in ve.clarification_answers:
                ve.clarification_answers[key] = value


def ensure_pkg_fields():
    defaults = {
        "procurement_type":
            "clarification_required",

        "supplier_name":
            "",

        "supplier_country":
            "clarification_required",

        "supplier_country_other":
            "",

        "supplied_object_type":
            "clarification_required",

        "independent_packaging_function":
            "clarification_required",

        "integration_actor":
            "clarification_required",

        "food_contact": False,
    }

    for ve in company.packaging_units:
        for pkg in ve.components:

            if not hasattr(pkg, "material_subtypes"):
                old_value = getattr(
                    pkg,
                    "material_subtype",
                    "",
                )

                if (
                    isinstance(old_value, str)
                    and old_value.strip()
                ):
                    pkg.material_subtypes = [
                        old_value.strip()
                    ]

                else:
                    pkg.material_subtypes = []

            for name, default in defaults.items():
                if not hasattr(pkg, name):
                    setattr(
                        pkg,
                        name,
                        default,
                    )


def ensure_flow_fields():
    for ve in company.packaging_units:
        for flow in ve.market_flows:

            if not hasattr(
                flow,
                "prior_supply_in_target_country",
            ):
                old_value = getattr(
                    flow,
                    "first_placing_by_company",
                    "clarification_required",
                )

                migration_map = {
                    "yes": "no",
                    "no": "yes",
                    "clarification_required":
                        "clarification_required",
                }

                flow.prior_supply_in_target_country = (
                    migration_map.get(
                        old_value,
                        "clarification_required",
                    )
                )

            defaults = {
                "label": "",

                "dispatch_country":
                    "clarification_required",

                "dispatch_country_other":
                    "",

                "target_country":
                    "clarification_required",

                "target_country_other":
                    "",

                "recipient_type":
                    "clarification_required",

                "distance_sale":
                    "clarification_required",
            }

            for name, default in defaults.items():
                if not hasattr(flow, name):
                    setattr(
                        flow,
                        name,
                        default,
                    )


ensure_company_fields()
ensure_ve_fields()
ensure_pkg_fields()
ensure_flow_fields()

case.schema_version = "0.8.2"


if "selected_object" not in st.session_state:
    st.session_state.selected_object = {
        "type": "company",
        "id": company.company_id,
    }


if "expanded_ves" not in st.session_state:
    st.session_state.expanded_ves = set()


# =========================================================
# IDs
# =========================================================

def numeric_suffix(value):
    try:
        return int(
            value.split("-")[-1]
        )

    except (ValueError, IndexError):
        return 0


def get_highest_ve_number():
    return max(
        [
            numeric_suffix(ve.ve_id)
            for ve in company.packaging_units
        ],
        default=0,
    )


def get_highest_pkg_number():
    return max(
        [
            numeric_suffix(pkg.pkg_id)
            for ve in company.packaging_units
            for pkg in ve.components
        ],
        default=0,
    )


def get_highest_flow_number():
    return max(
        [
            numeric_suffix(flow.flow_id)
            for ve in company.packaging_units
            for flow in ve.market_flows
        ],
        default=0,
    )


if "next_ve_number" not in st.session_state:
    st.session_state.next_ve_number = (
        get_highest_ve_number() + 1
    )


if "next_pkg_number" not in st.session_state:
    st.session_state.next_pkg_number = (
        get_highest_pkg_number() + 1
    )


if "next_flow_number" not in st.session_state:
    st.session_state.next_flow_number = (
        get_highest_flow_number() + 1
    )


def next_ve_id():
    result = (
        f"VE-{st.session_state.next_ve_number:03d}"
    )

    st.session_state.next_ve_number += 1

    return result


def next_pkg_id():
    result = (
        f"PKG-{st.session_state.next_pkg_number:03d}"
    )

    st.session_state.next_pkg_number += 1

    return result


def next_flow_id():
    result = (
        f"FLOW-{st.session_state.next_flow_number:03d}"
    )

    st.session_state.next_flow_number += 1

    return result


def load_uploaded_case():
    uploaded_case = st.session_state.get(_widget_key("case_import_file"))
    if uploaded_case is None:
        st.session_state["case_import_error"] = "Bitte zuerst eine JSON-Datei auswählen."
        return

    try:
        imported_case = case_from_json(
            uploaded_case.getvalue().decode("utf-8-sig")
        )
    except (ValueError, UnicodeDecodeError) as exc:
        st.session_state["case_import_error"] = str(exc)
        return

    install_imported_case(st.session_state, imported_case)


# =========================================================
# Allgemeine Hilfsfunktionen
# =========================================================

def select_object(
    object_type,
    object_id,
    parent_id=None,
):
    value = {
        "type": object_type,
        "id": object_id,
    }

    if parent_id is not None:
        value["parent_id"] = parent_id

    st.session_state.selected_object = value


def find_ve(ve_id):
    return next(
        (
            ve
            for ve in company.packaging_units
            if ve.ve_id == ve_id
        ),
        None,
    )


def find_pkg(
    pkg_id,
    parent_ve_id=None,
):
    if parent_ve_id:
        ve = find_ve(
            parent_ve_id
        )

        if ve:
            pkg = next(
                (
                    item
                    for item in ve.components
                    if item.pkg_id == pkg_id
                ),
                None,
            )

            if pkg:
                return ve, pkg

    for ve in company.packaging_units:
        for pkg in ve.components:
            if pkg.pkg_id == pkg_id:
                return ve, pkg

    return None, None


def open_ve(ve_id):
    st.session_state.expanded_ves.add(
        ve_id
    )


def toggle_ve(ve_id):
    if ve_id in st.session_state.expanded_ves:
        st.session_state.expanded_ves.remove(
            ve_id
        )

    else:
        st.session_state.expanded_ves.add(
            ve_id
        )


def init_widget_state(
    key,
    value,
):
    key = _widget_key(key)
    if key not in st.session_state:
        st.session_state[key] = value


def select_from_dict(
    label,
    current_value,
    labels,
    key,
    help_text=None,
):
    options = list(
        labels.keys()
    )

    if current_value not in options:
        current_value = options[0]

    return st.selectbox(
        label,
        options=options,
        index=options.index(
            current_value
        ),
        format_func=lambda value:
            labels[value],
        key=key,
        help=help_text,
    )


def classification_radio(
    label,
    current_value,
    key,
    packaging_type_label=None,
    help_text=None,
):
    if current_value not in TRI_STATE_OPTIONS:
        current_value = "clarification_required"

    display_label = label

    if packaging_type_label:
        display_label = (
            f"{label}  \n"
            f"({packaging_type_label})"
        )

    return st.radio(
        display_label,
        options=TRI_STATE_OPTIONS,
        index=TRI_STATE_OPTIONS.index(
            current_value
        ),
        format_func=lambda value:
            TRI_STATE_LABELS[value],
        horizontal=True,
        key=key,
        help=help_text,
    )


def country_display(
    code,
    other="",
):
    if code in EU_COUNTRIES:
        return EU_COUNTRIES[
            code
        ]

    if code == "THIRD_COUNTRY":
        if other.strip():
            return other.strip()

        return "Drittstaat"

    return "offen"


def company_country_display():
    if company.country in EU_COUNTRIES:
        return EU_COUNTRIES[
            company.country
        ]

    return (
        company.country_other.strip()
        or "Sonstiger Staat"
    )


# =========================================================
# Callbacks
# =========================================================

def update_ve_name(ve_id):
    ve = find_ve(
        ve_id
    )

    if ve:
        ve.name = st.session_state.get(
            _widget_key(f"name_{ve_id}"),
            "",
        )


def update_ve_description(ve_id):
    ve = find_ve(
        ve_id
    )

    if ve:
        ve.description = st.session_state.get(
            _widget_key(f"description_{ve_id}"),
            "",
        )


def update_pkg_name(
    ve_id,
    pkg_id,
):
    _, pkg = find_pkg(
        pkg_id,
        ve_id,
    )

    if pkg:
        pkg.name = st.session_state.get(
            _widget_key(f"name_{ve_id}_{pkg_id}"),
            "",
        )


def update_pkg_material(
    ve_id,
    pkg_id,
):
    _, pkg = find_pkg(
        pkg_id,
        ve_id,
    )

    if pkg:
        pkg.material = st.session_state.get(
            _widget_key(f"material_{ve_id}_{pkg_id}"),
            "",
        )


def update_pkg_weight(
    ve_id,
    pkg_id,
):
    _, pkg = find_pkg(
        pkg_id,
        ve_id,
    )

    if pkg:
        pkg.weight_g = st.session_state.get(
            _widget_key(f"weight_{ve_id}_{pkg_id}"),
            0.0,
        )


# =========================================================
# Materialunterarten
# =========================================================

def add_material_subtype(
    ve_id,
    pkg_id,
):
    _, pkg = find_pkg(
        pkg_id,
        ve_id,
    )

    if pkg:
        pkg.material_subtypes.append(
            ""
        )


def remove_material_subtype(
    ve_id,
    pkg_id,
):
    _, pkg = find_pkg(
        pkg_id,
        ve_id,
    )

    if not pkg:
        return

    if not pkg.material_subtypes:
        return

    index = (
        len(pkg.material_subtypes)
        - 1
    )

    pkg.material_subtypes.pop()

    key = (
        f"material_subtype_"
        f"{ve_id}_{pkg_id}_{index}"
    )

    if key in st.session_state:
        del st.session_state[
            key
        ]


# =========================================================
# Löschen
# =========================================================

def delete_ve(ve_id):
    company.packaging_units = [
        ve
        for ve in company.packaging_units
        if ve.ve_id != ve_id
    ]

    st.session_state.expanded_ves.discard(
        ve_id
    )

    select_object(
        "company",
        company.company_id,
    )


def delete_pkg(
    ve_id,
    pkg_id,
):
    ve = find_ve(
        ve_id
    )

    if not ve:
        return

    ve.components = [
        pkg
        for pkg in ve.components
        if pkg.pkg_id != pkg_id
    ]

    select_object(
        "ve",
        ve_id,
    )

    open_ve(
        ve_id
    )


def delete_flow(
    ve,
    flow_id,
):
    ve.market_flows = [
        flow
        for flow in ve.market_flows
        if flow.flow_id != flow_id
    ]


# =========================================================
# Verpackungsart-Engine
# =========================================================

def evaluate_packaging_types(ve):
    answers = ve.classification_answers

    candidates = []
    reasons = {}

    if answers.get("sales_unit") == "yes":
        candidates.append(
            "sales"
        )

        reasons["sales"] = [
            (
                "Die VE bildet nach der Angabe des "
                "Anwenders für den Endabnehmer eine "
                "Verkaufseinheit aus Produkt und Verpackung."
            )
        ]

    if answers.get("grouped_sales_units") == "yes":
        candidates.append(
            "grouped"
        )

        reasons["grouped"] = [
            (
                "Die VE enthält eine Zusammenstellung von "
                "Verkaufseinheiten und kann entfernt werden, "
                "ohne die Eigenschaften des Produkts zu "
                "beeinträchtigen."
            )
        ]

    if answers.get("transport_function") == "yes":
        candidates.append(
            "transport"
        )

        reasons["transport"] = [
            (
                "Die VE ist für Handhabung und Transport "
                "bestimmt und dient der Vermeidung von "
                "Schäden."
            )
        ]

    if answers.get("service_point_of_sale") == "yes":
        candidates.append(
            "service"
        )

        reasons["service"] = [
            (
                "Die VE ist zur Befüllung in der Verkaufsstelle "
                "zur Übergabe des Produkts vorgesehen."
            )
        ]

    if answers.get("primary_production") == "yes":
        candidates.append(
            "primary_production"
        )

        reasons["primary_production"] = [
            (
                "Die VE ist als Verpackung für ein "
                "unverarbeitetes Erzeugnis aus "
                "Primärproduktion gestaltet und bestimmt."
            )
        ]

    ecommerce = answers.get(
        "ecommerce_delivery"
    )

    if ecommerce == "no":
        ve.is_ecommerce_packaging = "no"

    elif ecommerce == "yes":
        if "transport" in candidates:
            ve.is_ecommerce_packaging = "yes"

        else:
            ve.is_ecommerce_packaging = (
                "clarification_required"
            )

    else:
        ve.is_ecommerce_packaging = (
            "clarification_required"
        )

    ve.packaging_type_candidates = (
        candidates.copy()
    )

    ve.packaging_types = (
        candidates.copy()
    )

    ve.classification_reasons = reasons

    if ve.primary_packaging_type not in candidates:
        ve.primary_packaging_type = None

    main_keys = [
        "sales_unit",
        "grouped_sales_units",
        "transport_function",
        "service_point_of_sale",
        "primary_production",
    ]

    unresolved = any(
        answers.get(key)
        == "clarification_required"
        for key in main_keys
    )

    if not candidates:
        ve.classification_status = (
            "clarification_required"
        )

    elif unresolved:
        ve.classification_status = (
            "clarification_required"
        )

    elif len(candidates) == 1:
        ve.primary_packaging_type = (
            candidates[0]
        )

        ve.classification_status = (
            "determined"
        )

    elif ve.primary_packaging_type:
        ve.classification_status = (
            "determined_multiple"
        )

    else:
        ve.classification_status = (
            "multiple_candidates"
        )


# =========================================================
# Lieferantenprüfung
# =========================================================

def supplier_same_member_state_status(pkg):
    if pkg.procurement_type == "self_manufactured":
        return "not_applicable"

    if (
        company.country in EU_COUNTRIES
        and
        pkg.supplier_country in EU_COUNTRIES
    ):
        if company.country == pkg.supplier_country:
            return "yes"

        return "no"

    if (
        company.country in EU_COUNTRIES
        and
        pkg.supplier_country == "THIRD_COUNTRY"
    ):
        return "no"

    return "clarification_required"


# =========================================================
# Hinweis eigenständige Verpackungsfunktion
# =========================================================

def render_independent_packaging_function_notice(
    ve,
    pkg,
):
    if pkg.independent_packaging_function != "yes":
        return

    # Direkt auf die aktuelle Klassifikationsantwort
    # zugreifen, nicht auf einen eventuell erst später
    # aktualisierten Kandidatenstatus.
    is_transport = (
        ve.classification_answers.get(
            "transport_function"
        )
        == "yes"
    )

    if is_transport:
        st.markdown(
            """
**Auslegung der Kommission – nicht rechtsverbindlich**

**Nach Ihrer Angabe** kann dieser Gegenstand eigenständig eine Verpackungsfunktion erfüllen. Nach der Auslegung der Kommission ist bei **Transportverpackungen** in diesem Fall das Unternehmen Erzeuger, welches die leere Verpackung herstellt.

Wenn die Verpackungsfunktion jedoch **erst durch das Zusammenfügen mehrerer nicht selbst funktionsfähiger Bestandteile entsteht**, ist der Zusammensetzende Erzeuger.

**Quelle:** Kommissionsleitlinie C/2026/3084 vom 10.06.2026, S. 8/37.  
*Die Einstufung „eigenständige Verpackungsfunktion“ beruht auf der Eingabe des Anwenders und stellt keine Festlegung durch PPWR-Assist dar.*
"""
        )

    st.info(
        "Prüfen Sie für die weitere Erfassung, ob dieser "
        "Gegenstand tatsächlich Bestandteil der aktuell "
        "betrachteten Verpackung ist oder als eigenständige "
        "Verpackungseinheit (VE) erfasst werden sollte."
    )


# =========================================================
# Transportverpackung – PKG-Übersicht
# =========================================================

def render_transport_component_function_check(ve):
    st.markdown(
        "**Verpackungsfunktion der Bestandteile**"
    )

    if not ve.components:
        st.warning(
            "Für diese VE wurden noch keine Bestandteile "
            "erfasst. Die Transportprüfung kann deshalb "
            "noch nicht vollständig durchgeführt werden."
        )

        return

    values = []

    for pkg in ve.components:
        status = (
            pkg.independent_packaging_function
        )

        values.append(
            status
        )

        st.write(
            f"**{pkg.pkg_id} – {pkg.name}:** "
            f"{TRI_STATE_LABELS.get(status, 'Klärung erforderlich')}"
        )

    all_yes = all(
        value == "yes"
        for value in values
    )

    any_unknown = any(
        value == "clarification_required"
        for value in values
    )

    if all_yes:
        st.info(
            "Nach den derzeitigen PKG-Angaben kann jeder "
            "erfasste Gegenstand bereits für sich eine "
            "Verpackungsfunktion erfüllen. Das besondere "
            "Kriterium „Erzeuger durch Zusammenfügen“ "
            "wird dadurch nicht automatisch ausgelöst."
        )

    elif any_unknown:
        st.warning(
            "Für mindestens einen Bestandteil ist noch "
            "nicht geklärt, ob er bereits eigenständig "
            "eine Verpackungsfunktion erfüllen kann."
        )

    else:
        st.info(
            "Mindestens ein Bestandteil kann nach den "
            "erfassten Angaben nicht bereits für sich "
            "eine Verpackungsfunktion erfüllen. Die "
            "nachfolgende Frage zum Zusammenfügen ist "
            "daher besonders relevant."
        )


# =========================================================
# Rollen-Engine – Hilfsfunktionen
# =========================================================

def role_packaging_group(ve):
    candidates = set(
        ve.packaging_type_candidates
    )

    sales_group = bool(
        candidates.intersection(
            {
                "sales",
                "grouped",
            }
        )
    )

    special_group = bool(
        candidates.intersection(
            {
                "transport",
                "service",
                "primary_production",
            }
        )
    )

    if sales_group and special_group:
        return "mixed"

    if sales_group:
        return "sales_grouped"

    if special_group:
        return "special"

    return "unknown"


def complete_ve_supplier_candidates(ve):
    return [
        pkg
        for pkg in ve.components
        if (
            pkg.supplied_object_type
            == "complete_ve"
            and
            pkg.procurement_type
            != "self_manufactured"
        )
    ]


def company_makes_complete_ve(ve):
    return any(
        (
            pkg.procurement_type
            == "self_manufactured"
            and
            pkg.supplied_object_type
            == "complete_ve"
        )
        for pkg in ve.components
    )


def all_transport_objects_independent(ve):
    if not ve.components:
        return False

    return all(
        pkg.independent_packaging_function == "yes"
        for pkg in ve.components
    )


def any_unresolved_pkg_supplier(ve):
    return any(
        (
            pkg.procurement_type
            != "self_manufactured"
            and
            pkg.supplier_country
            == "clarification_required"
        )
        for pkg in ve.components
    )


def imported_packaging_from_third_country(ve):
    for pkg in ve.components:
        if (
            pkg.procurement_type
            != "self_manufactured"
            and
            pkg.supplier_country
            == "THIRD_COUNTRY"
            and
            pkg.supplied_object_type
            != "packaging_material"
        ):
            return True

    return False


def has_eu_market_flow(ve):
    return any(
        flow.target_country in EU_COUNTRIES
        for flow in ve.market_flows
    )


def role_result(
    role_key,
    title,
    status,
    summary,
    scope="",
    country="",
    facts=None,
    rationale=None,
    legal_basis="",
    interpretation_basis="",
    basis_kind="legal",
):
    return RoleAssessment(
        role_key=role_key,
        title=title,
        status=status,
        scope=scope,
        country=country,
        summary=summary,
        facts=facts or [],
        rationale=rationale or [],
        legal_basis=legal_basis,
        interpretation_basis=interpretation_basis,
        basis_kind=basis_kind,
    )


# =========================================================
# Rollen-Engine – Erzeuger
# =========================================================

def assess_producer(ve):
    facts = []

    group = role_packaging_group(
        ve
    )

    # -----------------------------------------------------
    # Zunächst Verpackungsart abgrenzen
    # -----------------------------------------------------

    if group == "mixed":
        return role_result(
            role_key="producer",
            title="Erzeuger",
            status="clarification_required",
            summary=(
                "Die VE wurde gleichzeitig einer "
                "Verkaufs-/Umverpackung und einer "
                "Transport-/Service-/"
                "Primärproduktionsverpackung zugeordnet. "
                "Die Verpackungsart muss zunächst "
                "abgegrenzt werden."
            ),
            scope=ve.ve_id,
            legal_basis=(
                "PPWR Art. 3 Abs. 1 Nr. 13"
            ),
            interpretation_basis=(
                "Kommissionsleitlinie C/2026/3084, "
                "S. 5 und S. 8/37"
            ),
            basis_kind="mixed",
        )

    # -----------------------------------------------------
    # Verkaufs-/Umverpackung
    #
    # Eigene Befüllung / Bestückung wird zuerst geprüft.
    # Dadurch wird die Kleinstunternehmensregel nicht
    # fälschlich auf Standardverpackungen angewandt.
    # -----------------------------------------------------

    if (
        group == "sales_grouped"
        and
        ve.self_filling_sales_grouped == "yes"
    ):
        return role_result(
            role_key="producer",
            title="Erzeuger",
            status="yes",
            summary=(
                "Das Unternehmen ist nach den erfassten "
                "Angaben Erzeuger dieser Verkaufs- bzw. "
                "Umverpackung."
            ),
            scope=ve.ve_id,
            facts=[
                (
                    "Die Verpackung ist als Verkaufs- "
                    "bzw. Umverpackung eingeordnet."
                ),
                (
                    "Die Verpackung wird durch das "
                    "eigene Unternehmen befüllt bzw. "
                    "bestückt."
                ),
            ],
            rationale=[
                (
                    "Nach der Auslegung der Kommission "
                    "ist bei Verkaufs- und Umverpackungen "
                    "in der Regel der Wirtschaftsakteur "
                    "Erzeuger, der die letzten "
                    "Verarbeitungsschritte vornimmt und "
                    "die Verpackung mit seinem Produkt "
                    "befüllt."
                ),
                (
                    "Die Kleinstunternehmensregel wird "
                    "nicht allein dadurch ausgelöst, "
                    "dass leere Standardverpackungen oder "
                    "Verpackungsbestandteile von "
                    "Lieferanten bezogen werden."
                ),
            ],
            legal_basis=(
                "PPWR Art. 3 Abs. 1 Nr. 13"
            ),
            interpretation_basis=(
                "Kommissionsleitlinie C/2026/3084 "
                "vom 10.06.2026, S. 5/37"
            ),
            basis_kind="mixed",
        )

    # -----------------------------------------------------
    # Auftragsentwicklung / Auftragsherstellung
    # unter eigenem Namen / eigener Marke
    # -----------------------------------------------------

    if ve.own_name_or_brand == "clarification_required":
        return role_result(
            role_key="producer",
            title="Erzeuger",
            status="clarification_required",
            summary=(
                "Es ist noch nicht geklärt, ob die "
                "Verpackung oder das bereits verpackte "
                "Produkt von einem anderen Unternehmen "
                "unter Ihrem Namen oder Ihrer Marke "
                "entwickelt oder hergestellt wird."
            ),
            scope=ve.ve_id,
            legal_basis=(
                "PPWR Art. 3 Abs. 1 Nr. 13"
            ),
        )

    if ve.own_name_or_brand == "yes":
        facts.append(
            "Die Verpackung bzw. das bereits verpackte "
            "Produkt wird nach Angabe des Anwenders von "
            "einem anderen Unternehmen unter dem eigenen "
            "Namen oder der eigenen Marke entwickelt "
            "oder hergestellt."
        )

        if company.micro_enterprise_status == "no":
            return role_result(
                role_key="producer",
                title="Erzeuger",
                status="yes",
                summary=(
                    "Das Unternehmen ist nach den "
                    "erfassten Angaben Erzeuger."
                ),
                scope=ve.ve_id,
                facts=facts,
                rationale=[
                    (
                        "Die Verpackung bzw. das verpackte "
                        "Produkt wird unter eigenem Namen "
                        "oder eigener Marke entwickeln "
                        "oder herstellen gelassen."
                    )
                ],
                legal_basis=(
                    "PPWR Art. 3 Abs. 1 "
                    "Nr. 13 Buchst. a"
                ),
                basis_kind="legal",
            )

        if company.micro_enterprise_status == "yes":
            if company.country not in EU_COUNTRIES:
                return role_result(
                    role_key="producer",
                    title="Erzeuger",
                    status="yes",
                    summary=(
                        "Die Ausnahme für einen Lieferanten "
                        "im selben Mitgliedstaat kann bei "
                        "dem erfassten Sitz außerhalb der "
                        "EU nicht angewendet werden."
                    ),
                    scope=ve.ve_id,
                    facts=facts,
                    legal_basis=(
                        "PPWR Art. 3 Abs. 1 "
                        "Nr. 13 Buchst. a und b"
                    ),
                )

            suppliers = (
                complete_ve_supplier_candidates(
                    ve
                )
            )

            if len(suppliers) == 1:
                supplier = suppliers[0]

                if (
                    supplier.supplier_country
                    == company.country
                ):
                    return role_result(
                        role_key="producer",
                        title="Erzeuger",
                        status="no",
                        summary=(
                            "Nach den erfassten Angaben "
                            "greift die besondere "
                            "Kleinstunternehmensregel. "
                            "Der Lieferant der Verpackung "
                            "ist Erzeuger."
                        ),
                        scope=ve.ve_id,
                        facts=facts + [
                            "Kleinstunternehmen: Ja.",
                            (
                                "Die maßgebliche "
                                "Verpackung wird von einem "
                                "Lieferanten im selben "
                                "Mitgliedstaat bezogen."
                            ),
                        ],
                        legal_basis=(
                            "PPWR Art. 3 Abs. 1 "
                            "Nr. 13 Buchst. b"
                        ),
                        basis_kind="legal",
                    )

                if (
                    supplier.supplier_country
                    in EU_COUNTRIES
                    or
                    supplier.supplier_country
                    == "THIRD_COUNTRY"
                ):
                    return role_result(
                        role_key="producer",
                        title="Erzeuger",
                        status="yes",
                        summary=(
                            "Die Kleinstunternehmensregel "
                            "für einen Lieferanten im selben "
                            "Mitgliedstaat greift nach den "
                            "erfassten Angaben nicht."
                        ),
                        scope=ve.ve_id,
                        facts=facts,
                        legal_basis=(
                            "PPWR Art. 3 Abs. 1 "
                            "Nr. 13 Buchst. a und b"
                        ),
                        basis_kind="legal",
                    )

            return role_result(
                role_key="producer",
                title="Erzeuger",
                status="clarification_required",
                summary=(
                    "Das Unternehmen ist ein "
                    "Kleinstunternehmen und lässt die "
                    "Verpackung bzw. das verpackte Produkt "
                    "unter eigenem Namen oder eigener Marke "
                    "entwickeln oder herstellen. Für die "
                    "abschließende Prüfung muss geklärt "
                    "werden, wer die maßgebliche Verpackung "
                    "liefert und ob dieser Lieferant im "
                    "selben Mitgliedstaat ansässig ist."
                ),
                scope=ve.ve_id,
                facts=facts,
                legal_basis=(
                    "PPWR Art. 3 Abs. 1 "
                    "Nr. 13 Buchst. b"
                ),
                basis_kind="legal",
            )

        return role_result(
            role_key="producer",
            title="Erzeuger",
            status="clarification_required",
            summary=(
                "Die Unternehmensgröße ist noch nicht "
                "geklärt. Die mögliche Ausnahme für "
                "Kleinstunternehmen kann deshalb nicht "
                "geprüft werden."
            ),
            scope=ve.ve_id,
            facts=facts,
            legal_basis=(
                "PPWR Art. 3 Abs. 1 Nr. 13"
            ),
        )

    # -----------------------------------------------------
    # Keine Auftragsentwicklung/-herstellung unter
    # eigenem Namen / eigener Marke
    # -----------------------------------------------------

    if group == "sales_grouped":
        if ve.self_filling_sales_grouped == "no":
            if ve.additional_processing_steps:
                return role_result(
                    role_key="producer",
                    title="Erzeuger",
                    status="clarification_required",
                    summary=(
                        "Das Unternehmen befüllt bzw. "
                        "bestückt die Verpackung nicht "
                        "selbst, führt aber weitere "
                        "Verarbeitungsschritte durch. "
                        "Die Erzeugerrolle kann mit den "
                        "bisher erfassten Angaben nicht "
                        "abschließend bestimmt werden."
                    ),
                    scope=ve.ve_id,
                    legal_basis=(
                        "PPWR Art. 3 Abs. 1 Nr. 13"
                    ),
                    interpretation_basis=(
                        "Kommissionsleitlinie "
                        "C/2026/3084, S. 5/37"
                    ),
                    basis_kind="mixed",
                )

            return role_result(
                role_key="producer",
                title="Erzeuger",
                status="no",
                summary=(
                    "Nach der Auslegung der Kommission "
                    "ist das Unternehmen aufgrund der "
                    "erfassten Tatsachen nicht der "
                    "Erzeuger dieser Verkaufs- bzw. "
                    "Umverpackung."
                ),
                scope=ve.ve_id,
                facts=[
                    (
                        "Die Verpackung wird nicht durch "
                        "das eigene Unternehmen befüllt "
                        "oder bestückt."
                    ),
                    (
                        "Es liegt keine Auftragsentwicklung "
                        "oder Auftragsherstellung unter "
                        "eigenem Namen oder eigener Marke "
                        "vor."
                    ),
                ],
                legal_basis=(
                    "PPWR Art. 3 Abs. 1 Nr. 13"
                ),
                interpretation_basis=(
                    "Kommissionsleitlinie C/2026/3084 "
                    "vom 10.06.2026, S. 5/37"
                ),
                basis_kind="mixed",
            )

        return role_result(
            role_key="producer",
            title="Erzeuger",
            status="clarification_required",
            summary=(
                "Es ist noch nicht geklärt, wer die "
                "Verkaufs- bzw. Umverpackung befüllt "
                "oder bestückt."
            ),
            scope=ve.ve_id,
            legal_basis=(
                "PPWR Art. 3 Abs. 1 Nr. 13"
            ),
            interpretation_basis=(
                "Kommissionsleitlinie C/2026/3084, "
                "S. 5/37"
            ),
            basis_kind="mixed",
        )

    # -----------------------------------------------------
    # Transportverpackung
    # -----------------------------------------------------

    if "transport" in ve.packaging_type_candidates:
        if (
            ve.transport_function_created_by_assembly
            == "yes"
        ):
            return role_result(
                role_key="producer",
                title="Erzeuger",
                status="yes",
                summary=(
                    "Nach der Auslegung der Kommission "
                    "ist das Unternehmen Erzeuger, weil "
                    "die Verpackungsfunktion erst durch "
                    "das Zusammenfügen der Bestandteile "
                    "entsteht."
                ),
                scope=ve.ve_id,
                facts=[
                    (
                        "Verpackungsfunktion entsteht "
                        "erst durch Zusammenfügen: Ja."
                    )
                ],
                interpretation_basis=(
                    "Kommissionsleitlinie C/2026/3084 "
                    "vom 10.06.2026, S. 8/37"
                ),
                basis_kind="commission",
            )

        if (
            ve.transport_function_created_by_assembly
            == "clarification_required"
        ):
            return role_result(
                role_key="producer",
                title="Erzeuger",
                status="clarification_required",
                summary=(
                    "Es ist noch nicht geklärt, ob "
                    "die Verpackungsfunktion erst durch "
                    "das Zusammenfügen entsteht."
                ),
                scope=ve.ve_id,
                interpretation_basis=(
                    "Kommissionsleitlinie C/2026/3084, "
                    "S. 8/37"
                ),
                basis_kind="commission",
            )

        if company_makes_complete_ve(
            ve
        ):
            return role_result(
                role_key="producer",
                title="Erzeuger",
                status="yes",
                summary=(
                    "Das Unternehmen stellt nach den "
                    "erfassten Angaben die vollständige "
                    "leere Transportverpackung selbst her."
                ),
                scope=ve.ve_id,
                legal_basis=(
                    "PPWR Art. 3 Abs. 1 Nr. 13"
                ),
                interpretation_basis=(
                    "Kommissionsleitlinie C/2026/3084, "
                    "S. 5 und S. 8/37"
                ),
                basis_kind="mixed",
            )

        if all_transport_objects_independent(
            ve
        ):
            return role_result(
                role_key="producer",
                title="Erzeuger",
                status="no",
                summary=(
                    "Nach der Auslegung der Kommission "
                    "wird das Unternehmen nicht allein "
                    "durch das Zusammenstellen bereits "
                    "eigenständig funktionsfähiger "
                    "Transportverpackungen zum Erzeuger."
                ),
                scope=ve.ve_id,
                facts=[
                    (
                        "Alle erfassten PKG können nach "
                        "Anwenderangabe eigenständig eine "
                        "Verpackungsfunktion erfüllen."
                    ),
                    (
                        "Verpackungsfunktion entsteht "
                        "nicht erst durch Zusammenfügen."
                    ),
                ],
                interpretation_basis=(
                    "Kommissionsleitlinie C/2026/3084 "
                    "vom 10.06.2026, S. 8/37"
                ),
                basis_kind="commission",
            )

        return role_result(
            role_key="producer",
            title="Erzeuger",
            status="clarification_required",
            summary=(
                "Die Erzeugerrolle der "
                "Transportverpackung kann aus den "
                "bisherigen Angaben nicht eindeutig "
                "bestimmt werden."
            ),
            scope=ve.ve_id,
            interpretation_basis=(
                "Kommissionsleitlinie C/2026/3084, "
                "S. 8/37"
            ),
            basis_kind="commission",
        )

    # -----------------------------------------------------
    # Service- / Primärproduktionsverpackung
    # -----------------------------------------------------

    if group == "special":
        if company_makes_complete_ve(
            ve
        ):
            return role_result(
                role_key="producer",
                title="Erzeuger",
                status="yes",
                summary=(
                    "Das Unternehmen stellt nach den "
                    "erfassten Angaben die vollständige "
                    "Verpackung selbst her."
                ),
                scope=ve.ve_id,
                legal_basis=(
                    "PPWR Art. 3 Abs. 1 Nr. 13"
                ),
                interpretation_basis=(
                    "Kommissionsleitlinie C/2026/3084, "
                    "S. 5/37"
                ),
                basis_kind="mixed",
            )

        if (
            ve.components
            and
            all(
                pkg.procurement_type
                != "self_manufactured"
                for pkg in ve.components
            )
        ):
            return role_result(
                role_key="producer",
                title="Erzeuger",
                status="no",
                summary=(
                    "Nach der Auslegung der Kommission "
                    "ist bei der erfassten Service- bzw. "
                    "Primärproduktionsverpackung "
                    "regelmäßig der Hersteller der "
                    "leeren Verpackung Erzeuger."
                ),
                scope=ve.ve_id,
                interpretation_basis=(
                    "Kommissionsleitlinie C/2026/3084, "
                    "S. 5/37"
                ),
                basis_kind="commission",
            )

    return role_result(
        role_key="producer",
        title="Erzeuger",
        status="clarification_required",
        summary=(
            "Für eine belastbare Erzeugerbewertung "
            "reichen die erfassten Angaben noch nicht aus."
        ),
        scope=ve.ve_id,
        legal_basis=(
            "PPWR Art. 3 Abs. 1 Nr. 13"
        ),
    )


# =========================================================
# Rollen-Engine – Importeur
# =========================================================

def assess_importer(ve):
    if company.country not in EU_COUNTRIES:
        return role_result(
            role_key="importer",
            title="Importeur",
            status="no",
            summary=(
                "Die betrachtete Person ist nach den "
                "Stammdaten nicht in der Union ansässig. "
                "Sie kann daher nicht Importeur im Sinne "
                "von Art. 3 Abs. 1 Nr. 17 sein."
            ),
            scope=ve.ve_id,
            legal_basis=(
                "PPWR Art. 3 Abs. 1 Nr. 17"
            ),
        )

    third_country_source = (
        ve.packaged_product_source
        == "third_country"
        or
        imported_packaging_from_third_country(
            ve
        )
    )

    if third_country_source:
        if has_eu_market_flow(
            ve
        ):
            return role_result(
                role_key="importer",
                title="Importeur",
                status="yes",
                summary=(
                    "Das Unternehmen ist nach den "
                    "erfassten Angaben Importeur: Es ist "
                    "in der Union ansässig, bezieht die "
                    "betrachtete Verpackung bzw. das "
                    "verpackte Produkt unmittelbar aus "
                    "einem Drittland und stellt sie bzw. "
                    "es im Unionsmarkt bereit."
                ),
                scope=ve.ve_id,
                legal_basis=(
                    "PPWR Art. 3 Abs. 1 Nr. 17"
                ),
            )

        return role_result(
            role_key="importer",
            title="Importeur",
            status="clarification_required",
            summary=(
                "Ein unmittelbarer Bezug aus einem "
                "Drittland ist erfasst. Es ist jedoch "
                "noch nicht durch einen Marktfluss "
                "dokumentiert, dass die Verpackung auf "
                "dem Unionsmarkt in Verkehr gebracht wird."
            ),
            scope=ve.ve_id,
            legal_basis=(
                "PPWR Art. 3 Abs. 1 Nr. 17"
            ),
        )

    if (
        ve.packaged_product_source
        == "clarification_required"
        or
        any_unresolved_pkg_supplier(
            ve
        )
    ):
        return role_result(
            role_key="importer",
            title="Importeur",
            status="clarification_required",
            summary=(
                "Der Ursprung der bereits verpackten "
                "Ware bzw. einzelner Verpackungen ist "
                "noch nicht vollständig geklärt."
            ),
            scope=ve.ve_id,
            legal_basis=(
                "PPWR Art. 3 Abs. 1 Nr. 17"
            ),
        )

    return role_result(
        role_key="importer",
        title="Importeur",
        status="no",
        summary=(
            "Aus den erfassten Angaben ergibt sich "
            "für diese VE kein unmittelbarer Bezug "
            "von Verpackungen aus einem Drittland."
        ),
        scope=ve.ve_id,
        legal_basis=(
            "PPWR Art. 3 Abs. 1 Nr. 17"
        ),
    )


# =========================================================
# Rollen-Engine – Vertreiber
# =========================================================

def assess_distributor(
    ve,
    producer,
    importer,
):
    if (
        producer.status == "yes"
        or
        importer.status == "yes"
    ):
        return role_result(
            role_key="distributor",
            title="Vertreiber",
            status="no",
            summary=(
                "Für die betrachtete VE greift bereits "
                "die Erzeuger- bzw. Importeurrolle. "
                "Die Definition des Vertreibers schließt "
                "Erzeuger und Importeure aus."
            ),
            scope=ve.ve_id,
            legal_basis=(
                "PPWR Art. 3 Abs. 1 Nr. 18"
            ),
        )

    if (
        producer.status
        == "clarification_required"
        or
        importer.status
        == "clarification_required"
    ):
        return role_result(
            role_key="distributor",
            title="Vertreiber",
            status="clarification_required",
            summary=(
                "Die Erzeuger- oder Importeurrolle ist "
                "noch nicht abschließend geklärt. Die "
                "Vertreiberrolle kann deshalb noch nicht "
                "abschließend bestimmt werden."
            ),
            scope=ve.ve_id,
            legal_basis=(
                "PPWR Art. 3 Abs. 1 Nr. 18"
            ),
        )

    if has_eu_market_flow(
        ve
    ):
        return role_result(
            role_key="distributor",
            title="Vertreiber",
            status="yes",
            summary=(
                "Das Unternehmen stellt die Verpackung "
                "bzw. das verpackte Produkt nach den "
                "erfassten Marktflüssen auf dem "
                "Unionsmarkt bereit und ist für diese "
                "VE weder Erzeuger noch Importeur."
            ),
            scope=ve.ve_id,
            legal_basis=(
                "PPWR Art. 3 Abs. 1 Nr. 18"
            ),
        )

    if ve.market_flows:
        return role_result(
            role_key="distributor",
            title="Vertreiber",
            status="no",
            summary=(
                "Die erfassten Marktflüsse führen "
                "ausschließlich in Drittstaaten. Eine "
                "Bereitstellung auf dem Unionsmarkt ist "
                "für diese VE derzeit nicht erfasst."
            ),
            scope=ve.ve_id,
            legal_basis=(
                "PPWR Art. 3 Abs. 1 Nr. 18"
            ),
        )

    return role_result(
        role_key="distributor",
        title="Vertreiber",
        status="clarification_required",
        summary=(
            "Es wurde noch kein Marktfluss erfasst. "
            "Eine Vertreiberrolle kann deshalb noch "
            "nicht beurteilt werden."
        ),
        scope=ve.ve_id,
        legal_basis=(
            "PPWR Art. 3 Abs. 1 Nr. 18"
        ),
    )


# =========================================================
# Rollen-Engine – Hersteller
# =========================================================

def base_role_available(
    producer,
    importer,
    distributor,
):
    roles = [
        producer,
        importer,
        distributor,
    ]

    if any(
        role.status == "yes"
        for role in roles
    ):
        return "yes"

    if any(
        role.status
        == "clarification_required"
        for role in roles
    ):
        return "clarification_required"

    return "no"


def assess_manufacturer_flow(
    ve,
    flow,
    producer,
    importer,
    distributor,
):
    group = role_packaging_group(
        ve
    )

    target = (
        flow.target_country
    )

    dispatch = (
        flow.dispatch_country
    )

    if target == "clarification_required":
        return role_result(
            role_key="manufacturer",
            title=f"Hersteller – {flow.flow_id}",
            status="clarification_required",
            summary=(
                "Der Zielstaat des Marktflusses ist "
                "noch nicht geklärt."
            ),
            scope=flow.flow_id,
            legal_basis=(
                "PPWR Art. 3 Abs. 1 Nr. 15"
            ),
        )

    if target == "THIRD_COUNTRY":
        return role_result(
            role_key="manufacturer",
            title=f"Hersteller – {flow.flow_id}",
            status="no",
            summary=(
                "Der Marktfluss führt in einen "
                "Drittstaat. Für diesen Zielstaat "
                "entsteht keine Herstellerstellung "
                "nach der PPWR."
            ),
            scope=flow.flow_id,
            country=country_display(
                target,
                flow.target_country_other,
            ),
            interpretation_basis=(
                "Kommissionsleitlinie C/2026/3084, "
                "S. 8/37"
            ),
            basis_kind="commission",
        )

    if group in {
        "mixed",
        "unknown",
    }:
        return role_result(
            role_key="manufacturer",
            title=f"Hersteller – {flow.flow_id}",
            status="clarification_required",
            summary=(
                "Die für Art. 3 Abs. 1 Nr. 15 "
                "erforderliche Verpackungsart ist "
                "noch nicht ausreichend abgegrenzt."
            ),
            scope=flow.flow_id,
            country=country_display(
                target
            ),
            legal_basis=(
                "PPWR Art. 3 Abs. 1 Nr. 15"
            ),
        )

    if (
        flow.prior_supply_in_target_country
        == "clarification_required"
    ):
        return role_result(
            role_key="manufacturer",
            title=f"Hersteller – {flow.flow_id}",
            status="clarification_required",
            summary=(
                "Es ist noch nicht geklärt, ob die "
                "Verpackung bzw. das verpackte Produkt "
                "bereits vor Ihrem Unternehmen im "
                "Zielland angeboten oder abgegeben wurde."
            ),
            scope=flow.flow_id,
            country=country_display(
                target
            ),
            legal_basis=(
                "PPWR Art. 3 Abs. 1 Nr. 15"
            ),
        )

    if (
        flow.prior_supply_in_target_country
        == "yes"
    ):
        return role_result(
            role_key="manufacturer",
            title=f"Hersteller – {flow.flow_id}",
            status="no",
            summary=(
                "Nach Ihrer Angabe wurde die VE bzw. "
                "das verpackte Produkt bereits vor Ihrem "
                "Unternehmen im Zielland angeboten oder "
                "abgegeben. Ihr Unternehmen ist damit "
                "für diesen Marktfluss nicht der erstmals "
                "Bereitstellende."
            ),
            scope=flow.flow_id,
            country=country_display(
                target
            ),
            legal_basis=(
                "PPWR Art. 3 Abs. 1 Nr. 15"
            ),
        )

    base_status = base_role_available(
        producer,
        importer,
        distributor,
    )

    if base_status != "yes":
        return role_result(
            role_key="manufacturer",
            title=f"Hersteller – {flow.flow_id}",
            status="clarification_required",
            summary=(
                "Die Herstellerdefinition setzt einen "
                "Erzeuger, Importeur oder Vertreiber "
                "voraus. Mindestens eine dieser "
                "Grundrollen ist noch nicht ausreichend "
                "geklärt."
            ),
            scope=flow.flow_id,
            country=country_display(
                target
            ),
            legal_basis=(
                "PPWR Art. 3 Abs. 1 Nr. 15"
            ),
        )

    special = (
        group == "special"
    )

    # -----------------------------------------------------
    # Zielland = Sitzstaat des Unternehmens
    #
    # Art. 3 Abs. 1 Nr. 15 a/b:
    # Bereitstellung im Hoheitsgebiet UND
    # von demselben Hoheitsgebiet aus.
    # -----------------------------------------------------

    if (
        company.country in EU_COUNTRIES
        and
        target == company.country
    ):
        if dispatch == "clarification_required":
            return role_result(
                role_key="manufacturer",
                title=f"Hersteller – {flow.flow_id}",
                status="clarification_required",
                summary=(
                    "Der Zielstaat entspricht dem "
                    "Niederlassungsstaat des Unternehmens. "
                    "Für die Prüfung muss jedoch noch "
                    "geklärt werden, von welchem Staat "
                    "aus die Bereitstellung erfolgt."
                ),
                scope=flow.flow_id,
                country=EU_COUNTRIES[
                    target
                ],
                legal_basis=(
                    "PPWR Art. 3 Abs. 1 Nr. 15 "
                    "Buchst. a bzw. b"
                ),
            )

        if dispatch != company.country:
            return role_result(
                role_key="manufacturer",
                title=f"Hersteller – {flow.flow_id}",
                status="clarification_required",
                summary=(
                    "Der Zielstaat entspricht dem "
                    "Niederlassungsstaat des Unternehmens, "
                    "der Marktfluss erfolgt jedoch nicht "
                    "von demselben Hoheitsgebiet aus. "
                    "Der Tatbestand nach Art. 3 Abs. 1 "
                    "Nr. 15 Buchst. a bzw. b ist deshalb "
                    "mit den bisher erfassten Angaben "
                    "nicht eindeutig erfüllt."
                ),
                scope=flow.flow_id,
                country=EU_COUNTRIES[
                    target
                ],
                legal_basis=(
                    "PPWR Art. 3 Abs. 1 Nr. 15 "
                    "Buchst. a bzw. b"
                ),
            )

        letter = (
            "a"
            if special
            else "b"
        )

        return role_result(
            role_key="manufacturer",
            title=f"Hersteller – {flow.flow_id}",
            status="yes",
            summary=(
                "Das Unternehmen ist nach den "
                "erfassten Angaben Hersteller in "
                f"{EU_COUNTRIES[target]}."
            ),
            scope=flow.flow_id,
            country=EU_COUNTRIES[
                target
            ],
            facts=[
                (
                    "Zielstaat und Niederlassungsstaat "
                    "des Unternehmens stimmen überein."
                ),
                (
                    "Bereitstellung erfolgt von demselben "
                    "Hoheitsgebiet aus."
                ),
                (
                    "Vorherige Bereitstellung durch ein "
                    "anderes Unternehmen im Zielland: Nein."
                ),
            ],
            legal_basis=(
                "PPWR Art. 3 Abs. 1 Nr. 15 "
                f"Buchst. {letter}"
            ),
            basis_kind="legal",
        )

    # -----------------------------------------------------
    # Weitere erfasste EU-Niederlassung
    # -----------------------------------------------------

    if target in company.eu_establishments:
        return role_result(
            role_key="manufacturer",
            title=f"Hersteller – {flow.flow_id}",
            status="clarification_required",
            summary=(
                "Im Zielland ist eine weitere "
                "Niederlassung erfasst. PPWR-Assist "
                "unterscheidet derzeit noch nicht, ob "
                "diese Niederlassung Teil derselben "
                "juristischen Person oder eine "
                "rechtlich selbständige Gesellschaft "
                "ist. Die Herstellerrolle kann deshalb "
                "nicht automatisch zugeordnet werden."
            ),
            scope=flow.flow_id,
            country=EU_COUNTRIES.get(
                target,
                target,
            ),
            legal_basis=(
                "PPWR Art. 3 Abs. 1 Nr. 15"
            ),
        )

    # -----------------------------------------------------
    # Anderer EU-Mitgliedstaat
    # -----------------------------------------------------

    direct_end_recipient = (
        flow.recipient_type
        in {
            "consumer_end_user",
            "professional_end_user",
        }
    )

    if direct_end_recipient:
        letter = (
            "c"
            if special
            else "d"
        )

        return role_result(
            role_key="manufacturer",
            title=f"Hersteller – {flow.flow_id}",
            status="yes",
            summary=(
                "Das Unternehmen stellt die VE bzw. "
                "das verpackte Produkt nach den "
                "erfassten Angaben in einem anderen "
                "Mitgliedstaat erstmals direkt einem "
                "Endabnehmer bereit."
            ),
            scope=flow.flow_id,
            country=EU_COUNTRIES[
                target
            ],
            facts=[
                "Empfänger ist ein Endabnehmer.",
                (
                    "Vorherige Bereitstellung durch ein "
                    "anderes Unternehmen im Zielland: Nein."
                ),
            ],
            legal_basis=(
                "PPWR Art. 3 Abs. 1 Nr. 15 "
                f"Buchst. {letter}"
            ),
            basis_kind="legal",
        )

    if flow.recipient_type == "reseller":
        return role_result(
            role_key="manufacturer",
            title=f"Hersteller – {flow.flow_id}",
            status="no",
            summary=(
                "Die Lieferung erfolgt in einen anderen "
                "Mitgliedstaat an einen Händler bzw. "
                "Wiederverkäufer und nicht direkt an "
                "einen Endabnehmer. Nach der "
                "Kommissionsauslegung ist in diesem "
                "Fall regelmäßig der Empfänger bzw. "
                "der erste Bereitstellende im Zielland "
                "Hersteller."
            ),
            scope=flow.flow_id,
            country=EU_COUNTRIES[
                target
            ],
            legal_basis=(
                "PPWR Art. 3 Abs. 1 Nr. 15 "
                "Buchst. c bzw. d"
            ),
            interpretation_basis=(
                "Kommissionsleitlinie C/2026/3084, "
                "S. 8/37"
            ),
            basis_kind="commission",
        )

    return role_result(
        role_key="manufacturer",
        title=f"Hersteller – {flow.flow_id}",
        status="clarification_required",
        summary=(
            "Die Empfängerart erlaubt noch keine "
            "eindeutige Prüfung, ob eine direkte "
            "Bereitstellung an einen Endabnehmer "
            "vorliegt."
        ),
        scope=flow.flow_id,
        country=EU_COUNTRIES.get(
            target,
            target,
        ),
        legal_basis=(
            "PPWR Art. 3 Abs. 1 Nr. 15"
        ),
    )


# =========================================================
# Hersteller durch Auspacken
# =========================================================

def assess_unpacking_manufacturer(ve):
    if (
        ve.unpacked_without_being_end_user
        == "no"
    ):
        return role_result(
            role_key="manufacturer_unpacking",
            title="Hersteller – Auspacken",
            status="no",
            summary=(
                "Das Unternehmen packt nach den "
                "erfassten Angaben keine verpackten "
                "Produkte aus, ohne Endabnehmer zu sein."
            ),
            scope=ve.ve_id,
            legal_basis=(
                "PPWR Art. 3 Abs. 1 "
                "Nr. 15 Buchst. e"
            ),
        )

    if (
        ve.unpacked_without_being_end_user
        == "clarification_required"
    ):
        return role_result(
            role_key="manufacturer_unpacking",
            title="Hersteller – Auspacken",
            status="clarification_required",
            summary=(
                "Die Auspack-Situation ist noch nicht "
                "geklärt."
            ),
            scope=ve.ve_id,
            legal_basis=(
                "PPWR Art. 3 Abs. 1 "
                "Nr. 15 Buchst. e"
            ),
        )

    if company.country not in EU_COUNTRIES:
        return role_result(
            role_key="manufacturer_unpacking",
            title="Hersteller – Auspacken",
            status="no",
            summary=(
                "Art. 3 Abs. 1 Nr. 15 Buchst. e "
                "setzt eine Niederlassung in einem "
                "Mitgliedstaat voraus."
            ),
            scope=ve.ve_id,
            legal_basis=(
                "PPWR Art. 3 Abs. 1 "
                "Nr. 15 Buchst. e"
            ),
        )

    if ve.packaged_product_source in {
        "other_eu",
        "third_country",
    }:
        return role_result(
            role_key="manufacturer_unpacking",
            title="Hersteller – Auspacken",
            status="yes",
            summary=(
                "Das Unternehmen packt ein aus einem "
                "anderen EU-Mitgliedstaat bzw. Drittland "
                "bezogenes verpacktes Produkt aus, ohne "
                "Endabnehmer zu sein. Nach den erfassten "
                "Angaben kann damit der Auspack-"
                "Tatbestand greifen."
            ),
            scope=ve.ve_id,
            country=company_country_display(),
            facts=[
                (
                    "Auspacken ohne Endabnehmer zu sein: Ja."
                )
            ],
            legal_basis=(
                "PPWR Art. 3 Abs. 1 "
                "Nr. 15 Buchst. e"
            ),
            basis_kind="legal",
        )

    if (
        ve.packaged_product_source
        == "same_member_state"
    ):
        return role_result(
            role_key="manufacturer_unpacking",
            title="Hersteller – Auspacken",
            status="clarification_required",
            summary=(
                "Das verpackte Produkt wird bereits "
                "aus demselben Mitgliedstaat bezogen. "
                "Vor einer Zuordnung nach Buchst. e "
                "muss geprüft werden, ob bereits eine "
                "andere Person Hersteller nach "
                "Buchst. a bis d ist."
            ),
            scope=ve.ve_id,
            country=company_country_display(),
            legal_basis=(
                "PPWR Art. 3 Abs. 1 "
                "Nr. 15 Buchst. e"
            ),
        )

    return role_result(
        role_key="manufacturer_unpacking",
        title="Hersteller – Auspacken",
        status="clarification_required",
        summary=(
            "Das Unternehmen packt verpackte Produkte "
            "aus, ohne Endabnehmer zu sein. Der "
            "Bezugsweg des verpackten Produkts ist "
            "jedoch noch nicht ausreichend geklärt."
        ),
        scope=ve.ve_id,
        legal_basis=(
            "PPWR Art. 3 Abs. 1 "
            "Nr. 15 Buchst. e"
        ),
    )


# =========================================================
# Rollenanzeige
# =========================================================

def market_flow_reference(flow):
    label = (flow.label or "").strip()
    if label:
        return f"{flow.flow_id} – {label}"
    return f"{flow.flow_id} – Bezeichnung nicht angegeben"


def obligation_market_flow_references(item, market_flows):
    if item.scope_type == "flow":
        flow_ids = {item.scope_id}
    elif item.scope_type == "company":
        flow_ids = set(item.trigger_ids)
    else:
        return []
    return [
        market_flow_reference(flow)
        for flow in market_flows
        if flow.flow_id in flow_ids
    ]


def render_role_card(result, market_flow=None):
    with st.container(
        border=True
    ):
        st.markdown(
            f"### {result.title}"
        )
        if market_flow is not None:
            st.caption("Marktfluss: " + market_flow_reference(market_flow))

        status_text = (
            ROLE_STATUS_LABELS.get(
                result.status,
                result.status,
            )
        )

        if result.status == "yes":
            st.success(
                f"Ergebnis für Ihr Unternehmen: "
                f"**{status_text}**"
            )

        elif result.status == "no":
            st.info(
                f"Ergebnis für Ihr Unternehmen: "
                f"**{status_text}**"
            )

        else:
            st.warning(
                f"Ergebnis: **{status_text}**"
            )

        if result.country:
            st.write(
                f"**Staat:** {result.country}"
            )

        if result.summary:
            st.write(
                result.summary
            )

        if result.basis_kind in {
            "commission",
            "mixed",
        }:
            st.caption(
                "⚠️ Soweit die Bewertung auf der "
                "Kommissionsleitlinie beruht, handelt "
                "es sich um eine nicht rechtsverbindliche "
                "Auslegung."
            )

        if result.legal_basis:
            st.caption(
                "Rechtsgrundlage: "
                + result.legal_basis
            )

        if result.interpretation_basis:
            st.caption(
                "Auslegung: "
                + result.interpretation_basis
            )

        if (
            result.facts
            or result.rationale
        ):
            with st.expander(
                "Herleitung"
            ):
                if result.facts:
                    st.markdown(
                        "**Verwendete Angaben**"
                    )

                    for fact in result.facts:
                        st.write(
                            f"• {fact}"
                        )

                if result.rationale:
                    st.markdown(
                        "**Bewertung**"
                    )

                    for reason in result.rationale:
                        st.write(
                            f"• {reason}"
                        )


def render_roles(ve):
    producer = assess_producer(
        ve
    )

    importer = assess_importer(
        ve
    )

    distributor = assess_distributor(
        ve,
        producer,
        importer,
    )

    st.subheader(
        "Grundrollen"
    )

    st.caption(
        "Die Rollen werden aus den erfassten Tatsachen "
        "abgeleitet. PPWR-Assist fragt nicht danach, "
        "welche Rolle sich der Anwender selbst zuordnet."
    )

    col1, col2, col3 = st.columns(
        3
    )

    with col1:
        render_role_card(
            producer
        )

    with col2:
        render_role_card(
            importer
        )

    with col3:
        render_role_card(
            distributor
        )

    st.divider()

    st.subheader(
        "Hersteller / EPR nach Marktfluss"
    )

    st.caption(
        "Die Herstellerrolle wird getrennt für den "
        "jeweiligen EU-Mitgliedstaat geprüft. "
        "Erzeuger und Hersteller sind unterschiedliche "
        "PPWR-Rollen."
    )

    if not ve.market_flows:
        st.warning(
            "Es wurde noch kein Marktfluss erfasst. "
            "Eine Herstellerbewertung nach Art. 3 "
            "Abs. 1 Nr. 15 Buchst. a bis d ist "
            "deshalb noch nicht möglich."
        )

    for flow in ve.market_flows:
        result = assess_manufacturer_flow(
            ve,
            flow,
            producer,
            importer,
            distributor,
        )

        render_role_card(
            result,
            market_flow=flow,
        )

    unpacking_result = (
        assess_unpacking_manufacturer(
            ve
        )
    )

    render_role_card(
        unpacking_result
    )

    st.info(
        "Die Anzeige ist keine vollständige Pflichtenbewertung; offene "
        "Tatbestände und Ausnahmen werden als "
        "Klärungsbedarf ausgewiesen."
    )


# =========================================================
# Strukturbaum
# =========================================================

def render_structure_tree():
    with st.container(
        key="structure_tree"
    ):
        st.subheader(
            "Struktur"
        )

        with st.container(
            border=True
        ):
            if st.button(
                "🏢 Unternehmen",
                key="tree_company",
                type="tertiary",
            ):
                select_object(
                    "company",
                    company.company_id,
                )

                st.rerun()

        with st.container(key="structure_tree_items"):
            for ve in company.packaging_units:
                expanded = (
                    ve.ve_id
                    in st.session_state.expanded_ves
                )

                with st.container(
                    border=True
                ):
                    arrow_col, ve_col = st.columns(
                        [0.08, 0.92],
                        gap="small",
                    )

                    with arrow_col:
                        arrow = (
                            "▾"
                            if expanded
                            else "▸"
                        )

                        if st.button(
                            arrow,
                            key=f"toggle_{ve.ve_id}",
                            type="tertiary",
                        ):
                            toggle_ve(
                                ve.ve_id
                            )

                            st.rerun()

                    with ve_col:
                        if st.button(
                            (
                                f"📦 {ve.ve_id} – "
                                f"{ve.name or 'Neue Verpackung'}"
                            ),
                            key=f"select_{ve.ve_id}",
                            type="tertiary",
                        ):
                            select_object(
                                "ve",
                                ve.ve_id,
                            )

                            st.rerun()

                if expanded:
                    for pkg in ve.components:
                        _, pkg_col = st.columns(
                            [0.12, 0.88],
                            gap="small",
                        )

                        with pkg_col:
                            selected = (
                                st.session_state.selected_object
                            )

                            active = (
                                selected.get("type") == "pkg"
                                and
                                selected.get("id")
                                == pkg.pkg_id
                                and
                                selected.get("parent_id")
                                == ve.ve_id
                            )

                            prefix = (
                                "●"
                                if active
                                else "↳"
                            )

                            if st.button(
                                (
                                    f"{prefix} "
                                    f"{pkg.pkg_id} – "
                                    f"{pkg.name or 'Bestandteil'}"
                                ),
                                key=(
                                    f"select_{ve.ve_id}_"
                                    f"{pkg.pkg_id}"
                                ),
                                type="tertiary",
                            ):
                                select_object(
                                    "pkg",
                                    pkg.pkg_id,
                                    ve.ve_id,
                                )

                                st.rerun()

            st.divider()

            if st.button(
                "➕ Verpackungseinheit",
                key="add_ve",
                use_container_width=True,
            ):
                new_ve = PackagingUnit(
                    ve_id=next_ve_id(),
                    name="Neue Verpackung",
                )

                new_ve.classification_answers = (
                    CLASSIFICATION_DEFAULTS.copy()
                )

                new_ve.clarification_answers = (
                    CLARIFICATION_DEFAULTS.copy()
                )

                company.packaging_units.append(
                    new_ve
                )

                open_ve(
                    new_ve.ve_id
                )

                select_object(
                    "ve",
                    new_ve.ve_id,
                )

                st.rerun()


# =========================================================
# Unternehmen
# =========================================================

OBLIGATION_STATUS_LABELS = {
    "applicable": "Gilt nach Prüfdatum",
    "upcoming": "Künftig anwendbar",
    "review": "Klärung / Prüfung erforderlich",
    "scheduled_review": "Termin abhängig von Durchführungsrechtsakt",
    "exempt": "Kleinstunternehmen-Ausnahme zu berücksichtigen",
}


OBLIGATION_APPLICABILITY_LABELS = {
    "applicable": "Anwendbar",
    "future": "Künftig anwendbar",
    "clarification_required": "Anwendbarkeit zu klären",
    "not_applicable": "Nicht anwendbar",
}


def collect_case_roles(active_case):
    results = []
    for ve in active_case.company.packaging_units:
        producer = assess_producer(ve)
        importer = assess_importer(ve)
        distributor = assess_distributor(ve, producer, importer)
        results.extend([producer, importer, distributor])
        results.extend(
            assess_manufacturer_flow(ve, flow, producer, importer, distributor)
            for flow in ve.market_flows
        )
    return results


def persist_obligation_progress(item):
    key = (item.obligation_id, item.scope_type, item.scope_id, item.country)
    record = next(
        (r for r in case.obligation_records
         if (r.obligation_id, r.scope_type, r.scope_id, r.country) == key),
        None,
    )
    if record is None:
        record = ObligationAssessment(
            obligation_id=item.obligation_id,
            title=item.title,
            scope_type=item.scope_type,
            scope_id=item.scope_id,
            country=item.country,
        )
        case.obligation_records.append(record)
    record.status = item.status
    record.evidence = list(item.evidence)
    record.notes = item.notes


def render_obligation_list(obligations, heading, editable=False, market_flows=None):
    market_flows = market_flows or []
    st.subheader(heading)
    if editable:
        st.caption(
            "„Erfüllt“ dokumentiert nur Ihre eigene Bestätigung und ist keine rechtliche Zertifizierung durch PPWR-Assist."
        )
    if not obligations:
        st.info("Für die erfassten Angaben wurde hier kein Sonderpfad ausgelöst.")
        return

    for item in obligations:
        with st.container(border=True):
            st.markdown(f"**{item.title}**")
            due = f" · ab {item.applicable_from}" if item.applicable_from else ""
            if item.depends_on_act:
                due = " · Termin hängt von Durchführungsrechtsakt ab"
            st.caption(
                f"Anwendbarkeit: {OBLIGATION_APPLICABILITY_LABELS.get(item.applicability, item.applicability)}"
                f" · Bearbeitung: {item.status}{due}"
            )
            st.write(item.requirement_text)
            st.caption(f"Betroffen: {item.scope_type} {item.scope_id}" + (f" · {item.country}" if item.country else ""))
            flow_references = obligation_market_flow_references(item, market_flows)
            if flow_references:
                st.caption("Marktfluss: " + "; ".join(flow_references))
            if item.missing_facts:
                st.warning("Offene Tatsachen: " + "; ".join(item.missing_facts))
            if item.rule_notes:
                st.info("Regelhinweise: " + "; ".join(item.rule_notes))
            if item.exceptions:
                st.caption("Ausnahmen / Abgrenzungen: " + "; ".join(item.exceptions))
            if item.notes:
                st.caption("Notiz: " + item.notes)
            if item.time_rule:
                st.caption("Zeitregel: " + item.time_rule)
            st.caption("Rechtsgrundlage: " + "; ".join(item.sources))
            st.caption(
                "Pflicht-ID: " + item.obligation_id
                + " · Auslöser: "
                + (", ".join(item.trigger_ids) or "Verpackungsmerkmale")
            )
            if editable:
                progress_key = "_".join((item.obligation_id, item.scope_type, item.scope_id, item.country))
                item.status = st.selectbox(
                    "Bearbeitungsstatus",
                    options=list(WORK_STATUSES),
                    index=list(WORK_STATUSES).index(item.status),
                    key=f"ob_status_{progress_key}",
                )
                evidence_text = st.text_area(
                    "Nachweis / Belegverweis",
                    value="\n".join(item.evidence),
                    key=f"ob_evidence_{progress_key}",
                )
                item.evidence = [line.strip() for line in evidence_text.splitlines() if line.strip()]
                item.notes = st.text_area(
                    "Notiz",
                    value=item.notes,
                    key=f"ob_notes_{progress_key}",
                )
                persist_obligation_progress(item)


def render_special_path_inputs(ve):
    st.divider()
    st.subheader("Besondere Prüfpfade")
    st.caption(
        "Nur die in der Spezifikation vorgesehenen Merkmale werden abgefragt. "
        "Nicht aktivierte Checkboxen erzeugen keinen Prüfpfad."
    )

    ve.intended_for_reuse = st.checkbox(
        "Zur Wiederverwendung / Mehrweg vorgesehen",
        value=ve.intended_for_reuse,
        key=f"intended_for_reuse_{ve.ve_id}_v082",
    )

    if ve.intended_for_reuse:
        systems = company.reuse_systems
        options = [""] + [system.system_id for system in systems]
        labels = {system.system_id: system.name or system.system_id for system in systems}
        selected = st.selectbox(
            "Wiederverwendungssystem zuordnen (optional)",
            options=options,
            index=options.index(ve.reuse_system_id)
            if ve.reuse_system_id in options
            else 0,
            format_func=lambda value: "Kein System zugeordnet"
            if value == ""
            else labels.get(value, value),
            key=f"reuse_system_link_{ve.ve_id}_v082",
        )
        ve.reuse_system_id = selected or None
        if not systems:
            st.info("Lege ein Wiederverwendungssystem im Unternehmensbereich an, wenn eine Zuordnung besteht.")
    else:
        ve.reuse_system_id = None

    ve.is_plastic_carrier_bag = st.checkbox(
        "Kunststofftragetasche",
        value=ve.is_plastic_carrier_bag,
        key=f"plastic_bag_{ve.ve_id}_v082",
    )

    compost_options = [
        "no",
        "tea_coffee_bag",
        "single_serve_unit",
        "produce_sticker",
        "other_national",
        "clarification_required",
    ]
    compost_labels = {
        "no": "Nein",
        "tea_coffee_bag": "Durchlässiger Tee-/Kaffeebeutel oder vergleichbarer Getränkebeutel",
        "single_serve_unit": "Bei Gebrauch aufweichende Einzelportionseinheit für Tee/Kaffee/Getränke",
        "produce_sticker": "Obst-/Gemüseaufkleber",
        "other_national": "Sonstiges möglicherweise national geregeltes Format",
        "clarification_required": "Klärung erforderlich",
    }
    ve.compostable_format = st.selectbox(
        "Kompostierbares Verpackungsformat",
        options=compost_options,
        index=compost_options.index(
            ve.compostable_format if ve.compostable_format in compost_options else "no"
        ),
        format_func=lambda value: compost_labels[value],
        key=f"compost_format_{ve.ve_id}_v082",
    )

    ve.is_beverage_packaging = st.checkbox(
        "Getränkeverpackung",
        value=ve.is_beverage_packaging,
        key=f"beverage_packaging_{ve.ve_id}_v082",
    )
    if ve.is_beverage_packaging:
        beverage_options = [
            "other_beverage",
            "single_use_plastic_bottle",
            "single_use_metal_container",
            "clarification_required",
        ]
        beverage_labels = {
            "other_beverage": "Sonstige Getränkeverpackung",
            "single_use_plastic_bottle": "Einweg-Kunststoffgetränkeflasche",
            "single_use_metal_container": "Einweg-Metallgetränkebehälter",
            "clarification_required": "Klärung erforderlich",
        }
        ve.beverage_packaging_type = st.selectbox(
            "Art der Getränkeverpackung",
            options=beverage_options,
            index=beverage_options.index(
                ve.beverage_packaging_type
                if ve.beverage_packaging_type in beverage_options
                else "other_beverage"
            ),
            format_func=lambda value: beverage_labels[value],
            key=f"beverage_type_{ve.ve_id}_v082",
        )

    ve.used_for_dangerous_goods = st.checkbox(
        "Für den Transport gefährlicher Güter verwendet",
        value=ve.used_for_dangerous_goods,
        key=f"dangerous_goods_{ve.ve_id}_v082",
        help="Maßgeblich ist die tatsächliche Gefahrgutverwendung; eine UN-Zulassung allein genügt nicht.",
    )

    sensitive_options = ["no", *SENSITIVE_PACKAGING_OPTIONS.keys(), "clarification_required"]
    ve.sensitive_packaging_category = st.selectbox(
        "Sensible Verpackungskategorie",
        options=sensitive_options,
        index=sensitive_options.index(
            ve.sensitive_packaging_category
            if ve.sensitive_packaging_category in sensitive_options
            else "no"
        ),
        format_func=lambda value: {
            "no": "Nein",
            "clarification_required": "Klärung erforderlich",
            **SENSITIVE_PACKAGING_OPTIONS,
        }[value],
        key=f"sensitive_category_{ve.ve_id}_v082",
    )

    ve.potentially_innovative = st.checkbox(
        "Möglicherweise innovative Verpackung",
        value=ve.potentially_innovative,
        key=f"innovative_packaging_{ve.ve_id}_v082",
    )

    ve.individually_designed_large_goods = st.checkbox(
        "Individuell gestaltete Verpackung für große Maschinen, Ausrüstung oder Rohstoffe",
        value=ve.individually_designed_large_goods,
        key=f"art29_individual_design_{ve.ve_id}_v082",
        help="Ausnahme-Trigger ausschließlich für Art. 29 Abs. 1–3; keine allgemeine PPWR-Befreiung.",
    )

    producer = assess_producer(ve)
    importer = assess_importer(ve)
    distributor = assess_distributor(ve, producer, importer)
    if importer.status != "no" or distributor.status != "no":
        ve.article21_para1_trigger = st.selectbox(
            "Fälle, in denen die Pflichten der Erzeuger auch für Importeure und Vertreiber gelten",
            options=["clarification_required", "yes", "no"],
            index=["clarification_required", "yes", "no"].index(
                ve.article21_para1_trigger
                if ve.article21_para1_trigger in {"clarification_required", "yes", "no"}
                else "clarification_required"
            ),
            format_func=lambda value: {
                "clarification_required": "Noch zu klären",
                "yes": "Ja",
                "no": "Nein",
            }[value],
            help=(
                "Hier wird geprüft, ob ein Fall nach Art. 21 Abs. 1 vorliegt: Ein Importeur oder "
                "Vertreiber bringt die Verpackung unter eigenem Namen/eigener Marke in Verkehr "
                "oder verändert sie so, dass die Konformität beeinträchtigt werden kann. "
                "Art. 21 Abs. 2 wird zusätzlich anhand des Kleinstunternehmensstatus und der "
                "Lieferantenangaben geprüft. Ist der Importeur/Vertreiber ein Kleinstunternehmen "
                "und der Verpackungslieferant in der Union ansässig, gilt der Lieferant als Erzeuger "
                "für die Zwecke des Art. 15."
            ),
            key=f"article21_trigger_{ve.ve_id}_v082",
        )
    else:
        ve.article21_para1_trigger = "clarification_required"


SENSITIVE_PACKAGING_OPTIONS = {
    "medicinal_primary": "Arzneimittel-Primärverpackung",
    "medicinal_outer": "Arzneimittel-äußere Umhüllung zur Qualitätserhaltung",
    "medical_device": "Kontaktempfindliche Medizinproduktverpackung",
    "ivd": "In-vitro-Diagnostikum (IVD)",
    "special_food": "Kontaktempfindliche Verpackung für Säuglings-/Kleinkindernahrung oder Lebensmittel für besondere medizinische Zwecke",
}


def render_packaging_obligations(ve):
    pkg_ids = {pkg.pkg_id for pkg in ve.components}
    flow_ids = {flow.flow_id for flow in ve.market_flows}
    register = build_register(case, collect_case_roles(case))
    relevant = [
        item
        for item in register
        if (
            (
                (item.scope_type == "VE" and item.scope_id == ve.ve_id)
                or (item.scope_type == "PKG" and item.scope_id in pkg_ids)
                or (item.scope_type == "flow" and item.scope_id in flow_ids)
                or (item.scope_type == "company" and any(flow_id in item.trigger_ids for flow_id in flow_ids))
            )
            and item.applicability != "future"
        )
    ]
    render_obligation_list(
        relevant,
        "Rollen- und Verpackungspflichten",
        market_flows=ve.market_flows,
    )


def render_documentation_outlook(ve):
    pkg_ids = {pkg.pkg_id for pkg in ve.components}
    flow_ids = {flow.flow_id for flow in ve.market_flows}
    register = build_register(case, collect_case_roles(case))
    relevant = [
        item for item in register
        if (
            (item.scope_type == "VE" and item.scope_id == ve.ve_id)
            or (item.scope_type == "PKG" and item.scope_id in pkg_ids)
            or (item.scope_type == "flow" and item.scope_id in flow_ids)
            or (
                item.scope_type == "company"
                and (
                    any(fid in item.trigger_ids for fid in flow_ids)
                    or "SPEC_HORECA_REFILL_REUSE" in item.trigger_ids
                )
            )
        )
    ]
    documents, future = build_documentation_register(relevant)

    st.subheader("Nachweise aus ausgelösten Pflichten")
    if not documents:
        st.info("Für diese Verpackungseinheit wurden keine Dokumentationsnachweise aus den erfassten Pflichten abgeleitet.")
    else:
        for entry in documents:
            parent = entry["parent"]
            with st.container(border=True):
                st.markdown(f"**{entry['title']}**")
                st.caption(f"Abgeleitet aus: {parent.title} · {parent.obligation_id}")
                flow_references = obligation_market_flow_references(parent, ve.market_flows)
                if flow_references:
                    st.caption("Marktfluss: " + "; ".join(flow_references))
                for detail in entry["details"]:
                    st.markdown(f"- {detail}")
                if parent.evidence:
                    st.caption("Erfasste Nachweise: " + "; ".join(parent.evidence))
                if parent.applicability == "clarification_required":
                    st.caption("Pflichtanwendbarkeit ist noch zu klären.")

    st.subheader("Künftige Anforderungen")
    if not future:
        st.info("Für diese Verpackungseinheit wurden keine künftigen Pflichten ausgelöst.")
    else:
        render_obligation_list(
            future,
            "Noch nicht geltende Pflichten",
            market_flows=ve.market_flows,
        )

def render_company_detail():
    st.header(
        "Unternehmen"
    )

    tab1, tab2, tab3 = st.tabs(
        [
            "Unternehmen",
            "Verpackungen & Rollen",
            "Pflichten & offene Punkte",
        ]
    )

    with tab1:
        st.subheader(
            "Stammdaten"
        )

        company.name = st.text_input(
            "Unternehmensbezeichnung (optional)",
            value=company.name,
            key="company_name_v072",
        )

        country_options = (
            list(
                EU_COUNTRIES.keys()
            )
            + ["OTHER"]
        )

        current_country = (
            company.country
        )

        if current_country not in country_options:
            current_country = "OTHER"

        company.country = st.selectbox(
            "Sitzstaat",
            options=country_options,
            index=country_options.index(
                current_country
            ),
            format_func=lambda value:
                (
                    EU_COUNTRIES[value]
                    if value in EU_COUNTRIES
                    else "Sonstiger Staat"
                ),
            key="company_country_v072",
        )

        if company.country == "OTHER":
            company.country_other = (
                st.text_input(
                    "Staat",
                    value=company.country_other,
                    key="company_country_other_v072",
                )
            )

        st.divider()

        st.subheader(
            "Weitere EU-Niederlassungen"
        )

        has_other = st.radio(
            (
                "Hat das Unternehmen Niederlassungen "
                "in weiteren EU-Mitgliedstaaten?"
            ),
            options=[
                "Nein",
                "Ja",
            ],
            index=(
                1
                if company.has_other_eu_establishments
                else 0
            ),
            horizontal=True,
            key="has_other_eu_v072",
        )

        company.has_other_eu_establishments = (
            has_other == "Ja"
        )

        if company.has_other_eu_establishments:
            count = st.number_input(
                "Anzahl weiterer EU-Mitgliedstaaten",
                min_value=1,
                max_value=26,
                value=max(
                    1,
                    len(
                        company.eu_establishments
                    ),
                ),
                step=1,
                key="eu_count_v072",
            )

            countries = []

            for index in range(
                int(count)
            ):
                options = list(
                    EU_COUNTRIES.keys()
                )

                if company.country in options:
                    options.remove(
                        company.country
                    )

                current = None

                if index < len(
                    company.eu_establishments
                ):
                    current = (
                        company.eu_establishments[
                            index
                        ]
                    )

                selected_index = (
                    options.index(
                        current
                    )
                    if current in options
                    else 0
                )

                value = st.selectbox(
                    f"Niederlassung {index + 1}",
                    options=options,
                    index=selected_index,
                    format_func=lambda code:
                        EU_COUNTRIES[
                            code
                        ],
                    key=(
                        f"eu_establishment_v072_"
                        f"{index}"
                    ),
                )

                countries.append(
                    value
                )

            company.eu_establishments = (
                list(
                    dict.fromkeys(
                        countries
                    )
                )
            )

            st.caption(
                "Bei weiteren Niederlassungen wird "
                "derzeit keine automatische Gleichsetzung "
                "mit einer rechtlich selbständigen "
                "Gesellschaft vorgenommen."
            )

        else:
            company.eu_establishments = []

        st.divider()

        st.subheader(
            "Unternehmensgröße"
        )

        micro_options = list(
            MICRO_STATUS_LABELS.keys()
        )

        company.micro_enterprise_status = (
            st.selectbox(
                (
                    "Ist das Unternehmen ein "
                    "Kleinstunternehmen im Sinne "
                    "der Empfehlung 2003/361/EG?"
                ),
                options=micro_options,
                index=micro_options.index(
                    (
                        company.micro_enterprise_status
                        if company.micro_enterprise_status
                        in micro_options
                        else "clarification_required"
                    )
                ),
                format_func=lambda value:
                    MICRO_STATUS_LABELS[
                        value
                    ],
                key="micro_status_v072",
            )
        )

        st.divider()

        st.subheader(
            "Verpackungsbezogene Tätigkeiten"
        )

        company.activities = st.multiselect(
            (
                "Welche Tätigkeiten führt "
                "das Unternehmen aus?"
            ),
            options=list(
                ACTIVITIES.keys()
            ),
            default=[
                item
                for item in company.activities
                if item in ACTIVITIES
            ],
            format_func=lambda value:
                ACTIVITIES[
                    value
                ],
            key="activities_v072",
        )

        st.divider()

        st.subheader(
            "Beschaffung und Absatz"
        )

        company.procurement_regions = (
            st.multiselect(
                (
                    "Woher werden Verpackungen oder "
                    "verpackte Waren bezogen?"
                ),
                options=list(
                    REGION_OPTIONS.keys()
                ),
                default=[
                    item
                    for item
                    in company.procurement_regions
                    if item in REGION_OPTIONS
                ],
                format_func=lambda value:
                    REGION_OPTIONS[
                        value
                    ],
                key="procurement_regions_v072",
            )
        )

        company.sales_regions = (
            st.multiselect(
                (
                    "In welche Regionen werden "
                    "Waren bzw. Verpackungen abgegeben?"
                ),
                options=list(
                    REGION_OPTIONS.keys()
                ),
                default=[
                    item
                    for item
                    in company.sales_regions
                    if item in REGION_OPTIONS
                ],
                format_func=lambda value:
                    REGION_OPTIONS[
                        value
                    ],
                key="sales_regions_v072",
            )
        )

        st.divider()

        st.subheader(
            "Kundengruppen und Vertriebswege"
        )

        company.customer_types = (
            st.multiselect(
                (
                    "An welche Kundengruppen "
                    "wird geliefert?"
                ),
                options=list(
                    CUSTOMER_TYPES.keys()
                ),
                default=[
                    item
                    for item in company.customer_types
                    if item in CUSTOMER_TYPES
                ],
                format_func=lambda value:
                    CUSTOMER_TYPES[
                        value
                    ],
                key="customer_types_v072",
            )
        )

        company.sales_channels = (
            st.multiselect(
                (
                    "Welche Vertriebswege "
                    "werden genutzt?"
                ),
                options=list(
                    SALES_CHANNELS.keys()
                ),
                default=[
                    item
                    for item in company.sales_channels
                    if item in SALES_CHANNELS
                ],
                format_func=lambda value:
                    SALES_CHANNELS[
                        value
                    ],
                key="sales_channels_v072",
            )
        )

        st.divider()

        st.subheader(
            "Tätigkeitsbereiche"
        )

        company.sector_triggers = (
            st.multiselect(
                (
                    "Welche Tätigkeitsbereiche "
                    "treffen auf das Unternehmen zu?"
                ),
                options=list(
                    SECTOR_TRIGGERS.keys()
                ),
                default=[
                    item
                    for item in company.sector_triggers
                    if item in SECTOR_TRIGGERS
                ],
                format_func=lambda value:
                    SECTOR_TRIGGERS[
                        value
                    ],
                key="sector_triggers_v072",
            )
        )

        st.divider()
        st.subheader("Wiederverwendungssysteme")
        st.caption(
            "Systeme sind Hintergrundobjekte und können mehreren "
            "Verpackungseinheiten zugeordnet werden. In dieser Version "
            "werden nur Name und Systemart erfasst."
        )
        for system in company.reuse_systems:
            system.name = st.text_input(
                f"Systemname ({system.system_id})",
                value=system.name,
                key=f"reuse_system_name_{system.system_id}_v082",
            )
            system.system_type = st.selectbox(
                f"Systemart ({system.system_id})",
                options=["open", "closed", "clarification_required"],
                index=["open", "closed", "clarification_required"].index(
                    system.system_type
                    if system.system_type in {"open", "closed", "clarification_required"}
                    else "clarification_required"
                ),
                format_func=lambda value: {
                    "open": "Offen",
                    "closed": "Geschlossen",
                    "clarification_required": "Klärung erforderlich",
                }[value],
                key=f"reuse_system_type_{system.system_id}_v082",
            )

        if st.button("Wiederverwendungssystem hinzufügen", key="add_reuse_system_v082"):
            next_id = len(company.reuse_systems) + 1
            used_ids = {item.system_id for item in company.reuse_systems}
            while f"SYS-{next_id:03d}" in used_ids:
                next_id += 1
            company.reuse_systems.append(
                ReuseSystem(system_id=f"SYS-{next_id:03d}")
            )
            st.rerun()

    with tab2:
        st.write(
            "Erfasste Verpackungseinheiten: "
            f"**{len(company.packaging_units)}**"
        )

        st.info(
            "Die konkrete Rollenbewertung erfolgt "
            "auf Ebene der jeweiligen "
            "Verpackungseinheit."
        )

    with tab3:
        render_obligation_list(
            build_register(case, collect_case_roles(case)),
            "Konsolidiertes Pflichtenregister",
            editable=True,
            market_flows=[
                flow
                for unit in company.packaging_units
                for flow in unit.market_flows
            ],
        )


# =========================================================
# Marktflüsse
# =========================================================

def render_market_flows(ve):
    st.divider()

    st.subheader(
        "Marktflüsse"
    )

    st.caption(
        "Ein Marktfluss beschreibt einen konkreten "
        "Weg dieser Verpackungseinheit bzw. des "
        "verpackten Produkts zu einem bestimmten "
        "Empfänger."
    )

    if not ve.market_flows:
        st.caption(
            "Noch keine Marktflüsse vorhanden."
        )

    for flow in ve.market_flows:
        source = country_display(
            flow.dispatch_country,
            flow.dispatch_country_other,
        )

        target = country_display(
            flow.target_country,
            flow.target_country_other,
        )

        with st.expander(
            (
                f"{market_flow_reference(flow)} · "
                f"{source} → {target}"
            ),
            expanded=(
                len(
                    ve.market_flows
                )
                == 1
            ),
        ):
            flow.label = st.text_input(
                "Bezeichnung des Marktflusses",
                value=flow.label,
                key=f"flow_label_{ve.ve_id}_{flow.flow_id}",
                help="Frei wählbare Bezeichnung zur leichteren Zuordnung. Die interne Flow-ID bleibt unverändert und eindeutig.",
            )

            col1, col2 = st.columns(
                2
            )

            with col1:
                flow.dispatch_country = (
                    select_from_dict(
                        (
                            "Von welchem Staat aus "
                            "erfolgt dieser Marktfluss?"
                        ),
                        flow.dispatch_country,
                        FLOW_COUNTRY_LABELS,
                        key=(
                            f"flow_source_"
                            f"{ve.ve_id}_"
                            f"{flow.flow_id}"
                        ),
                        help_text=(
                            "Hier ist der tatsächliche "
                            "Ausgangsstaat des Marktflusses "
                            "gemeint. Es muss sich nicht "
                            "um eine eigene Niederlassung "
                            "des Unternehmens handeln."
                        ),
                    )
                )

                if (
                    flow.dispatch_country
                    == "THIRD_COUNTRY"
                ):
                    flow.dispatch_country_other = (
                        st.text_input(
                            "Ausgangs-Drittstaat",
                            value=(
                                flow
                                .dispatch_country_other
                            ),
                            key=(
                                f"flow_source_other_"
                                f"{ve.ve_id}_"
                                f"{flow.flow_id}"
                            ),
                        )
                    )

            with col2:
                flow.target_country = (
                    select_from_dict(
                        (
                            "In welchem Staat wird "
                            "bereitgestellt?"
                        ),
                        flow.target_country,
                        FLOW_COUNTRY_LABELS,
                        key=(
                            f"flow_target_"
                            f"{ve.ve_id}_"
                            f"{flow.flow_id}"
                        ),
                    )
                )

                if (
                    flow.target_country
                    == "THIRD_COUNTRY"
                ):
                    flow.target_country_other = (
                        st.text_input(
                            "Ziel-Drittstaat",
                            value=(
                                flow
                                .target_country_other
                            ),
                            key=(
                                f"flow_target_other_"
                                f"{ve.ve_id}_"
                                f"{flow.flow_id}"
                            ),
                        )
                    )

            st.divider()

            flow.recipient_type = (
                select_from_dict(
                    (
                        "An wen wird die VE bzw. "
                        "das verpackte Produkt "
                        "abgegeben?"
                    ),
                    flow.recipient_type,
                    FLOW_RECIPIENT_LABELS,
                    key=(
                        f"flow_recipient_"
                        f"{ve.ve_id}_"
                        f"{flow.flow_id}"
                    ),
                )
            )

            if (
                flow.target_country
                in EU_COUNTRIES
            ):
                flow.prior_supply_in_target_country = (
                    classification_radio(
                        (
                            "Wurde diese VE bzw. das "
                            "verpackte Produkt vor der "
                            "Abgabe durch Ihr Unternehmen "
                            "bereits von einem anderen "
                            "Unternehmen im Zielland "
                            "angeboten oder abgegeben?"
                        ),
                        (
                            flow
                            .prior_supply_in_target_country
                        ),
                        key=(
                            f"flow_prior_supply_"
                            f"{ve.ve_id}_"
                            f"{flow.flow_id}"
                        ),
                        help_text=(
                            "Diese Frage erfasst den "
                            "tatsächlichen Ablauf. Die "
                            "rechtliche Schlussfolgerung, "
                            "wer Hersteller ist, zieht "
                            "PPWR-Assist anschließend aus "
                            "den Angaben."
                        ),
                    )
                )

            st.caption(
                "Rechtsgrundlage für die spätere "
                "Herstellerprüfung: PPWR Art. 3 "
                "Abs. 1 Nr. 15."
            )

            confirmed = st.checkbox(
                (
                    f"{flow.flow_id} zum "
                    "Löschen markieren"
                ),
                key=(
                    f"confirm_delete_"
                    f"{ve.ve_id}_"
                    f"{flow.flow_id}"
                ),
            )

            if st.button(
                "Marktfluss löschen",
                key=(
                    f"delete_flow_"
                    f"{ve.ve_id}_"
                    f"{flow.flow_id}"
                ),
                disabled=not confirmed,
            ):
                delete_flow(
                    ve,
                    flow.flow_id,
                )

                st.rerun()

    if st.button(
        "➕ Marktfluss hinzufügen",
        key=(
            f"add_flow_"
            f"{ve.ve_id}"
        ),
    ):
        ve.market_flows.append(
            MarketFlow(
                flow_id=next_flow_id()
            )
        )

        st.rerun()

    st.divider()

    st.subheader(
        "Auspacken beim Unternehmen"
    )

    ve.unpacked_without_being_end_user = (
        classification_radio(
            (
                "Packt Ihr Unternehmen diese VE "
                "bzw. das darin gelieferte Produkt "
                "aus, ohne selbst Endabnehmer des "
                "verpackten Produkts zu sein?"
            ),
            ve.unpacked_without_being_end_user,
            key=(
                f"unpacking_"
                f"{ve.ve_id}"
            ),
            help_text=(
                "Diese Angabe wird für den "
                "Herstellertatbestand nach "
                "Art. 3 Abs. 1 Nr. 15 Buchst. e "
                "verwendet."
            ),
        )
    )

    st.caption(
        "Quelle: PPWR Art. 3 Abs. 1 "
        "Nr. 15 Buchst. e."
    )


# =========================================================
# VE
# =========================================================

def render_ve_detail(ve):
    with st.container(key="detail_panel_heading"):
        st.header(
            f"{ve.ve_id} – {ve.name}"
        )

    tab1, tab2, tab3 = st.tabs(
        [
            "Übersicht",
            "Rollen & Pflichten",
            "Dokumentation & Ausblick",
        ]
    )

    with tab1:
        st.subheader(
            "Grunddaten"
        )

        name_key = (
            f"name_{ve.ve_id}"
        )

        init_widget_state(
            name_key,
            ve.name,
        )

        st.text_input(
            "Bezeichnung der Verpackungseinheit",
            key=name_key,
            on_change=update_ve_name,
            args=(
                ve.ve_id,
            ),
        )

        col1, col2 = st.columns(
            2
        )

        with col1:
            ve.product_name = st.text_input(
                "Produkt / Inhalt",
                value=ve.product_name,
                key=(
                    f"product_"
                    f"{ve.ve_id}"
                ),
            )

        with col2:
            ve.product_group = st.text_input(
                "Produktgruppe",
                value=ve.product_group,
                key=(
                    f"group_"
                    f"{ve.ve_id}"
                ),
            )

        amount = st.number_input(
            (
                "Jährliche Anzahl dieser "
                "Verpackungseinheiten (optional)"
            ),
            min_value=0,
            value=(
                ve.annual_units
                if ve.annual_units is not None
                else 0
            ),
            step=1,
            key=(
                f"amount_"
                f"{ve.ve_id}"
            ),
        )

        ve.annual_units = (
            int(
                amount
            )
            if amount > 0
            else None
        )

        description_key = (
            f"description_"
            f"{ve.ve_id}"
        )

        init_widget_state(
            description_key,
            ve.description,
        )

        st.text_area(
            "Beschreibung",
            key=description_key,
            on_change=update_ve_description,
            args=(
                ve.ve_id,
            ),
        )

        st.divider()

        with st.expander(
            "🗑️ Verpackungseinheit löschen"
        ):
            confirmed = st.checkbox(
                (
                    f"{ve.ve_id} "
                    "wirklich löschen"
                ),
                key=(
                    f"confirm_delete_"
                    f"{ve.ve_id}"
                ),
            )

            if st.button(
                "VE endgültig löschen",
                key=(
                    f"delete_"
                    f"{ve.ve_id}"
                ),
                disabled=not confirmed,
            ):
                delete_ve(
                    ve.ve_id
                )

                st.rerun()

        st.divider()

        # -------------------------------------------------
        # Bestandteile
        # -------------------------------------------------

        st.subheader(
            "Bestandteile"
        )

        for pkg in ve.components:
            st.write(
                f"**{pkg.pkg_id}** – "
                f"{pkg.name}"
            )

        if not ve.components:
            st.caption(
                "Noch keine Bestandteile vorhanden."
            )

        if st.button(
            "➕ Bestandteil hinzufügen",
            key=(
                f"add_pkg_"
                f"{ve.ve_id}"
            ),
        ):
            pkg = PackagingComponent(
                pkg_id=next_pkg_id(),
                name="Neuer Bestandteil",
            )

            ve.components.append(
                pkg
            )

            open_ve(
                ve.ve_id
            )

            select_object(
                "pkg",
                pkg.pkg_id,
                ve.ve_id,
            )

            st.rerun()

        st.divider()

        # -------------------------------------------------
        # Bezugsweg
        # -------------------------------------------------

        st.subheader(
            "Bezugsweg der VE / des verpackten Produkts"
        )

        ve.packaged_product_source = (
            select_from_dict(
                (
                    "Wie gelangt die betrachtete VE "
                    "bzw. das bereits verpackte Produkt "
                    "zu Ihrem Unternehmen?"
                ),
                ve.packaged_product_source,
                PACKAGED_PRODUCT_SOURCE_LABELS,
                key=(
                    f"packaged_source_"
                    f"{ve.ve_id}"
                ),
                help_text=(
                    "Diese Angabe betrifft den Bezug "
                    "der bereits vorhandenen VE bzw. "
                    "des verpackten Produkts. Sie ist "
                    "von der Beschaffung einzelner "
                    "PKG zu unterscheiden."
                ),
            )
        )

        st.caption(
            "Die Angabe wird insbesondere für die "
            "Prüfung von Importeur, Vertreiber und "
            "Hersteller verwendet."
        )

        st.divider()

        # -------------------------------------------------
        # Auftragsentwicklung / Name / Marke
        # -------------------------------------------------

        st.subheader(
            "Auftragsentwicklung / eigener Name / eigene Marke"
        )

        ve.own_name_or_brand = (
            classification_radio(
                (
                    "Lässt Ihr Unternehmen diese "
                    "Verpackung oder das bereits "
                    "verpackte Produkt von einem "
                    "anderen Unternehmen unter Ihrem "
                    "eigenen Namen oder Ihrer eigenen "
                    "Marke entwickeln oder herstellen?"
                ),
                ve.own_name_or_brand,
                key=(
                    f"own_brand_"
                    f"{ve.ve_id}"
                ),
                help_text=(
                    "Gemeint ist eine Auftragsentwicklung "
                    "oder Auftragsherstellung durch ein "
                    "anderes Unternehmen. Nicht gemeint "
                    "ist allein, dass Ihr Unternehmen "
                    "selbst befüllt und das eigene Produkt "
                    "unter eigenem Namen vertreibt."
                ),
            )
        )

        st.caption(
            "Quelle: PPWR Art. 3 Abs. 1 "
            "Nr. 13 Buchst. a und b."
        )

        st.divider()

        # -------------------------------------------------
        # Funktionen
        # -------------------------------------------------

        st.subheader(
            "Funktionen der Verpackungseinheit"
        )

        ve.packaging_functions = (
            st.multiselect(
                (
                    "Welche Funktionen erfüllt "
                    "die VE?"
                ),
                options=list(
                    PACKAGING_FUNCTIONS.keys()
                ),
                default=[
                    item
                    for item in ve.packaging_functions
                    if item
                    in PACKAGING_FUNCTIONS
                ],
                format_func=lambda value:
                    PACKAGING_FUNCTIONS[
                        value
                    ],
                key=(
                    f"functions_"
                    f"{ve.ve_id}"
                ),
            )
        )

        st.divider()

        # -------------------------------------------------
        # Verpackungsart
        # -------------------------------------------------

        st.subheader(
            "Ermittlung der Verpackungsart"
        )

        answers = (
            ve.classification_answers
        )

        answers["sales_unit"] = (
            classification_radio(
                (
                    "Bildet die Verpackung zusammen "
                    "mit dem Produkt für den "
                    "Endabnehmer in der Verkaufsstelle "
                    "eine Verkaufseinheit?"
                ),
                answers.get(
                    "sales_unit"
                ),
                key=(
                    f"class_sales_"
                    f"{ve.ve_id}"
                ),
                packaging_type_label=(
                    "Verkaufsverpackung"
                ),
            )
        )

        answers["grouped_sales_units"] = (
            classification_radio(
                (
                    "Ist die Verpackung so konzipiert, "
                    "dass sie in der Verkaufsstelle "
                    "eine Zusammenstellung von "
                    "Verkaufseinheiten enthält und "
                    "entfernt werden kann, ohne die "
                    "Eigenschaften des Produkts zu "
                    "beeinträchtigen?"
                ),
                answers.get(
                    "grouped_sales_units"
                ),
                key=(
                    f"class_grouped_"
                    f"{ve.ve_id}"
                ),
                packaging_type_label=(
                    "Umverpackung"
                ),
            )
        )

        answers["transport_function"] = (
            classification_radio(
                (
                    "Ist die Verpackung so konzipiert, "
                    "dass sie Handhabung und Transport "
                    "von einer oder mehreren "
                    "Verkaufseinheiten erleichtert "
                    "und dabei eine Beschädigung des "
                    "Produkts vermeiden soll?"
                ),
                answers.get(
                    "transport_function"
                ),
                key=(
                    f"class_transport_"
                    f"{ve.ve_id}"
                ),
                packaging_type_label=(
                    "Transportverpackung"
                ),
            )
        )

        # -------------------------------------------------
        # E-Commerce ist ein Zusatzmerkmal der
        # Transportverpackung und wird deshalb unmittelbar
        # darunter angezeigt.
        # -------------------------------------------------

        if (
            answers.get(
                "transport_function"
            )
            == "yes"
        ):
            answers["ecommerce_delivery"] = (
                classification_radio(
                    (
                        "Wird diese Transportverpackung "
                        "für die Lieferung von Produkten "
                        "aus Online-Verkäufen oder "
                        "sonstigem Fernabsatz an den "
                        "Endabnehmer verwendet?"
                    ),
                    answers.get(
                        "ecommerce_delivery"
                    ),
                    key=(
                        f"class_ecommerce_"
                        f"{ve.ve_id}"
                    ),
                    packaging_type_label=(
                        "Zusatzmerkmal: Verpackung für "
                        "den elektronischen Handel"
                    ),
                )
            )

            st.caption(
                "Quelle: PPWR Art. 3 Abs. 1 Nr. 8. "
                "Verpackungen für den elektronischen "
                "Handel sind Transportverpackungen."
            )

        elif (
            answers.get(
                "transport_function"
            )
            == "no"
        ):
            answers[
                "ecommerce_delivery"
            ] = "no"

        else:
            answers[
                "ecommerce_delivery"
            ] = "clarification_required"

        answers["service_point_of_sale"] = (
            classification_radio(
                (
                    "Ist die Verpackung für die "
                    "Befüllung in der Verkaufsstelle "
                    "zur Übergabe des Produkts "
                    "konzipiert und vorgesehen?"
                ),
                answers.get(
                    "service_point_of_sale"
                ),
                key=(
                    f"class_service_"
                    f"{ve.ve_id}"
                ),
                packaging_type_label=(
                    "Serviceverpackung"
                ),
            )
        )

        answers["primary_production"] = (
            classification_radio(
                (
                    "Ist die Verpackung als Verpackung "
                    "für ein unverarbeitetes Erzeugnis "
                    "aus Primärproduktion gestaltet "
                    "und bestimmt?"
                ),
                answers.get(
                    "primary_production"
                ),
                key=(
                    f"class_primary_"
                    f"{ve.ve_id}"
                ),
                packaging_type_label=(
                    "Primärproduktionsverpackung"
                ),
            )
        )

        evaluate_packaging_types(
            ve
        )

        st.divider()

        # -------------------------------------------------
        # Ergebnis Verpackungsart
        # -------------------------------------------------

        st.subheader(
            "Ergebnis der Einordnung"
        )

        candidates = (
            ve.packaging_type_candidates
        )

        if not candidates:
            st.warning(
                "Noch keine Verpackungsart "
                "eindeutig ermittelt."
            )

        for packaging_type in candidates:
            with st.container(
                border=True
            ):
                st.markdown(
                    "#### ✓ "
                    + PACKAGING_TYPE_LABELS[
                        packaging_type
                    ]
                )

                for reason in (
                    ve.classification_reasons.get(
                        packaging_type,
                        [],
                    )
                ):
                    st.write(
                        reason
                    )

                st.caption(
                    "Quelle: "
                    + PACKAGING_TYPE_SOURCES[
                        packaging_type
                    ]
                )

        if (
            ve.is_ecommerce_packaging
            == "yes"
        ):
            with st.container(
                border=True
            ):
                st.markdown(
                    "#### ✓ Zusatzmerkmal: "
                    "Verpackung für den elektronischen Handel"
                )

                st.write(
                    "Die Transportverpackung wird nach "
                    "der Angabe des Anwenders für die "
                    "Lieferung aus Online-Verkäufen oder "
                    "sonstigem Fernabsatz an den "
                    "Endabnehmer verwendet."
                )

                st.caption(
                    "Quelle: PPWR Art. 3 Abs. 1 Nr. 8."
                )

        unresolved = any(
            answers.get(
                key
            ) == "clarification_required"
            for key in [
                "sales_unit",
                "grouped_sales_units",
                "transport_function",
                "service_point_of_sale",
                "primary_production",
            ]
        )

        if unresolved:
            st.warning(
                "Mindestens eine Grundfrage ist "
                "noch nicht geklärt."
            )

        if len(
            candidates
        ) > 1:
            options = [
                ""
            ] + candidates

            selected_primary = (
                st.selectbox(
                    (
                        "Führende Verpackungsart "
                        "für die Bewertung"
                    ),
                    options=options,
                    index=(
                        options.index(
                            ve.primary_packaging_type
                        )
                        if (
                            ve.primary_packaging_type
                            in options
                        )
                        else 0
                    ),
                    format_func=lambda value:
                        (
                            "Bitte auswählen"
                            if value == ""
                            else
                            PACKAGING_TYPE_LABELS[
                                value
                            ]
                        ),
                    key=(
                        f"primary_"
                        f"{ve.ve_id}"
                    ),
                )
            )

            ve.primary_packaging_type = (
                selected_primary
                or None
            )

            st.warning(
                "Die führende Verpackungsart steuert die besondere "
                "Primärproduktionsprüfung. Weitere zutreffende "
                "Verpackungsarten bleiben bestehen."
            )

        elif len(
            candidates
        ) == 1:
            ve.primary_packaging_type = (
                candidates[
                    0
                ]
            )

        # -------------------------------------------------
        # Fertigstellung
        # -------------------------------------------------

        if candidates:
            st.divider()

            st.subheader(
                "Fertigstellung der Verpackungseinheit"
            )

        if (
            "sales" in candidates
            or
            "grouped" in candidates
        ):
            st.markdown(
                "#### Verkaufs- / Umverpackung"
            )

            ve.self_filling_sales_grouped = (
                classification_radio(
                    (
                        "Befüllt bzw. bestückt Ihr "
                        "Unternehmen diese Verpackung "
                        "selbst?"
                    ),
                    ve.self_filling_sales_grouped,
                    key=(
                        f"self_fill_"
                        f"{ve.ve_id}"
                    ),
                )
            )

            ve.additional_processing_steps = (
                st.multiselect(
                    (
                        "Welche weiteren "
                        "Verarbeitungsschritte nimmt "
                        "Ihr Unternehmen selbst vor?"
                    ),
                    options=list(
                        PROCESSING_STEP_LABELS.keys()
                    ),
                    default=[
                        item
                        for item
                        in ve.additional_processing_steps
                        if item
                        in PROCESSING_STEP_LABELS
                    ],
                    format_func=lambda value:
                        PROCESSING_STEP_LABELS[
                            value
                        ],
                    key=(
                        f"processing_"
                        f"{ve.ve_id}"
                    ),
                )
            )

            st.caption(
                "Die Befüllung bzw. Bestückung wird "
                "separat abgefragt."
            )

        if (
            "transport"
            in candidates
        ):
            st.markdown(
                "#### Transportverpackung"
            )

            render_transport_component_function_check(
                ve
            )

            ve.transport_function_created_by_assembly = (
                classification_radio(
                    (
                        "Entsteht die funktionsfähige "
                        "Transportverpackung erst "
                        "dadurch, dass Ihr Unternehmen "
                        "mehrere Bestandteile "
                        "zusammensetzt?"
                    ),
                    (
                        ve
                        .transport_function_created_by_assembly
                    ),
                    key=(
                        f"transport_assembly_"
                        f"{ve.ve_id}"
                    ),
                    help_text=(
                        "Entscheidend ist, ob erst "
                        "durch das Zusammenfügen die "
                        "Verpackungsfunktion entsteht."
                    ),
                )
            )

            component_values = [
                pkg.independent_packaging_function
                for pkg in ve.components
            ]

            all_components_yes = (
                bool(
                    component_values
                )
                and
                all(
                    value == "yes"
                    for value
                    in component_values
                )
            )

            if (
                all_components_yes
                and
                ve.transport_function_created_by_assembly
                == "yes"
            ):
                st.warning(
                    "Plausibilitätsprüfung: Alle PKG "
                    "wurden als bereits eigenständig "
                    "funktionsfähige Verpackungen "
                    "erfasst. Gleichzeitig wurde "
                    "angegeben, dass die "
                    "Verpackungsfunktion erst durch "
                    "das Zusammenfügen entsteht. "
                    "Bitte die Angaben prüfen."
                )

            st.caption(
                "Quelle für diese Auslegung: "
                "Kommissionsleitlinie C/2026/3084 "
                "vom 10.06.2026, S. 8/37."
            )

        render_market_flows(
            ve
        )

        render_special_path_inputs(ve)

    with tab2:
        render_roles(
            ve
        )
        render_packaging_obligations(ve)

    with tab3:
        render_documentation_outlook(ve)


# =========================================================
# PKG
# =========================================================

def render_pkg_detail(
    ve,
    pkg,
):
    st.header(
        f"{pkg.pkg_id} – {pkg.name}"
    )

    st.caption(
        f"Bestandteil von "
        f"{ve.ve_id} – {ve.name}"
    )

    tab1, tab2 = st.tabs(
        [
            "Bestandteil",
            "Beschaffung & Lieferkette",
        ]
    )

    with tab1:
        name_key = (
            f"name_"
            f"{ve.ve_id}_"
            f"{pkg.pkg_id}"
        )

        material_key = (
            f"material_"
            f"{ve.ve_id}_"
            f"{pkg.pkg_id}"
        )

        weight_key = (
            f"weight_"
            f"{ve.ve_id}_"
            f"{pkg.pkg_id}"
        )

        init_widget_state(
            name_key,
            pkg.name,
        )

        init_widget_state(
            material_key,
            pkg.material,
        )

        init_widget_state(
            weight_key,
            float(
                pkg.weight_g
                or 0.0
            ),
        )

        st.text_input(
            "Bezeichnung",
            key=name_key,
            on_change=update_pkg_name,
            args=(
                ve.ve_id,
                pkg.pkg_id,
            ),
        )

        st.text_input(
            "Hauptmaterial",
            key=material_key,
            on_change=update_pkg_material,
            args=(
                ve.ve_id,
                pkg.pkg_id,
            ),
            help=(
                "Zum Beispiel Papier, Glas, "
                "Stahl, Aluminium oder Kunststoff."
            ),
        )

        pkg.food_contact = st.checkbox(
            "Lebensmittelkontakt",
            value=pkg.food_contact,
            key=f"food_contact_{ve.ve_id}_{pkg.pkg_id}_v082",
        )

        st.markdown(
            "**Materialunterarten / Beschichtungen / "
            "weitere Stoffe**"
        )

        st.caption(
            "Zum Beispiel Kleber, Druckfarbe, Lack, "
            "Innenbeschichtung, Gummierung oder Zink."
        )

        minus_col, count_col, plus_col, _ = (
            st.columns(
                [
                    0.08,
                    0.20,
                    0.08,
                    0.64,
                ]
            )
        )

        with minus_col:
            st.button(
                "−",
                key=(
                    f"minus_subtype_"
                    f"{ve.ve_id}_"
                    f"{pkg.pkg_id}"
                ),
                disabled=(
                    len(
                        pkg.material_subtypes
                    )
                    == 0
                ),
                on_click=remove_material_subtype,
                args=(
                    ve.ve_id,
                    pkg.pkg_id,
                ),
            )

        with count_col:
            st.markdown(
                (
                    f"**Anzahl: "
                    f"{len(pkg.material_subtypes)}**"
                )
            )

        with plus_col:
            st.button(
                "+",
                key=(
                    f"plus_subtype_"
                    f"{ve.ve_id}_"
                    f"{pkg.pkg_id}"
                ),
                on_click=add_material_subtype,
                args=(
                    ve.ve_id,
                    pkg.pkg_id,
                ),
            )

        values = []

        for index, subtype in enumerate(
            pkg.material_subtypes
        ):
            key = (
                f"material_subtype_"
                f"{ve.ve_id}_"
                f"{pkg.pkg_id}_"
                f"{index}"
            )

            init_widget_state(
                key,
                subtype,
            )

            values.append(
                st.text_input(
                    (
                        f"Materialunterart "
                        f"{index + 1}"
                    ),
                    key=key,
                )
            )

        pkg.material_subtypes = (
            values
        )

        st.caption(
            "Quelle für die spätere "
            "Recyclingfähigkeitsprüfung: "
            "PPWR Anhang II Tabelle 4."
        )

        st.number_input(
            "Gewicht in g",
            min_value=0.0,
            step=1.0,
            key=weight_key,
            on_change=update_pkg_weight,
            args=(
                ve.ve_id,
                pkg.pkg_id,
            ),
        )

        st.divider()

        with st.expander(
            "🗑️ Bestandteil löschen"
        ):
            confirmed = st.checkbox(
                (
                    f"{pkg.pkg_id} "
                    "wirklich löschen"
                ),
                key=(
                    f"confirm_delete_"
                    f"{ve.ve_id}_"
                    f"{pkg.pkg_id}"
                ),
            )

            if st.button(
                "Bestandteil endgültig löschen",
                key=(
                    f"delete_"
                    f"{ve.ve_id}_"
                    f"{pkg.pkg_id}"
                ),
                disabled=not confirmed,
            ):
                delete_pkg(
                    ve.ve_id,
                    pkg.pkg_id,
                )

                st.rerun()

    with tab2:
        st.subheader(
            "Beschaffung"
        )

        pkg.procurement_type = (
            select_from_dict(
                (
                    "Wie wird dieser Bestandteil "
                    "bezogen?"
                ),
                pkg.procurement_type,
                PROCUREMENT_TYPE_LABELS,
                key=(
                    f"procurement_"
                    f"{ve.ve_id}_"
                    f"{pkg.pkg_id}"
                ),
            )
        )

        if (
            pkg.procurement_type
            != "self_manufactured"
        ):
            pkg.supplier_name = (
                st.text_input(
                    (
                        "Lieferant / Unternehmen "
                        "(optional)"
                    ),
                    value=(
                        pkg.supplier_name
                    ),
                    key=(
                        f"supplier_name_"
                        f"{ve.ve_id}_"
                        f"{pkg.pkg_id}"
                    ),
                )
            )

            pkg.supplier_country = (
                select_from_dict(
                    "Sitzstaat des Lieferanten",
                    pkg.supplier_country,
                    SUPPLIER_COUNTRY_LABELS,
                    key=(
                        f"supplier_country_"
                        f"{ve.ve_id}_"
                        f"{pkg.pkg_id}"
                    ),
                )
            )

            if (
                pkg.supplier_country
                == "THIRD_COUNTRY"
            ):
                pkg.supplier_country_other = (
                    st.text_input(
                        "Drittstaat",
                        value=(
                            pkg
                            .supplier_country_other
                        ),
                        key=(
                            f"supplier_other_"
                            f"{ve.ve_id}_"
                            f"{pkg.pkg_id}"
                        ),
                    )
                )

        st.divider()

        st.subheader(
            "Gegenstand"
        )

        if (
            pkg.procurement_type
            == "self_manufactured"
        ):
            question = (
                "Was stellt Ihr Unternehmen bezogen "
                "auf die hier betrachtete VE her?"
            )

        else:
            question = (
                "Was liefert der Lieferant bezogen "
                "auf die hier betrachtete VE?"
            )

        pkg.supplied_object_type = (
            select_from_dict(
                question,
                pkg.supplied_object_type,
                SUPPLIED_OBJECT_TYPE_LABELS,
                key=(
                    f"supplied_object_"
                    f"{ve.ve_id}_"
                    f"{pkg.pkg_id}"
                ),
                help_text=(
                    "Die Angabe beschreibt, ob die "
                    "vollständige VE, ein Bestandteil "
                    "oder lediglich Ausgangsmaterial "
                    "bezogen bzw. hergestellt wird."
                ),
            )
        )

        st.markdown(
            "**Verpackungsfunktion des Bestandteils**"
        )

        pkg.independent_packaging_function = (
            classification_radio(
                (
                    "Kann dieser Bestandteil bereits "
                    "für sich – also ohne das "
                    "Zusammenfügen mit den übrigen PKG "
                    "dieser VE – eine Verpackungsfunktion "
                    "erfüllen?"
                ),
                pkg.independent_packaging_function,
                key=(
                    f"independent_function_"
                    f"{ve.ve_id}_"
                    f"{pkg.pkg_id}"
                ),
                help_text=(
                    "Bei Transportverpackungen ist nach "
                    "der Kommissionsleitlinie insbesondere "
                    "zu prüfen, ob der Gegenstand bereits "
                    "selbst eine Verpackungsfunktion "
                    "erfüllen kann."
                ),
            )
        )

        st.caption(
            "Quelle für Transportverpackungen: "
            "Kommissionsleitlinie C/2026/3084 "
            "vom 10.06.2026, S. 8/37."
        )

        render_independent_packaging_function_notice(
            ve,
            pkg,
        )

        st.divider()

        st.subheader(
            "Einfügen / Anbringen"
        )

        pkg.integration_actor = (
            select_from_dict(
                (
                    "Wer fügt diesen Bestandteil in "
                    "die fertige VE ein bzw. bringt "
                    "ihn an?"
                ),
                pkg.integration_actor,
                INTEGRATION_ACTOR_LABELS,
                key=(
                    f"integration_"
                    f"{ve.ve_id}_"
                    f"{pkg.pkg_id}"
                ),
            )
        )

        st.divider()

        st.subheader(
            "Zusammenfassung"
        )

        with st.container(
            border=True
        ):
            st.write(
                "**Bezugsart:** "
                + PROCUREMENT_TYPE_LABELS.get(
                    pkg.procurement_type,
                    "Klärung erforderlich",
                )
            )

            st.write(
                "**Gegenstand:** "
                + SUPPLIED_OBJECT_TYPE_LABELS.get(
                    pkg.supplied_object_type,
                    "Klärung erforderlich",
                )
            )

            st.write(
                "**Bereits eigenständig "
                "verpackungsfunktionsfähig:** "
                + TRI_STATE_LABELS.get(
                    pkg.independent_packaging_function,
                    "Klärung erforderlich",
                )
            )

            st.write(
                "**Einfügen / Anbringen:** "
                + INTEGRATION_ACTOR_LABELS.get(
                    pkg.integration_actor,
                    "Klärung erforderlich",
                )
            )

            st.write(
                "**Materialunterarten:** "
                f"{len(pkg.material_subtypes)}"
            )

            st.write(
                "**Lebensmittelkontakt:** "
                + ("Ja" if pkg.food_contact else "Nein")
            )

            same_ms = (
                supplier_same_member_state_status(
                    pkg
                )
            )

            if same_ms == "yes":
                st.write(
                    "**Lieferant im selben "
                    "Mitgliedstaat:** Ja"
                )

            elif same_ms == "no":
                st.write(
                    "**Lieferant im selben "
                    "Mitgliedstaat:** Nein"
                )

            elif (
                same_ms
                == "clarification_required"
            ):
                st.write(
                    "**Lieferant im selben "
                    "Mitgliedstaat:** "
                    "Klärung erforderlich"
                )


# =========================================================
# Hauptansicht
# =========================================================

st.title(
    "📦 PPWR-Assist"
)

st.caption(
    "Geführte Erfassung und Bewertung von "
    "Verpackungen nach der Verordnung "
    "(EU) 2025/40."
)


left, right = st.columns(
    [1, 3],
    gap="large",
)


with left:
    with st.expander("Prüffall exportieren / importieren"):
        st.download_button(
            "JSON exportieren",
            data=case_to_json(case),
            file_name=f"{case.case_id}.json",
            mime="application/json",
            use_container_width=True,
        )
        uploaded_case = st.file_uploader(
            "JSON-Prüffall importieren",
            type=["json"],
            key="case_import_file",
        )
        st.button(
            "Prüffall laden",
            key="import_case_button",
            use_container_width=True,
            disabled=uploaded_case is None,
            on_click=load_uploaded_case,
        )
        if st.session_state.get("case_import_error"):
            st.error(st.session_state["case_import_error"])

    render_structure_tree()


with right:
    selected = (
        st.session_state.selected_object
    )

    if (
        selected["type"]
        == "company"
    ):
        render_company_detail()

    elif (
        selected["type"]
        == "ve"
    ):
        ve = find_ve(
            selected["id"]
        )

        if ve:
            render_ve_detail(
                ve
            )

        else:
            st.error(
                "Verpackungseinheit nicht gefunden."
            )

    elif (
        selected["type"]
        == "pkg"
    ):
        ve, pkg = find_pkg(
            selected["id"],
            selected.get(
                "parent_id"
            ),
        )

        if ve and pkg:
            render_pkg_detail(
                ve,
                pkg,
            )

        else:
            st.error(
                "Bestandteil nicht gefunden."
            )


# =========================================================
# Entwicklungsinformationen
# =========================================================

st.divider()

with st.expander(
    "Entwicklungsinformationen"
):
    st.write(
        f"Fall-ID: {case.case_id}"
    )

    st.write(
        f"Schema-Version: "
        f"{case.schema_version}"
    )

    st.write(
        f"Regelwerk-Version: "
        f"{case.ruleset_version}"
    )

    st.write(
        f"Prüfdatum: "
        f"{case.assessment_date}"
    )

    st.write(
        "Verpackungseinheiten: "
        f"{len(company.packaging_units)}"
    )

    st.write(
        "Verpackungsbestandteile: "
        + str(
            sum(
                len(
                    ve.components
                )
                for ve
                in company.packaging_units
            )
        )
    )

    st.write(
        "Marktflüsse: "
        + str(
            sum(
                len(
                    ve.market_flows
                )
                for ve
                in company.packaging_units
            )
        )
    )
