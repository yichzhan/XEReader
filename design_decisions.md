# Design Decisions Log

## Document Purpose
This document captures key design decisions made during the XEReader project design phase, including rationale and alternatives considered.

---

## 1. Output Format: Two Separate JSON Files

**Decision:** Generate two separate JSON files instead of one combined file.

**Files:**
1. `activities.json` - All activities with basic information and dependencies
2. `critical_path.json` - Critical path sequence only

**Rationale:**
- Separation of concerns: activity data vs critical path analysis
- Smaller file sizes for consumers who only need one aspect
- Easier to update critical path independently if recalculated

**Date:** 2026-01-20

---

## 2. Activity Unique Identifier: task_code (not task_id)

**Decision:** Use `task_code` as the sole unique identifier in JSON output, exclude `task_id`.

**Key Findings:**
- `task_id`: Temporary identifier, changes on every XER export/import, used only within a single XER file
- `task_code`: Persistent identifier (Activity ID in P6), remains consistent across exports, used for matching during imports

**Rationale:**
- `task_code` is the true business key that users recognize
- `task_code` persists across schedule versions, enabling comparison
- Simpler JSON structure without redundant identifiers
- `task_id` only needed internally during parsing to resolve TASKPRED relationships

**Implementation Note:**
- Parser uses `task_id` internally to build dependency graph
- Convert all `task_id` references to `task_code` before JSON export
- Build `task_id` → `task_code` lookup map during processing

**Date:** 2026-01-20
**Source:** Planning Planet forums, XER file documentation

---

## 3. Date Fields: Include Both Planned and Actual Dates

**Decision:** Include both planned (baseline) and actual dates in activities.json.

**Fields Included:**
- `planned_start_date` (from `target_start_date`)
- `planned_end_date` (from `target_end_date`)
- `actual_start_date` (from `act_start_date`)
- `actual_end_date` (from `act_end_date`)

**Rationale:**
- **Delay Detection:** Can calculate delay = `actual_start - planned_start`
- **Progress Tracking:** Know which activities have started/finished
- **Schedule Variance:** Compare planned vs actual performance
- **Minimal Overhead:** Only 2 additional optional fields per activity
- **Essential for Analysis:** Required for meaningful schedule analysis

**Alternatives Considered:**
- Planned dates only: Insufficient for delay detection
- Early/Late dates: Not needed for basic delay analysis, adds complexity
- Status field only: Doesn't show magnitude of delays

**Date:** 2026-01-20

---

## 4. Dependency Structure: Bidirectional (Predecessors + Successors)

**Decision:** Include both predecessors and successors for each activity.

**Structure:**
```json
"dependencies": {
  "predecessors": [...],  // What must finish before this starts
  "successors": [...]     // What depends on this activity
}
```

**Rationale:**
- **Backward Tracing:** Identify root causes of delays (follow predecessors)
- **Forward Impact:** Identify downstream impacts of delays (follow successors)
- **Complete Analysis:** Enable both impact analysis and root cause analysis
- **Graph Traversal:** Support both directions without rebuilding graph

**Use Cases:**
- "Why is Activity X delayed?" → Check predecessors recursively
- "If Activity X delays, what's impacted?" → Check successors recursively
- Critical path calculation requires both directions

**Data Source:**
- Predecessors: Query `TASKPRED WHERE task_id = current_activity`
- Successors: Query `TASKPRED WHERE pred_task_id = current_activity`

**Date:** 2026-01-20

---

## 5. Dependency Details: task_code + type + lag

**Decision:** Each dependency includes three fields only.

**Fields:**
- `task_code`: Related activity identifier
- `dependency_type`: FS, SS, FF, or SF
- `lag_hours`: Lag/lead time in hours

**Rationale:**
- **Sufficient for Impact Analysis:** Can determine how delays propagate
- **Type Matters:** Different dependency types (FS vs SS) affect timing differently
- **Lag is Critical:** Lag provides schedule buffer, affects delay propagation
- **Minimal but Complete:** No unnecessary fields, all essential data present

