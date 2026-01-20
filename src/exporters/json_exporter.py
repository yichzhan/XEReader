"""JSON export module for generating output files"""
import json
from typing import List, Dict
from pathlib import Path
from ..models.activity import Activity
from ..models.project import ProjectInfo


class JSONExporter:
    """Exports activities and critical path to JSON files"""

    def __init__(self, project_info: ProjectInfo, activities: List[Activity]):
        """
        Initialize exporter

        Args:
            project_info: Project metadata
            activities: List of all activities
        """
        self.project_info = project_info
        self.activities = activities

    def export_activities(self, output_path: str) -> None:
        """
        Export activities.json

        Args:
            output_path: Path to output file
        """
        data = {
            "project": {
                "project_code": self.project_info.project_code,
                "project_name": self.project_info.project_name
            },
            "activities": [activity.to_dict() for activity in self.activities]
        }

        self._write_json(output_path, data)

    def export_critical_path(
        self,
        output_path: str,
        critical_paths: List[List[Activity]],
        project_duration_hours: float
    ) -> None:
        """
        Export critical_path.json

        Args:
            output_path: Path to output file
            critical_paths: List of critical paths (each is a list of Activity objects)
            project_duration_hours: Total project duration in hours
        """
        # Calculate summary statistics
        unique_activities = set()
        for path in critical_paths:
            for activity in path:
                unique_activities.add(activity.task_code)

        summary = {
            "total_duration_hours": round(project_duration_hours, 2),
            "total_duration_days": round(project_duration_hours / 8, 2),  # Assuming 8-hour days
            "critical_path_count": len(critical_paths),
            "total_activities_on_critical_paths": len(unique_activities)
        }

        # Build critical paths array
        paths_data = []
        for path_idx, path in enumerate(critical_paths, start=1):
            path_duration = sum(activity.duration_hours for activity in path)

            path_data = {
                "path_id": path_idx,
                "is_primary": (path_idx == 1),  # First path is primary
                "duration_hours": round(path_duration, 2),
                "duration_days": round(path_duration / 8, 2),
                "activity_count": len(path),
                "activities": [
                    activity.to_critical_path_dict(sequence=seq)
                    for seq, activity in enumerate(path, start=1)
                ]
            }
            paths_data.append(path_data)

        data = {
            "project": {
                "project_code": self.project_info.project_code,
                "project_name": self.project_info.project_name
            },
            "summary": summary,
            "critical_paths": paths_data
        }

        self._write_json(output_path, data)

    def _write_json(self, output_path: str, data: Dict) -> None:
        """
        Write data to JSON file with pretty formatting

        Args:
            output_path: Path to output file
            data: Data dictionary to write
        """
        # Ensure directory exists
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        # Write JSON with indentation
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @staticmethod
    def get_file_size(file_path: str) -> str:
        """
        Get human-readable file size

        Args:
            file_path: Path to file

        Returns:
            File size string (e.g., "125 KB")
        """
        size_bytes = Path(file_path).stat().st_size
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
