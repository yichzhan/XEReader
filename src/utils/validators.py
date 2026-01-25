"""Data validation utilities"""
from typing import List, Set
from ..models.activity import Activity


class ValidationError(Exception):
    """Raised when data validation fails"""
    pass


def validate_activities(activities: List[Activity], strict: bool = True) -> List[str]:
    """
    Validate activities data

    Args:
        activities: List of Activity objects
        strict: If True, raise ValidationError on duplicate task codes.
                If False, return warnings instead.

    Returns:
        List of warning messages (empty if no issues or strict=True)

    Raises:
        ValidationError: If validation fails (always for missing activities,
                        only for duplicates if strict=True)
    """
    warnings = []

    if not activities:
        raise ValidationError("No activities found")

    # Check for duplicate task_codes
    task_codes = [a.task_code for a in activities]
    duplicates = [code for code in task_codes if task_codes.count(code) > 1]
    if duplicates:
        msg = f"Duplicate task codes found: {set(duplicates)}"
        if strict:
            raise ValidationError(msg)
        else:
            warnings.append(msg)

    # Validate each activity
    task_code_set = set(task_codes)
    for activity in activities:
        validate_activity(activity, task_code_set)

    return warnings


def validate_activity(activity: Activity, all_task_codes: Set[str]) -> None:
    """
    Validate a single activity

    Args:
        activity: Activity object
        all_task_codes: Set of all valid task codes

    Raises:
        ValidationError: If validation fails
    """
    # Required fields
    if not activity.task_code:
        raise ValidationError("Activity missing task_code")

    if not activity.task_name:
        raise ValidationError(f"Activity {activity.task_code} missing task_name")

    # Date validation
    if activity.planned_start_date and activity.planned_end_date:
        if activity.planned_end_date < activity.planned_start_date:
            raise ValidationError(
                f"Activity {activity.task_code}: planned_end_date before planned_start_date"
            )

    if activity.actual_end_date and not activity.actual_start_date:
        raise ValidationError(
            f"Activity {activity.task_code}: has actual_end_date but no actual_start_date"
        )

    # Dependency validation
    for dep in activity.predecessors:
        if dep.task_code not in all_task_codes:
            raise ValidationError(
                f"Activity {activity.task_code}: predecessor {dep.task_code} not found"
            )
        if dep.dependency_type not in ['FS', 'SS', 'FF', 'SF']:
            raise ValidationError(
                f"Activity {activity.task_code}: invalid dependency type {dep.dependency_type}"
            )

    for dep in activity.successors:
        if dep.task_code not in all_task_codes:
            raise ValidationError(
                f"Activity {activity.task_code}: successor {dep.task_code} not found"
            )
        if dep.dependency_type not in ['FS', 'SS', 'FF', 'SF']:
            raise ValidationError(
                f"Activity {activity.task_code}: invalid dependency type {dep.dependency_type}"
            )


def validate_required_tables(parser, required_tables: List[str]) -> None:
    """
    Validate that required tables exist in parsed XER

    Args:
        parser: XERParser instance
        required_tables: List of required table names

    Raises:
        ValidationError: If required table is missing
    """
    for table in required_tables:
        if not parser.has_table(table):
            raise ValidationError(f"Required table '{table}' not found in XER file")
