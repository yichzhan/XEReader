# critical_path.json - Schema

## Overview
JSON output containing the critical path(s) - the longest sequence(s) of dependent activities that determine minimum project duration.

**Key Features:**
- Sequential ordering of activities on critical path
- Support for multiple critical paths
- Sufficient information for diagram generation
- Summary statistics

## File Structure

```json
{
  "project": {
    "project_code": "PRJ-2026-001",
    "project_name": "Office Building Construction"
  },
  "summary": {
    "total_duration_hours": 4320.0,
    "total_duration_days": 180.0,
    "critical_path_count": 2,
    "total_activities_on_critical_paths": 45
  },
  "critical_paths": [
    {
      "path_id": 1,
      "is_primary": true,
      "duration_hours": 4320.0,
      "duration_days": 180.0,
      "activity_count": 25,
      "activities": [
        {
          "sequence": 1,
          "task_code": "A1000",
          "task_name": "Notice to Proceed",
          "planned_start_date": "2026-01-15T08:00:00Z",
          "planned_end_date": "2026-01-15T08:00:00Z"
        },
        {
          "sequence": 2,
          "task_code": "A1010",
          "task_name": "Site Mobilization",
          "planned_start_date": "2026-02-01T08:00:00Z",
          "planned_end_date": "2026-02-05T17:00:00Z"
        }
      ]
    },
    {
      "path_id": 2,
      "is_primary": false,
      "duration_hours": 4320.0,
      "duration_days": 180.0,
      "activity_count": 20,
      "activities": [...]
    }
  ]
}
```

---

## Section 1: Project

### Schema
```json
{
  "project": {
    "project_code": "PRJ-2026-001",
    "project_name": "Office Building Construction"
  }
}
```

### Data Mapping

| JSON Field | XER Table | XER Field | Data Type |
|------------|-----------|-----------|-----------|
| `project_code` | `PROJECT` | `proj_short_name` | String |
| `project_name` | `PROJECT` | `proj_name` | String |

---

## Section 2: Summary

### Schema
```json
{
  "summary": {
    "total_duration_hours": 4320.0,
    "total_duration_days": 180.0,
    "critical_path_count": 2,
    "total_activities_on_critical_paths": 45
  }
}
```

### Fields

| JSON Field | Data Type | Description | Calculation |
|------------|-----------|-------------|-------------|
| `total_duration_hours` | Float | Project total duration in hours | Maximum duration among all critical paths |
| `total_duration_days` | Float | Project total duration in days | `total_duration_hours / 8` |
| `critical_path_count` | Integer | Number of critical paths found | Count of paths with maximum duration |
| `total_activities_on_critical_paths` | Integer | Total unique activities across all critical paths | Count unique task_codes across all paths |

**Note:**
- `total_duration` is the length of the longest path (all critical paths have same duration by definition)
- If there are multiple critical paths, they all have the same duration
- `total_activities_on_critical_paths` may include activities that appear on multiple paths

---

## Section 3: Critical Paths Array

### Schema (Single Path)
```json
{
  "path_id": 1,
  "is_primary": true,
  "duration_hours": 4320.0,
  "duration_days": 180.0,
  "activity_count": 25,
  "activities": [...]
}
```

### Path-Level Fields

| JSON Field | Data Type | Description | Notes |
|------------|-----------|-------------|-------|
| `path_id` | Integer | Unique identifier for this path | Sequential: 1, 2, 3... |
| `is_primary` | Boolean | Whether this is the primary critical path | First path found = primary |
| `duration_hours` | Float | Total duration of this path in hours | Sum of all activity durations + lags |
| `duration_days` | Float | Total duration of this path in days | `duration_hours / 8` |
| `activity_count` | Integer | Number of activities on this path | Count of activities array |

**Primary Path Selection:**
- When multiple critical paths exist with equal duration
- First path found during traversal is marked as primary
- Arbitrary selection, all paths are equally critical

---

## Section 4: Activities on Critical Path

### Schema (Single Activity)
```json
{
  "sequence": 1,
  "task_code": "A1010",
  "task_name": "Site Mobilization",
  "planned_start_date": "2026-02-01T08:00:00Z",
  "planned_end_date": "2026-02-05T17:00:00Z"
}
```

