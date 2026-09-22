"""Pure warning logic for an emergency route record (Phase E4). No I/O, so it is unit-testable."""


def build_warnings(dry_minutes, flood_minutes, dry_cat, flood_cat, dry_backup_minutes,
                    target_minutes, flood_path_crosses_flood):
    """Return a list of short, plain-language warnings for one point's dry/flood pair."""
    warnings = []
    if dry_minutes is None:
        warnings.append("no route to any qualifying facility in the dry season")
    if flood_minutes is None:
        warnings.append("no route to any qualifying facility in the flood")
    if dry_cat is not None and flood_cat is not None and dry_cat != flood_cat:
        warnings.append("the nearest qualifying facility changes in the flood")
    if dry_minutes is not None and flood_minutes is not None and flood_minutes - dry_minutes >= 15:
        warnings.append(f"the flood adds {round(flood_minutes - dry_minutes)} minutes")
    if dry_minutes is not None and target_minutes is not None and dry_minutes > target_minutes:
        warnings.append("outside the target time even in the dry season")
    elif (
        flood_minutes is not None and target_minutes is not None and flood_minutes > target_minutes
        and dry_minutes is not None and dry_minutes <= target_minutes
    ):
        warnings.append("the flood pushes this point beyond the target time")
    if dry_backup_minutes is not None and dry_minutes is not None:
        if dry_backup_minutes - dry_minutes >= 20 and dry_backup_minutes >= dry_minutes * 1.5:
            warnings.append("the backup facility is much slower than the first choice")
    if flood_path_crosses_flood:
        warnings.append("the flood-season path crosses flooded ground")
    return warnings
