"""Project information data model"""
from dataclasses import dataclass


@dataclass
class ProjectInfo:
    """Project metadata from XER file"""
    project_code: str  # proj_short_name in XER
    project_name: str  # proj_name in XER
    last_recalc_date: str = None  # last_recalc_date in XER (when schedule was last calculated)

    # Internal fields (not exported to JSON)
    project_id: int = None  # proj_id in XER (temporary, for internal use)
