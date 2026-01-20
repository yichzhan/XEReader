"""Dependency relationship data model"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Dependency:
    """Represents a dependency relationship between two activities"""
    task_code: str           # Activity code (converted from task_id)
    dependency_type: str     # FS, SS, FF, or SF
    lag_hours: float         # Lag in hours (positive=delay, negative=lead)

    # Internal fields used during parsing
    _task_id: Optional[int] = None      # Temporary: used during parsing
    _pred_task_id: Optional[int] = None # Temporary: used during parsing


@dataclass
class DependencyRelation:
    """Internal representation of TASKPRED table row"""
    task_id: int          # Successor activity
    pred_task_id: int     # Predecessor activity
    pred_type: str        # Dependency type from XER (e.g., "PR_FS")
    lag_hr_cnt: float     # Lag in hours

    def get_dependency_type(self) -> str:
        """Convert XER pred_type to simplified type"""
        # XER uses PR_FS, PR_SS, PR_FF, PR_SF
        # We output: FS, SS, FF, SF
        return self.pred_type.replace('PR_', '') if self.pred_type.startswith('PR_') else self.pred_type
