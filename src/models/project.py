"""Project information data model"""
from dataclasses import dataclass


@dataclass
class ProjectInfo:
    """Project metadata from XER file"""
    project_code: str  # proj_short_name in XER
    project_name: str  # proj_name in XER

    # Internal fields (not exported to JSON)
    project_id: int = None  # proj_id in XER (temporary, for internal use)