### Activity Fields

| JSON Field | XER Table | XER Field | Data Type | Notes |
|------------|-----------|-----------|-----------|-------|
| `sequence` | Calculated | N/A | Integer | Position in critical path (1, 2, 3...) |
| `task_code` | `TASK` | `task_code` | String | Activity unique identifier |
| `task_name` | `TASK` | `task_name` | String | Activity description |
| `planned_start_date` | `TASK` | `target_start_date` | DateTime | Baseline start (ISO 8601) |
| `planned_end_date` | `TASK` | `target_end_date` | DateTime | Baseline finish (ISO 8601) |

**Sequence Numbering:**
- Starts at 1 for each critical path
- Increments by 1 for each subsequent activity
- Represents the order of execution along the critical path
- Activities are ordered from project start to finish

**Why No Dependencies in Critical Path JSON?**
- Sequence number implicitly shows the flow
- Activity N → Activity N+1 is the relationship
- Reduces redundancy (dependencies already in activities.json)
- Cleaner for diagram generation

---

## Complete Example

```json
{
  "project": {
    "project_code": "PRJ-2026-001",
    "project_name": "Office Building Construction"
  },
  "summary": {
    "total_duration_hours": 4320.0,
    "total_duration_days": 180.0,
    "critical_path_count": 2,
    "total_activities_on_critical_paths": 50
  },
  "critical_paths": [
    {
      "path_id": 1,
      "is_primary": true,
      "duration_hours": 4320.0,
      "duration_days": 180.0,
      "activity_count": 25,
      "activities": [
        {
          "sequence": 1,
          "task_code": "A1000",
          "task_name": "Notice to Proceed",
          "planned_start_date": "2026-01-15T08:00:00Z",
          "planned_end_date": "2026-01-15T08:00:00Z"
        },
        {
          "sequence": 2,
          "task_code": "A1010",
          "task_name": "Site Mobilization",
          "planned_start_date": "2026-02-01T08:00:00Z",
          "planned_end_date": "2026-02-05T17:00:00Z"
        },
        {
          "sequence": 3,
          "task_code": "A1020",
          "task_name": "Excavation",
          "planned_start_date": "2026-02-06T08:00:00Z",
          "planned_end_date": "2026-02-20T17:00:00Z"
        },
        {
          "sequence": 4,
          "task_code": "A1030",
          "task_name": "Foundation",
          "planned_start_date": "2026-02-21T08:00:00Z",
          "planned_end_date": "2026-03-15T17:00:00Z"
        },
        {
          "sequence": 5,
          "task_code": "A2000",
          "task_name": "Structural Steel",
          "planned_start_date": "2026-03-16T08:00:00Z",
          "planned_end_date": "2026-05-01T17:00:00Z"
        }
      ]
    },
    {
      "path_id": 2,
      "is_primary": false,
      "duration_hours": 4320.0,
      "duration_days": 180.0,
      "activity_count": 30,
      "activities": [
        {
          "sequence": 1,
          "task_code": "A1000",
          "task_name": "Notice to Proceed",
          "planned_start_date": "2026-01-15T08:00:00Z",
          "planned_end_date": "2026-01-15T08:00:00Z"
        },
        {
          "sequence": 2,
          "task_code": "A1010",
          "task_name": "Site Mobilization",
          "planned_start_date": "2026-02-01T08:00:00Z",
          "planned_end_date": "2026-02-05T17:00:00Z"
        },
        {
          "sequence": 3,
          "task_code": "A1015",
          "task_name": "Utility Relocation",
          "planned_start_date": "2026-02-06T08:00:00Z",
          "planned_end_date": "2026-02-25T17:00:00Z"
        },
        {
          "sequence": 4,
          "task_code": "A1040",
          "task_name": "Site Grading",
          "planned_start_date": "2026-02-26T08:00:00Z",
          "planned_end_date": "2026-03-10T17:00:00Z"
        }
      ]
    }
  ]
}
```

---

## Data Sources

### From XER Tables

