"""Activity processor - converts XER data to Activity objects"""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from ..models.activity import Activity
from ..models.dependency import Dependency, DependencyRelation
from ..models.project import ProjectInfo
from ..utils.date_utils import parse_xer_date


@dataclass
class DuplicateInfo:
    """Information about a discarded duplicate task"""
    task_code: str
    task_id: Optional[int]
    task_name: str
    planned_start_date: Optional[datetime]
    planned_end_date: Optional[datetime]
    actual_start_date: Optional[datetime]
    actual_end_date: Optional[datetime]
    is_identical: bool  # True if all fields match the kept task
    differences: List[str]  # List of field names that differ


class ActivityProcessor:
    """Processes TASK and TASKPRED tables into Activity objects"""

    def __init__(self):
        self.activities: List[Activity] = []
        self.task_id_to_code: Dict[int, str] = {}  # Lookup map
        self.task_code_to_activity: Dict[str, Activity] = {}

    def process_project(self, project_table: List[Dict]) -> ProjectInfo:
        """
        Extract project information from PROJECT table

        Args:
            project_table: PROJECT table rows

        Returns:
            ProjectInfo object
        """
        if not project_table:
            raise ValueError("PROJECT table is empty")

        # Get first project (XER can contain multiple projects, we take the first)
        project_row = project_table[0]

        return ProjectInfo(
            project_code=project_row.get('proj_short_name', ''),
            project_name=project_row.get('proj_name', ''),
            last_recalc_date=project_row.get('last_recalc_date', ''),
            project_id=int(project_row['proj_id']) if project_row.get('proj_id') else None
        )

    def process_activities(self, task_table: List[Dict]) -> List[Activity]:
        """
        Convert TASK table to Activity objects

        Args:
            task_table: TASK table rows

        Returns:
            List of Activity objects
        """
        activities = []

        for row in task_table:
            activity = self._create_activity_from_row(row)
            activities.append(activity)

            # Build lookup maps
            if activity.task_id:
                self.task_id_to_code[activity.task_id] = activity.task_code
            self.task_code_to_activity[activity.task_code] = activity

        self.activities = activities
        return activities

    def _create_activity_from_row(self, row: Dict) -> Activity:
        """
        Create Activity object from TASK table row

        Args:
            row: Dictionary representing a TASK row

        Returns:
            Activity object
        """
        # Parse dates
        planned_start = parse_xer_date(row.get('target_start_date'))
        planned_end = parse_xer_date(row.get('target_end_date'))
        actual_start = parse_xer_date(row.get('act_start_date'))
        actual_end = parse_xer_date(row.get('act_end_date'))

        # Calculate duration in hours if dates available
        duration_hours = 0.0
        if planned_start and planned_end:
            delta = planned_end - planned_start
            duration_hours = delta.total_seconds() / 3600

        activity = Activity(
            task_code=row.get('task_code', ''),
            task_name=row.get('task_name', ''),
            planned_start_date=planned_start,
            planned_end_date=planned_end,
            actual_start_date=actual_start,
            actual_end_date=actual_end,
            task_id=int(row['task_id']) if row.get('task_id') else None,
            duration_hours=duration_hours
        )

        return activity

    def process_dependencies(self, taskpred_table: List[Dict]) -> None:
        """
        Process TASKPRED table and add dependencies to activities

        Args:
            taskpred_table: TASKPRED table rows
        """
        # Parse all dependency relationships
        relations = []
        for row in taskpred_table:
            relation = self._create_dependency_relation(row)
            if relation:
                relations.append(relation)

        # Build predecessors and successors for each activity
        for relation in relations:
            # Get task codes from task IDs
            successor_code = self.task_id_to_code.get(relation.task_id)
            predecessor_code = self.task_id_to_code.get(relation.pred_task_id)

            if not successor_code or not predecessor_code:
                # Skip if we can't find the task codes (shouldn't happen with valid data)
                continue

            successor_activity = self.task_code_to_activity.get(successor_code)
            predecessor_activity = self.task_code_to_activity.get(predecessor_code)

            if not successor_activity or not predecessor_activity:
                continue

            dep_type = relation.get_dependency_type()

            # Add predecessor to successor
            predecessor_dep = Dependency(
                task_code=predecessor_code,
                dependency_type=dep_type,
                lag_hours=relation.lag_hr_cnt
            )
            successor_activity.predecessors.append(predecessor_dep)

            # Add successor to predecessor
            successor_dep = Dependency(
                task_code=successor_code,
                dependency_type=dep_type,
                lag_hours=relation.lag_hr_cnt
            )
            predecessor_activity.successors.append(successor_dep)

    def _create_dependency_relation(self, row: Dict) -> DependencyRelation:
        """
        Create DependencyRelation from TASKPRED row

        Args:
            row: Dictionary representing a TASKPRED row

        Returns:
            DependencyRelation object or None
        """
        try:
            task_id = int(row['task_id']) if row.get('task_id') else None
            pred_task_id = int(row['pred_task_id']) if row.get('pred_task_id') else None

            if not task_id or not pred_task_id:
                return None

            # Handle None values for lag_hr_cnt
            lag_value = row.get('lag_hr_cnt', 0)
            lag_hr_cnt = float(lag_value) if lag_value is not None else 0.0
            pred_type = row.get('pred_type', 'PR_FS')

            return DependencyRelation(
                task_id=task_id,
                pred_task_id=pred_task_id,
                pred_type=pred_type,
                lag_hr_cnt=lag_hr_cnt
            )
        except (ValueError, KeyError):
            return None

    def get_activities(self) -> List[Activity]:
        """Get list of all activities"""
        return self.activities

    def get_activity_by_code(self, task_code: str) -> Activity:
        """Get activity by task code"""
        return self.task_code_to_activity.get(task_code)

    def deduplicate_activities(self) -> Tuple[List[Activity], Dict[str, List[DuplicateInfo]]]:
        """
        Remove duplicate task_codes, keeping first occurrence.

        Returns:
            Tuple of:
            - List of deduplicated activities
            - Dict mapping task_code to list of discarded DuplicateInfo
        """
        seen_codes: Dict[str, Activity] = {}
        deduplicated: List[Activity] = []
        discarded: Dict[str, List[DuplicateInfo]] = {}

        for activity in self.activities:
            if activity.task_code not in seen_codes:
                # First occurrence - keep it
                seen_codes[activity.task_code] = activity
                deduplicated.append(activity)
            else:
                # Duplicate - record info and discard
                kept = seen_codes[activity.task_code]
                differences = self._compare_activities(kept, activity)

                dup_info = DuplicateInfo(
                    task_code=activity.task_code,
                    task_id=activity.task_id,
                    task_name=activity.task_name,
                    planned_start_date=activity.planned_start_date,
                    planned_end_date=activity.planned_end_date,
                    actual_start_date=activity.actual_start_date,
                    actual_end_date=activity.actual_end_date,
                    is_identical=len(differences) == 0,
                    differences=differences
                )

                if activity.task_code not in discarded:
                    discarded[activity.task_code] = []
                discarded[activity.task_code].append(dup_info)

                # Remove from lookup maps
                if activity.task_id and activity.task_id in self.task_id_to_code:
                    del self.task_id_to_code[activity.task_id]

        # Update internal state
        self.activities = deduplicated
        self.task_code_to_activity = {a.task_code: a for a in deduplicated}

        return deduplicated, discarded

    def _compare_activities(self, kept: Activity, other: Activity) -> List[str]:
        """
        Compare two activities and return list of differing fields.

        Args:
            kept: The activity being kept
            other: The duplicate activity being discarded

        Returns:
            List of field names that differ (empty if identical)
        """
        differences = []

        if kept.task_name != other.task_name:
            differences.append('task_name')
        if kept.planned_start_date != other.planned_start_date:
            differences.append('planned_start_date')
        if kept.planned_end_date != other.planned_end_date:
            differences.append('planned_end_date')
        if kept.actual_start_date != other.actual_start_date:
            differences.append('actual_start_date')
        if kept.actual_end_date != other.actual_end_date:
            differences.append('actual_end_date')

        return differences