**Dependency Type Impact:**
- `FS` (Finish-to-Start): Predecessor must finish before successor starts (most common)
- `SS` (Start-to-Start): Both activities start together
- `FF` (Finish-to-Finish): Both activities finish together
- `SF` (Start-to-Finish): Successor finishes when predecessor starts (rare)

**Date:** 2026-01-20

---

## 6. Simplified activities.json Schema

**Decision:** Minimize fields in activities.json to essential data only.

**Final Fields (6 per activity):**
1. `task_code` - Unique identifier
2. `task_name` - Activity description
3. `planned_start_date` - Baseline start
4. `planned_end_date` - Baseline finish
5. `actual_start_date` - Actual start (nullable)
6. `actual_end_date` - Actual finish (nullable)
7. `dependencies` - Predecessors and successors

**Excluded Fields:**
- ❌ WBS information (not needed for delay analysis)
- ❌ Status codes (can infer from actual dates)
- ❌ Percent complete (not essential for dependency analysis)
- ❌ Duration fields (can calculate from dates)
- ❌ Float values (belong in critical_path.json)
- ❌ Calendar information (internal processing detail)
- ❌ Activity codes (custom classifications, not essential)
- ❌ Constraints (complex, not essential for basic analysis)
- ❌ Early/Late dates (internal CPM calculations)

**Rationale:**
- Focus on core use case: activity identification, dates, and dependencies
- Reduce JSON file size and complexity
- Easier for consumers to understand and use
- Can add fields later if needed (non-breaking change)

**Date:** 2026-01-20

---

## 7. Critical Path Definition: Longest Path, Not Just Zero Float

**Decision:** Calculate critical path as the longest sequence through the network, not just activities with zero float.

**Key Understanding:**
- **Critical Path:** The longest sequence of dependent activities (CPM definition)
- **Critical Activities:** Activities with zero total float
- **Important:** Not all critical activities are on THE critical path!

**Example:**
```
Path 1: A → B → End (10 days, float: 0)
Path 2: A → C → D → End (15 days, float: 0)

All activities have zero float, but only Path 2 is THE critical path.
```

**Algorithm:**
1. Calculate total float for all activities (forward/backward pass)
2. Filter activities with float ≤ 0 (critical activities)
3. Find ALL paths through critical activities
4. Calculate duration for each path
5. Select the longest path(s) as THE critical path

**Rationale:**
- **Correctness:** Adheres to proper CPM definition
- **Project Duration:** Critical path length = minimum project duration
- **Accurate Impact:** Only delays on longest path affect project completion
- **Industry Standard:** Aligns with how P6 and other tools define critical path

**Date:** 2026-01-20
**Source:** CPM scheduling theory, technical design research

---

## 8. Project Information: Minimal Fields

**Decision:** Include only essential project identification in both JSON files.

**Fields:**
- `project_code` (from `proj_short_name`)
- `project_name` (from `proj_name`)

**Excluded:**
- ❌ `project_id` (temporary, changes across exports)
- ❌ Dates (available from activities)
- ❌ Statistics (can be calculated from activities)

**Rationale:**
- Project code and name are sufficient for identification
- Avoid redundant data that can be derived from activities
- Keep JSON simple and focused

**Date:** 2026-01-20

---

## 9. Date Format: ISO 8601

**Decision:** Use ISO 8601 format for all dates in JSON output.

**Format:** `YYYY-MM-DDTHH:MM:SSZ`
**Example:** `2026-02-01T08:00:00Z`

**Input (XER):** `YYYY-MM-DD HH:MM` or `YYYY-MM-DD-HH.MM`

**Rationale:**
- Industry standard for JSON APIs
- Unambiguous timezone handling (Z = UTC)
- Easy to parse in all programming languages
- Sortable string format

**Null Handling:** Use JSON `null` for missing dates, not empty strings

**Date:** 2026-01-20

---

## 10. Technology Stack: Python 3.10+

**Decision:** Implement using Python 3.10 or higher.

**Key Libraries:**
- **Standard Library:** `csv`, `dataclasses`, `datetime`, `json`, `typing`
- **NetworkX:** Graph operations, topological sorting, path finding
- **python-dateutil:** Robust date parsing

