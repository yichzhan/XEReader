"""Activity processor - converts XER data to Activity objects"""
from datetime import datetime
from typing import Dict, List, Optional
from ..models.activity import Activity
from ..models.dependency import Dependency, DependencyRelation
from ..models.project import ProjectInfo
from ..utils.date_utils import parse_xer_date


class ActivityProcessor:
    """Processes TASK and TASKPRED tables into Activity objects"""

    def __init__(self):
        self.activities: List[Activity] = []
        self.task_id_to_code: Dict[int, str] = {}  # Lookup map
        self.task_id_to_proj_id: Dict[int, int] = {}  # task_id -> proj_id mapping
        self.task_code_to_activity: Dict[str, Activity] = {}

    def process_all_projects(self, project_table: List[Dict]) -> List[ProjectInfo]:
        """
        Extract all project information from PROJECT table

        Args:
            project_table: PROJECT table rows

        Returns:
            List of ProjectInfo objects
        """
        if not project_table:
            raise ValueError("PROJECT table is empty")

        projects = []
        for project_row in project_table:
            project = ProjectInfo(
                project_code=project_row.get('proj_short_name', ''),
                project_name=project_row.get('proj_name', ''),
                last_recalc_date=project_row.get('last_recalc_date', ''),
                project_id=int(project_row['proj_id']) if project_row.get('proj_id') else None
            )
            projects.append(project)

        return projects

    def process_project(self, project_table: List[Dict]) -> ProjectInfo:
        """
        Extract first project information from PROJECT table (for backward compatibility)

        Args:
            project_table: PROJECT table rows

        Returns:
            ProjectInfo object
        """
        projects = self.process_all_projects(project_table)
        return projects[0] if projects else None

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
                if activity.proj_id:
                    self.task_id_to_proj_id[activity.task_id] = activity.proj_id
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
            proj_id=int(row['proj_id']) if row.get('proj_id') else None,
            duration_hours=duration_hours
        )

        return activity

    def group_by_project(self) -> Dict[int, List[Activity]]:
        """
        Group activities by project ID.

        Returns:
            Dict mapping proj_id to list of Activity objects
        """
        grouped: Dict[int, List[Activity]] = {}

        for activity in self.activities:
            proj_id = activity.proj_id
            if proj_id is not None:
                if proj_id not in grouped:
                    grouped[proj_id] = []
                grouped[proj_id].append(activity)

        return grouped

    def process_dependencies(self, taskpred_table: List[Dict]) -> None:
        """
        Process TASKPRED table and add dependencies to activities.
        Only links dependencies within the same project.

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
                # Skip if we can't find the task codes
                continue

            successor_activity = self.task_code_to_activity.get(successor_code)
            predecessor_activity = self.task_code_to_activity.get(predecessor_code)

            if not successor_activity or not predecessor_activity:
                continue

            # Only link dependencies within the same project
            if successor_activity.proj_id != predecessor_activity.proj_id:
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

    def get_activities_for_project(self, proj_id: int) -> List[Activity]:
        """
        Get activities for a specific project.

        Args:
            proj_id: Project ID

        Returns:
            List of Activity objects belonging to the project
        """
        return [a for a in self.activities if a.proj_id == proj_id]