| Data Element | Source |
|--------------|--------|
| Project info | `PROJECT` table |
| Activity identification | `TASK.task_code`, `TASK.task_name` |
| Activity dates | `TASK.target_start_date`, `TASK.target_end_date` |
| Critical path determination | CPM calculation (forward/backward pass) |
| Path sequencing | Graph traversal (topological sort) |

### Calculated/Derived

| Data Element | Calculation Method |
|--------------|-------------------|
| `path_id` | Sequential numbering of discovered paths |
| `is_primary` | First path found = true, others = false |
| `sequence` | Position in topologically sorted critical path |
| `duration_hours` | Sum of activity durations along path |
| `duration_days` | `duration_hours / 8` |
| `activity_count` | Count of activities in path |
| `total_activities_on_critical_paths` | Count unique task_codes across all paths |

---

## Processing Steps

1. Perform CPM calculation (forward/backward pass)
2. Identify critical activities (total_float ≤ 0)
3. Build critical activities subgraph
4. Find all paths from start to finish through critical activities
5. Calculate duration for each path
6. Select paths with maximum duration (all are critical paths)
7. For each critical path:
   - Assign `path_id` (1, 2, 3...)
   - Mark first path as primary (`is_primary = true`)
   - Topologically sort activities in path
   - Assign `sequence` numbers (1, 2, 3...)
   - Extract activity details (code, name, dates)
   - Calculate path duration
8. Calculate summary statistics
9. Generate JSON output

---

## Information for Diagram Generation

The critical_path.json provides all necessary information for generating critical path diagrams:

### Network Diagram (Activity-on-Node)

**Available Data:**
- ✅ **Nodes:** Each activity with code, name, dates
- ✅ **Sequence:** Implicit edges from sequence N → N+1
- ✅ **Multiple Paths:** Separate paths clearly identified
- ✅ **Labels:** Activity codes and names for node labels
- ✅ **Dates:** Start/end dates for timeline positioning

**Diagram Types Supported:**
1. **Linear Flow Diagram:**
   ```
   [A1000] → [A1010] → [A1020] → [A1030] → [A2000]
   ```

2. **Timeline Diagram:**
   ```
   Jan 15        Feb 1         Feb 6         Feb 21        Mar 16
     |             |             |             |             |
   [A1000]  →  [A1010]  →   [A1020]   →   [A1030]   →   [A2000]
   ```

3. **Multi-Path Diagram:**
   ```
   Path 1: [A1000] → [A1010] → [A1020] → ...
   Path 2: [A1000] → [A1010] → [A1015] → ...
   ```

4. **Network Diagram:**
   - Use sequence to determine node positioning
   - Activities with same sequence across paths can be merged
   - Different sequences indicate parallel paths

### Data Required vs Available

| Diagram Requirement | Available in JSON | Notes |
|---------------------|-------------------|-------|
| Activity nodes | ✅ Yes | `task_code`, `task_name` |
| Node ordering | ✅ Yes | `sequence` field |
| Node grouping (paths) | ✅ Yes | `path_id` |
| Timeline positioning | ✅ Yes | `planned_start_date`, `planned_end_date` |
| Activity duration | ✅ Yes | Can calculate from dates |
| Path branching | ✅ Yes | Compare sequences across paths |
| Shared activities | ✅ Yes | Same task_code in multiple paths |
| Path duration | ✅ Yes | `duration_hours`, `duration_days` |
| Project total duration | ✅ Yes | Summary `total_duration_hours` |

### Additional Diagram Information

For more complex diagrams (showing non-critical activities or all dependencies), use **activities.json** which contains:
- All activities (not just critical path)
- Full dependency information (predecessors and successors)
- Dependency types and lags

**Recommended Approach for Full Network Diagram:**
1. Use `activities.json` for complete network graph
2. Use `critical_path.json` to highlight critical path activities
3. Color critical path activities differently (e.g., red)
4. Show all activities and dependencies in gray
5. Emphasize critical path with bold lines or red color

---

## Validation Rules

### Required Fields
- `project_code` - must not be empty
- `project_name` - must not be empty
- `summary.total_duration_hours` - must be > 0
- `critical_path_count` - must be ≥ 1
- Each path must have `path_id`, `duration_hours`, `activities`
- Each activity must have `sequence`, `task_code`, `task_name`, dates