**Rationale:**
- Rich ecosystem for data processing
- NetworkX provides excellent graph algorithms for CPM
- Strong typing with dataclasses and type hints
- Easy to read and maintain
- Existing XER parsing libraries available for reference

**Alternatives Considered:**
- Node.js/TypeScript: Good JSON handling, but weaker graph libraries
- Go: Fast performance, but more complex for data processing
- Java: Enterprise-grade, but overkill for this use case

**Date:** 2026-01-20

---

## 11. Processing Strategy: Internal task_id, Export task_code

**Decision:** Use `task_id` during parsing, convert to `task_code` for JSON export.

**Processing Steps:**
1. Parse TASK table, store both `task_id` and `task_code`
2. Build `task_id` → `task_code` lookup map
3. Parse TASKPRED using `task_id` and `pred_task_id` (as stored in XER)
4. Build dependency graph using internal `task_id`
5. Perform CPM calculations on graph
6. Convert all `task_id` references to `task_code` before JSON export
7. Output only contains `task_code`

**Rationale:**
- TASKPRED table uses `task_id`, so must use it for parsing
- Conversion to `task_code` provides persistent identifiers for output
- Best of both worlds: easy parsing + persistent output
- Internal implementation detail doesn't leak into API

**Date:** 2026-01-20

---

## 12. XER Tables Required: Only 3 Tables

**Decision:** Parse only essential tables from XER file.

**Required Tables:**
1. `PROJECT` - Project identification
2. `TASK` - Activity data
3. `TASKPRED` - Dependencies

**Optional Tables (Not Used in V1):**
- `PROJWBS` - WBS hierarchy (future enhancement)
- `CALENDAR` - Working calendars (future enhancement)
- `TASKRSRC` - Resource assignments (future enhancement)
- `ACTVCODE` - Activity codes (future enhancement)

**Rationale:**
- Minimize complexity for initial version
- Three tables provide all data needed for core functionality
- Can add additional tables in future versions
- Faster parsing with fewer tables

**Date:** 2026-01-20

---

## 13. Execution Model: Direct Python Script

**Decision:** Implement as a standalone Python script that can be executed directly from terminal, not a pip-installable package.

**Execution Method:**
```bash
python xereader.py input.xer
```

**Structure:**
- Single entry point script or simple module structure
- No setup.py or pip installation required
- Dependencies managed via requirements.txt
- Users run directly with Python interpreter

**Rationale:**
- **Simplicity:** Easier to distribute and use (just copy files)
- **No Installation:** No need for pip install, virtual env setup minimal
- **Development Speed:** Faster to develop without packaging overhead
- **Flexibility:** Easy to modify and customize for specific needs
- **Transparency:** Users can see and modify source code directly

**Distribution:**
- Users clone/download the repository
- Install dependencies: `pip install -r requirements.txt`
- Run directly: `python xereader.py <input.xer>`

**Future Evolution:**
- Can be packaged later if needed (add setup.py)
- Current approach doesn't prevent future pip packaging
- Maintains maximum flexibility for V1

**Date:** 2026-01-20

---

## Summary of Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Output Format | Two separate JSON files | Separation of concerns, smaller files |
| Activity ID | `task_code` only | Persistent identifier, user-recognizable |
| Dates | Planned + Actual | Enable delay detection and variance analysis |
| Dependencies | Bidirectional (pred + succ) | Support both root cause and impact analysis |
| Dependency Fields | code + type + lag | Sufficient for delay propagation analysis |
| activities.json | Minimal essential fields | Simple, focused, easy to consume |
| Critical Path | Longest path algorithm | Correct CPM definition, accurate impact |
| Date Format | ISO 8601 | Industry standard, unambiguous |
| Technology | Python 3.10+ | Rich ecosystem, NetworkX for graphs |
| Processing | task_id internal, task_code output | Easy parsing, persistent output |
| XER Tables | 3 tables only | Minimal complexity, core functionality |
| Execution Model | Direct Python script | Simple distribution, no installation needed |

---

**Document Version:** 1.0
**Last Updated:** 2026-01-20
**Related Documents:**
- technical_design.md
- activities_json_schema.md
- critical_path_json_schema.md (pending)
