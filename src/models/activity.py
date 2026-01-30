"""Activity data model"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict
from .dependency import Dependency


@dataclass
class Activity:
    """Represents a single activity/task from the schedule"""

    # Core identification
    task_code: str                          # Activity ID (persistent identifier)
    task_name: str                          # Activity description

    # Dates
    planned_start_date: Optional[datetime]  # target_start_date in XER
    planned_end_date: Optional[datetime]    # target_end_date in XER
    actual_start_date: Optional[datetime]   # act_start_date in XER
    actual_end_date: Optional[datetime]     # act_end_date in XER

    # Dependencies (will be populated during processing)
    predecessors: List[Dependency] = field(default_factory=list)
    successors: List[Dependency] = field(default_factory=list)

    # Notes from UDFVALUE table (schedule change explanations)
    # Each note is {"label": "UDF type label", "text": "note content"}
    notes: List[Dict[str, str]] = field(default_factory=list)

    # Internal fields (not exported to JSON)
    task_id: Optional[int] = None           # Temporary: used during parsing only
    proj_id: Optional[int] = None           # Project ID for multi-project XER files
    duration_hours: float = 0.0             # For CPM calculations

    # CPM calculation fields (for critical path)
    early_start: Optional[datetime] = None
    early_finish: Optional[datetime] = None
    late_start: Optional[datetime] = None
    late_finish: Optional[datetime] = None
    total_float_hours: Optional[float] = None

    def is_critical(self) -> bool:
        """Check if this activity is on critical path (float <= 0)"""
        if self.total_float_hours is None:
            return False
        return self.total_float_hours <= 0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON export (activities.json format)"""
        result = {
            "task_code": self.task_code,
            "task_name": self.task_name,
            "planned_start_date": self.planned_start_date.isoformat() + 'Z' if self.planned_start_date else None,
            "planned_end_date": self.planned_end_date.isoformat() + 'Z' if self.planned_end_date else None,
            "actual_start_date": self.actual_start_date.isoformat() + 'Z' if self.actual_start_date else None,
            "actual_end_date": self.actual_end_date.isoformat() + 'Z' if self.actual_end_date else None,
            "dependencies": {
                "predecessors": [
                    {
                        "task_code": dep.task_code,
                        "dependency_type": dep.dependency_type,
                        "lag_hours": dep.lag_hours
                    }
                    for dep in self.predecessors
                ],
                "successors": [
                    {
                        "task_code": dep.task_code,
                        "dependency_type": dep.dependency_type,
                        "lag_hours": dep.lag_hours
                    }
                    for dep in self.successors
                ]
            }
        }
        # Only include notes if present
        if self.notes:
            result["notes"] = self.notes
        return result

    def to_critical_path_dict(self, sequence: int) -> dict:
        """Convert to dictionary for critical_path.json format"""
        return {
            "sequence": sequence,
            "task_code": self.task_code,
            "task_name": self.task_name,
            "planned_start_date": self.planned_start_date.isoformat() + 'Z' if self.planned_start_date else None,
            "planned_end_date": self.planned_end_date.isoformat() + 'Z' if self.planned_end_date else None
        }