### Data Integrity
- All critical paths must have equal `duration_hours`
- `path_id` must be sequential (1, 2, 3...)
- Exactly one path must have `is_primary = true`
- Activity `sequence` within each path must be sequential (1, 2, 3...)
- All `task_code` references must exist in activities.json
- `total_duration_hours` in summary must match path durations
- `activity_count` must match length of activities array

### Multiple Critical Paths
- If `critical_path_count > 1`, must have multiple path objects
- All paths with same duration are critical paths
- Paths may share activities (same task_code appears in multiple paths)
- Each path gets independent sequence numbering

---

## Date Format

**Format:** ISO 8601 with timezone
**Example:** `2026-02-01T08:00:00Z`
**Null handling:** Not applicable (critical path activities always have dates)

---

## Special Cases

### Single Critical Path
```json
{
  "summary": {
    "critical_path_count": 1,
    ...
  },
  "critical_paths": [
    {
      "path_id": 1,
      "is_primary": true,
      ...
    }
  ]
}
```

### Multiple Critical Paths with Shared Activities
```json
{
  "critical_paths": [
    {
      "path_id": 1,
      "activities": [
        {"sequence": 1, "task_code": "A1000", ...},  // Shared
        {"sequence": 2, "task_code": "A1010", ...},  // Shared
        {"sequence": 3, "task_code": "A1020", ...}   // Path 1 only
      ]
    },
    {
      "path_id": 2,
      "activities": [
        {"sequence": 1, "task_code": "A1000", ...},  // Shared
        {"sequence": 2, "task_code": "A1010", ...},  // Shared
        {"sequence": 3, "task_code": "A1015", ...}   // Path 2 only
      ]
    }
  ]
}
```

**Note:** Activities A1000 and A1010 appear in both paths, so they are shared nodes where paths branch.

### Disconnected Critical Paths
If the project has disconnected phases with separate critical paths:
```json
{
  "summary": {
    "critical_path_count": 2,
    "total_duration_hours": 4320.0
  },
  "critical_paths": [
    {
      "path_id": 1,
      "duration_hours": 4320.0,
      "activities": [...]  // Phase 1 critical path
    },
    {
      "path_id": 2,
      "duration_hours": 2160.0,
      "activities": [...]  // Phase 2 critical path (shorter, different subgraph)
    }
  ]
}
```

**Note:** In this case, paths have different durations because they belong to disconnected subgraphs. Each subgraph has its own critical path.

---

## Usage Example: Diagram Generation

### Simple Linear Diagram (Python)
```python
import json

with open('critical_path.json', 'r') as f:
    data = json.load(f)

# Get primary critical path
primary_path = next(p for p in data['critical_paths'] if p['is_primary'])

# Generate simple text diagram
print(f"Critical Path (Duration: {primary_path['duration_days']} days)")
print("-" * 80)

for activity in primary_path['activities']:
    seq = activity['sequence']
    code = activity['task_code']
    name = activity['task_name']

    if seq == 1:
        print(f"{seq}. [{code}] {name}")
    else:
        print(f"    ↓")
        print(f"{seq}. [{code}] {name}")
```

### Timeline Diagram
```python
import matplotlib.pyplot as plt
from datetime import datetime

# Parse dates and plot timeline
for activity in primary_path['activities']:
    start = datetime.fromisoformat(activity['planned_start_date'].replace('Z', '+00:00'))
    end = datetime.fromisoformat(activity['planned_end_date'].replace('Z', '+00:00'))

    # Plot horizontal bar for each activity
    plt.barh(activity['sequence'], (end - start).days, left=start.toordinal())
    plt.text(start.toordinal(), activity['sequence'], activity['task_code'])

plt.xlabel('Timeline')
plt.ylabel('Activity Sequence')
plt.title(f"Critical Path: {data['project']['project_name']}")
plt.show()
```

---

**Document Version:** 1.0
**Last Updated:** 2026-01-20
**Related Documents:**
- technical_design.md (overall system design)
- activities_json_schema.md (all activities output)
- design_decisions.md (design rationale)
