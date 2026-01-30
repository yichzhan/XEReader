#!/usr/bin/env python3
"""
Markdown Exporter

Generates human-readable Markdown reports from XER data:
- activities.md: All activities with natural language format
- critical_path.md: Critical path analysis report
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from dateutil import parser as date_parser


class MarkdownExporter:
    """Exports project data to Markdown format with natural language style"""

    def __init__(self, project_info: Union[Dict[str, Any], Any], activities: List[Union[Dict[str, Any], Any]]):
        """
        Initialize Markdown exporter

        Args:
            project_info: Project metadata (dict or ProjectInfo object)
            activities: List of activity dictionaries or Activity objects
        """
        # Convert ProjectInfo object to dict if needed
        if hasattr(project_info, 'project_code') and hasattr(project_info, 'project_name'):
            self.project_info = {
                'project_code': project_info.project_code,
                'project_name': project_info.project_name,
                'last_recalc_date': getattr(project_info, 'last_recalc_date', '')
            }
        else:
            self.project_info = project_info

        # Convert Activity objects to dicts if needed
        self.activities = []
        for activity in activities:
            if hasattr(activity, 'to_dict'):
                self.activities.append(activity.to_dict())
            else:
                self.activities.append(activity)

    def export_activities(self, output_path: str):
        """
        Generate activities.md with natural language format

        Args:
            output_path: Path to output Markdown file
        """
        content = self._generate_activities_markdown()

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def export_critical_path(
        self,
        output_path: str,
        critical_paths: List[List[Any]],
        project_duration_hours: float
    ):
        """
        Generate critical_path.md with natural language format

        Args:
            output_path: Path to output Markdown file
            critical_paths: List of critical paths (each is list of Activity objects)
            project_duration_hours: Total project duration in hours
        """
        # Convert Activity objects to dicts
        paths_dicts = []
        for path_idx, path in enumerate(critical_paths, start=1):
            path_duration = sum(
                activity.duration_hours if hasattr(activity, 'duration_hours') else 0
                for activity in path
            )

            activities_dicts = []
            for seq, activity in enumerate(path, start=1):
                if hasattr(activity, 'to_critical_path_dict'):
                    act_dict = activity.to_critical_path_dict(sequence=seq)
                else:
                    act_dict = activity
                activities_dicts.append(act_dict)

            paths_dicts.append({
                'path_id': path_idx,
                'is_primary': (path_idx == 1),
                'duration_hours': round(path_duration, 2),
                'duration_days': round(path_duration / 8, 2),
                'activity_count': len(path),
                'activities': activities_dicts
            })

        content = self._generate_critical_path_markdown(paths_dicts, project_duration_hours)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def _generate_activities_markdown(self) -> str:
        """Generate Markdown content for activities report"""
        lines = []

        # Header
        project_name = self.project_info['project_name'] or "Unnamed Project"
        project_code = self.project_info['project_code']
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')

        lines.append("# Project Activities Report\n")
        lines.append(f"**{project_name}** ({project_code})\n")
        lines.append(f"This report contains {len(self.activities)} activities for the project.\n")

        # XER file date (if available)
        xer_date = self.project_info.get('last_recalc_date', '')
        if xer_date:
            lines.append(f"XER file date: {xer_date}\n")

        lines.append(f"Report generated on {timestamp}.\n")
        lines.append("---\n")

        # Activity list
        lines.append("## Activity List\n")

        for idx, activity in enumerate(self.activities, 1):
            task_code = activity['task_code']
            task_name = activity['task_name']

            lines.append(f"### {idx}. {task_code} - {task_name}\n")

            # Planned and actual schedule
            planned_start = self._format_date(activity.get('planned_start_date'))
            planned_end = self._format_date(activity.get('planned_end_date'))
            duration = self._calculate_duration(
                activity.get('planned_start_date'),
                activity.get('planned_end_date')
            )

            lines.append(f"- Planned: {planned_start} to {planned_end} ({duration})\n")

            # Actual progress
            actual_start = activity.get('actual_start_date')
            actual_end = activity.get('actual_end_date')

            if actual_start and actual_end:
                lines.append(f"- Actual: {self._format_date(actual_start)} to {self._format_date(actual_end)} (Completed)\n")
            elif actual_start:
                lines.append(f"- Actual: In Progress (started {self._format_date(actual_start)})\n")
            else:
                lines.append("- Actual: Not started\n")

            # Dependencies
            deps = activity.get('dependencies', {})
            preds = deps.get('predecessors', [])
            succs = deps.get('successors', [])

            if preds:
                pred_strs = [self._format_dependency(p) for p in preds]
                lines.append(f"- Predecessors: {', '.join(pred_strs)}\n")
            else:
                lines.append("- Predecessors: None\n")

            if succs:
                succ_strs = [self._format_dependency(s) for s in succs]
                lines.append(f"- Successors: {', '.join(succ_strs)}\n")
            else:
                lines.append("- Successors: None\n")

            # Notes (from UDFVALUE table)
            notes = activity.get('notes', [])
            if notes:
                if len(notes) == 1:
                    note = notes[0]
                    label = note.get('label', 'Note') if isinstance(note, dict) else 'Note'
                    text = note.get('text', note) if isinstance(note, dict) else note
                    lines.append(f"- **Notes:** **{label}:** {text}\n")
                else:
                    lines.append("- **Notes:**\n")
                    for note in notes:
                        label = note.get('label', 'Note') if isinstance(note, dict) else 'Note'
                        text = note.get('text', note) if isinstance(note, dict) else note
                        lines.append(f"  - **{label}:** {text}\n")

            lines.append("\n---\n")

        # Summary statistics
        lines.append("## Summary Statistics\n")
        completed = sum(1 for a in self.activities
                       if a.get('actual_start_date') and a.get('actual_end_date'))
        in_progress = sum(1 for a in self.activities
                         if a.get('actual_start_date') and not a.get('actual_end_date'))
        not_started = len(self.activities) - completed - in_progress

        lines.append(f"- Total activities: {len(self.activities)}\n")
        lines.append(f"- Completed activities: {completed}\n")
        lines.append(f"- In progress: {in_progress}\n")
        lines.append(f"- Not started: {not_started}\n")

        return '\n'.join(lines)

    def _generate_critical_path_markdown(
        self,
        critical_paths: List[Dict[str, Any]],
        project_duration_hours: float
    ) -> str:
        """Generate Markdown content for critical path report"""
        lines = []

        # Header
        project_name = self.project_info['project_name'] or "Unnamed Project"
        project_code = self.project_info['project_code']
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')

        lines.append("# Critical Path Analysis Report\n")
        lines.append(f"**{project_name}** ({project_code})\n")

        # XER file date (if available)
        xer_date = self.project_info.get('last_recalc_date', '')
        if xer_date:
            lines.append(f"XER file date: {xer_date}\n")

        lines.append(f"Analysis performed on {timestamp}.\n")
        lines.append("---\n")

        # Project summary
        lines.append("## Project Summary\n")
        total_hours = round(project_duration_hours, 2)
        total_days = round(project_duration_hours / 8, 2)
        num_paths = len(critical_paths)
        total_activities = sum(p['activity_count'] for p in critical_paths)

        lines.append(
            f"The project has a total duration of **{total_days:.1f} days** "
            f"({total_hours:.0f} hours) from start to finish.\n"
        )
        lines.append(
            f"The analysis identified **{num_paths} critical path{'s' if num_paths != 1 else ''}** "
            f"containing a total of **{total_activities} activities**. "
            f"{'These critical paths represent' if num_paths > 1 else 'This critical path represents'} "
            f"the longest sequence of dependent activities that "
            f"{'determine' if num_paths > 1 else 'determines'} "
            f"the minimum project duration.\n"
        )
        lines.append("---\n")

        # Each critical path
        for path in critical_paths:
            path_id = path['path_id']
            is_primary = path['is_primary']
            path_label = "Primary Path" if is_primary else "Alternate Path"

            lines.append(f"## Critical Path #{path_id} ({path_label})\n")

            path_days = path['duration_days']
            path_hours = path['duration_hours']
            path_count = path['activity_count']

            if is_primary:
                lines.append(
                    f"This is the primary critical path with a duration of **{path_days:.1f} days** "
                    f"({path_hours:.0f} hours) spanning **{path_count} activities**.\n"
                )
            else:
                lines.append(
                    f"This is an alternate critical path with the same duration of **{path_days:.1f} days** "
                    f"({path_hours:.0f} hours) spanning **{path_count} activities**.\n"
                )

            lines.append("\n### Path Sequence\n")

            # Activities in compact format
            for activity in path['activities']:
                seq = activity['sequence']
                task_code = activity['task_code']
                task_name = activity['task_name']
                start_date = self._format_date(activity['planned_start_date'])
                end_date = self._format_date(activity['planned_end_date'])
                duration = self._calculate_duration(
                    activity['planned_start_date'],
                    activity['planned_end_date']
                )

                lines.append(
                    f"**{seq}. {task_code} - {task_name}** - "
                    f"{start_date} to {end_date} ({duration})\n"
                )

            lines.append("\n---\n")

        # Analysis notes
        lines.append("## Analysis Notes\n")
        lines.append(
            "Critical paths represent sequences of activities where any delay will directly "
            "impact the project completion date. Project managers should monitor these activities "
            "closely and allocate resources to prevent delays.\n"
        )

        return '\n'.join(lines)

    def _format_date(self, date_str: Optional[str]) -> str:
        """
        Convert ISO date to readable format: '2026-01-15 08:00'

        Args:
            date_str: ISO format date string or None

        Returns:
            Formatted date string or 'N/A'
        """
        if not date_str:
            return 'N/A'

        try:
            dt = date_parser.parse(date_str)
            return dt.strftime('%Y-%m-%d %H:%M')
        except:
            return date_str

    def _calculate_duration(self, start_date: Optional[str], end_date: Optional[str]) -> str:
        """
        Calculate duration between two dates

        Args:
            start_date: Start date ISO string
            end_date: End date ISO string

        Returns:
            Human-readable duration string
        """
        if not start_date or not end_date:
            return 'N/A'

        try:
            start = date_parser.parse(start_date)
            end = date_parser.parse(end_date)
            delta = end - start

            days = delta.days
            hours = delta.seconds // 3600

            if days == 0 and hours == 0:
                return '0 days'
            elif days == 0:
                return f'{hours} hours'
            elif hours == 0:
                return f'{days} day{"s" if days != 1 else ""}'
            else:
                return f'{days} day{"s" if days != 1 else ""}, {hours} hour{"s" if hours != 1 else ""}'
        except:
            return 'N/A'

    def _format_dependency(self, dep: Dict[str, Any]) -> str:
        """
        Format dependency with relationship type and lag

        Args:
            dep: Dependency dictionary with task_code, dependency_type, lag_hours

        Returns:
            Formatted dependency string (e.g., "A1000 (Finish-to-Start)")
        """
        task_code = dep['task_code']
        dep_type = dep.get('dependency_type', 'FS')
        lag_hours = dep.get('lag_hours', 0.0)

        # Map dependency types to readable names
        type_map = {
            'FS': 'Finish-to-Start',
            'SS': 'Start-to-Start',
            'FF': 'Finish-to-Finish',
            'SF': 'Start-to-Finish'
        }

        dep_name = type_map.get(dep_type, dep_type)

        # Format lag if present
        if lag_hours != 0.0:
            lag_days = lag_hours / 8.0  # Assuming 8-hour workday
            if lag_days == int(lag_days):
                lag_str = f", lag: {int(lag_days)} day{'s' if abs(lag_days) != 1 else ''}"
            else:
                lag_str = f", lag: {lag_hours} hours"
            return f"{task_code} ({dep_name}{lag_str})"
        else:
            return f"{task_code} ({dep_name})"
