# activities.json - Simplified Schema

## Overview
Simplified JSON output containing only essential activity information: identification, dates, and dependencies.

**Note:** Uses `task_code` as the unique identifier (persistent across exports), not `task_id` (temporary XER export reference).

## File Structure

```json
{
  "project": {
    "project_code": "PRJ-2026-001",
    "project_name": "Office Building Construction"
  },
  "activities": [
    {
      "task_code": "A1010",
      "task_name": "Site Mobilization",
      "planned_start_date": "2026-02-01T08:00:00Z",
      "planned_end_date": "2026-02-05T17:00:00Z",
      "actual_start_date": "2026-02-01T08:00:00Z",
      "actual_end_date": null,
      "dependencies": {
        "predecessors": [
          {
            "task_code": "A1000",
            "dependency_type": "FS",
            "lag_hours": 0.0
          }
        ],
        "successors": [
          {
            "task_code": "A1020",
            "dependency_type": "FS",
            "lag_hours": 0.0
          }
        ]
      }
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

## Section 2: Activities Array

### Schema (Single Activity)
```json
{
  "task_code": "A1010",
  "task_name": "Site Mobilization",
  "planned_start_date": "2026-02-01T08:00:00Z",
  "planned_end_date": "2026-02-05T17:00:00Z",
  "actual_start_date": "2026-02-01T08:00:00Z",
  "actual_end_date": null,
  "dependencies": {
    "predecessors": [...],
    "successors": [...]
  }
}
```

### Basic Activity Fields

| JSON Field | XER Table | XER Field | Data Type | Notes |
|------------|-----------|-----------|-----------|-------|
| `task_code` | `TASK` | `task_code` | String | **Unique identifier** - Activity ID |
| `task_name` | `TASK` | `task_name` | String | Activity name/description |
| `planned_start_date` | `TASK` | `target_start_date` | DateTime | Baseline start (ISO 8601) |
| `planned_end_date` | `TASK` | `target_end_date` | DateTime | Baseline finish (ISO 8601) |
| `actual_start_date` | `TASK` | `act_start_date` | DateTime | Actual start (null if not started) |
| `actual_end_date` | `TASK` | `act_end_date` | DateTime | Actual finish (null if not finished) |

---

## Section 3: Dependencies

### Predecessors

Each predecessor object contains:

```json
{
  "task_code": "A1000",
  "dependency_type": "FS",
  "lag_hours": 0.0
}
```

| JSON Field | XER Table | XER Field | Data Type | Notes |
|------------|-----------|-----------|-----------|-------|
| `task_code` | `TASK` | `task_code` | String | Predecessor activity code (join via TASKPRED.pred_task_id) |
| `dependency_type` | `TASKPRED` | `pred_type` | String | FS, SS, FF, or SF |
| `lag_hours` | `TASKPRED` | `lag_hr_cnt` | Float | Lag in hours (positive=delay, negative=lead) |

**Finding Predecessors:**
```
For Activity with task_code "A1010":
1. Find task_id from TASK where task_code = "A1010"
2. Query TASKPRED WHERE task_id = [found task_id]
3. For each pred_task_id, get task_code from TASK table
```

### Successors

Each successor object contains:

```json
{
  "task_code": "A1020",
  "dependency_type": "FS",
  "lag_hours": 0.0
}
```

| JSON Field | XER Table | XER Field | Data Type | Notes |
|------------|-----------|-----------|-----------|-------|
| `task_code` | `TASK` | `task_code` | String | Successor activity code (join via TASKPRED.task_id) |
| `dependency_type` | `TASKPRED` | `pred_type` | String | FS, SS, FF, or SF |
| `lag_hours` | `TASKPRED` | `lag_hr_cnt` | Float | Lag in hours |

**Finding Successors:**
```
For Activity with task_code "A1010":
1. Find task_id from TASK where task_code = "A1010"
2. Query TASKPRED WHERE pred_task_id = [found task_id]
3. For each task_id (successor), get task_code from TASK table
```

### Dependency Types

| Code | Meaning |
|------|---------|
| `FS` | Finish-to-Start |
| `SS` | Start-to-Start |
| `FF` | Finish-to-Finish |
| `SF` | Start-to-Finish |

---

## Complete Example

```json
{
  "project": {
    "project_code": "PRJ-2026-001",
    "project_name": "Office Building Construction"
  },
  "activities": [
    {
      "task_code": "A1000",
      "task_name": "Notice to Proceed",
      "planned_start_date": "2026-01-15T08:00:00Z",
      "planned_end_date": "2026-01-15T08:00:00Z",
      "actual_start_date": "2026-01-15T08:00:00Z",
      "actual_end_date": "2026-01-15T08:00:00Z",
      "dependencies": {
        "predecessors": [],
        "successors": [
          {
            "task_code": "A1010",
            "dependency_type": "FS",
            "lag_hours": 0.0
          }
        ]
      }
    },
    {
      "task_code": "A1010",
      "task_name": "Site Mobilization",
      "planned_start_date": "2026-02-01T08:00:00Z",
      "planned_end_date": "2026-02-05T17:00:00Z",
      "actual_start_date": "2026-02-03T08:00:00Z",
      "actual_end_date": null,
      "dependencies": {
        "predecessors": [
          {
            "task_code": "A1000",
            "dependency_type": "FS",
            "lag_hours": 0.0
          }
        ],
        "successors": [
          {
            "task_code": "A1020",
            "dependency_type": "FS",
            "lag_hours": 0.0
          },
          {
            "task_code": "A1030",
            "dependency_type": "FS",
            "lag_hours": 8.0
          }
        ]
      }
    },
    {
      "task_code": "A1020",
      "task_name": "Excavation",
      "planned_start_date": "2026-02-06T08:00:00Z",
      "planned_end_date": "2026-02-12T17:00:00Z",
      "actual_start_date": null,
      "actual_end_date": null,
      "dependencies": {
        "predecessors": [
          {
            "task_code": "A1010",
            "dependency_type": "FS",
            "lag_hours": 0.0
          }
        ],
        "successors": [
          {
            "task_code": "A1040",
            "dependency_type": "FS",
            "lag_hours": 0.0
          }
        ]
      }
    }
  ]
}
```

---

## XER Source Tables

### Required XER Tables

Only 3 tables are needed:

| XER Table | Purpose | Key Fields Used |
|-----------|---------|-----------------|
| `PROJECT` | Project info | proj_short_name, proj_name |
| `TASK` | Activity data | task_code, task_name, target_start_date, target_end_date, act_start_date, act_end_date |
| `TASKPRED` | Dependencies | task_id, pred_task_id, pred_type, lag_hr_cnt |

**Note:** `task_id` is used internally during parsing to build relationships from TASKPRED, but only `task_code` appears in the JSON output.

### XER Table Format Example

**PROJECT Table:**
```
%T	PROJECT
%F	proj_id	proj_short_name	proj_name
%R	12345	PRJ-2026-001	Office Building Construction
```

**TASK Table:**
```
%T	TASK
%F	task_id	task_code	task_name	target_start_date	target_end_date
%R	10000	A1000	Notice to Proceed	2026-01-15 08:00	2026-01-15 08:00
%R	10001	A1010	Site Mobilization	2026-02-01 08:00	2026-02-05 17:00
%R	10002	A1020	Excavation	2026-02-06 08:00	2026-02-12 17:00
```

**TASKPRED Table:**
```
%T	TASKPRED
%F	task_id	pred_task_id	pred_type	lag_hr_cnt
%R	10001	10000	PR_FS	0
%R	10002	10001	PR_FS	0
%R	10003	10001	PR_FS	8
```

---

## Date Format

### Input (XER)
- Format: `YYYY-MM-DD HH:MM`
- Example: `2026-02-01 08:00`

### Output (JSON)
- Format: ISO 8601 with timezone
- Example: `2026-02-01T08:00:00Z`
- Null dates: `null`

---

## Validation Rules

### Required Fields
- `task_code` - must be unique and not empty
- `task_name` - must not be empty
- `planned_start_date` - must be valid date
- `planned_end_date` - must be valid date

### Optional Fields
- `actual_start_date` - null if activity not started
- `actual_end_date` - null if activity not finished

### Data Integrity
- All predecessor/successor `task_code` references must exist in activities array
- `planned_end_date` >= `planned_start_date`
- If `actual_end_date` is not null, `actual_start_date` must also not be null
- `dependency_type` must be one of: FS, SS, FF, SF

---

## Processing Steps

1. Parse XER file and extract PROJECT, TASK, TASKPRED tables
2. Extract project information from PROJECT table (proj_short_name, proj_name)
3. Build a lookup map: `task_id` → `task_code` from TASK table
4. Create Activity objects from TASK table:
   - Extract: task_code, task_name, dates (planned + actual)
   - Store task_id temporarily for dependency resolution
5. For each activity, build dependencies:
   - **Predecessors:** Query TASKPRED where task_id = current activity's task_id
     - Get pred_task_id, convert to task_code using lookup map
   - **Successors:** Query TASKPRED where pred_task_id = current activity's task_id
     - Get task_id (successor), convert to task_code using lookup map
6. Convert dates from XER format to ISO 8601
7. Remove internal task_id references, keep only task_code
8. Generate JSON output

---

**Document Version:** 2.0 (Simplified)
**Last Updated:** 2026-01-20
**Related Documents:**
- technical_design.md (overall system design)
- critical_path_json_schema.md (critical path output)
