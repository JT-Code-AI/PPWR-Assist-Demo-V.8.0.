"""Session-state setup for a successfully imported assessment case."""


def _numeric_suffix(value: str) -> int:
    try:
        return int(value.split("-")[-1])
    except (ValueError, AttributeError, IndexError):
        return 0


def install_imported_case(session_state, imported_case) -> None:
    """Replace the active case and discard widget values from the prior case."""
    try:
        widget_generation = int(session_state.get("widget_generation", 0)) + 1
    except (TypeError, ValueError):
        widget_generation = 1
    session_state.clear()
    session_state["widget_generation"] = widget_generation
    session_state["case"] = imported_case
    session_state["selected_object"] = {
        "type": "company",
        "id": imported_case.company.company_id,
    }
    session_state["expanded_ves"] = set()
    session_state["next_ve_number"] = max(
        (_numeric_suffix(ve.ve_id) for ve in imported_case.company.packaging_units),
        default=0,
    ) + 1
    session_state["next_pkg_number"] = max(
        (
            _numeric_suffix(pkg.pkg_id)
            for ve in imported_case.company.packaging_units
            for pkg in ve.components
        ),
        default=0,
    ) + 1
    session_state["next_flow_number"] = max(
        (
            _numeric_suffix(flow.flow_id)
            for ve in imported_case.company.packaging_units
            for flow in ve.market_flows
        ),
        default=0,
    ) + 1
