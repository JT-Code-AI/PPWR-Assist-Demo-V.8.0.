"""Helpers for stable reuse-system identifiers and links."""

from src.models import Company, ReuseSystem


def sync_next_reuse_system_number(company: Company) -> int:
    """Keep the next number above every active or referenced SYS identifier."""
    identifiers = {
        system.system_id for system in company.reuse_systems if system.system_id
    }
    identifiers.update(
        ve.reuse_system_id
        for ve in company.packaging_units
        if ve.reuse_system_id
    )
    used_numbers = []
    for identifier in identifiers:
        if identifier.startswith("SYS-"):
            try:
                used_numbers.append(int(identifier[4:]))
            except ValueError:
                continue
    company.reuse_system_next_number = max(
        int(company.reuse_system_next_number or 1),
        max(used_numbers, default=0) + 1,
    )
    return company.reuse_system_next_number


def add_reuse_system(company: Company) -> ReuseSystem:
    """Add a system with a never-reused sequential identifier."""
    next_number = sync_next_reuse_system_number(company)
    identifiers = {
        system.system_id for system in company.reuse_systems if system.system_id
    }
    identifiers.update(
        ve.reuse_system_id
        for ve in company.packaging_units
        if ve.reuse_system_id
    )
    while f"SYS-{next_number:03d}" in identifiers:
        next_number += 1
    system = ReuseSystem(system_id=f"SYS-{next_number:03d}")
    company.reuse_systems.append(system)
    company.reuse_system_next_number = next_number + 1
    return system


def delete_reuse_system(company: Company, system_id: str) -> bool:
    """Delete a system and clear VE links without rolling back its number."""
    system = next(
        (item for item in company.reuse_systems if item.system_id == system_id),
        None,
    )
    if system is None:
        return False
    sync_next_reuse_system_number(company)
    company.reuse_systems.remove(system)
    for ve in company.packaging_units:
        if ve.reuse_system_id == system_id:
            ve.reuse_system_id = None
    return True
