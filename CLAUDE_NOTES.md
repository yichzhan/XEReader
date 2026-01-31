# CLAUDE_NOTES.md

Session summary for project-based output implementation (2026-01-26)

---

## 1. Goal and Scope

**Problem:** Multi-project XER files contain duplicate `task_code` values across projects, causing validation failures and incorrect dependency graphs.

**Previous approach:** `--deduplicate` flag that kept first occurrence and discarded duplicates to a log file. This lost data and still had issues with cross-project dependency cycles.

**New approach:** Automatically generate separate output files per project. Each project gets its own `{xer}_{project_code}_activities.json/md` and `{xer}_{project_code}_critical_path.json/md`. Dependencies are only linked within the same project, eliminating cross-project issues.

**Key insight:** Oracle P6's `proj_short_name` (project_code) is unique per database, confirmed via [Protrain](https://www.protrain.com/blog/understanding-primavera-p6-database-schema) - P6 enforces uniqueness and appends "-1" if duplicates are attempted.

---

## 2. Files Touched

| File | Changes |
|------|---------|
| `src/models/activity.py` | Added `proj_id: Optional[int]` field |
| `src/processors/activity_processor.py` | Added `process_all_projects()`, `group_by_project()`, `get_activities_for_project()`. Removed `DuplicateInfo` and `deduplicate_activities()`. Updated `process_dependencies()` to skip cross-project links. |
| `src/utils/validators.py` | Removed `strict` parameter and duplicate task_code validation |
| `xereader.py` | Removed `--deduplicate` and `--skip-duplicate-validation` flags. Rewrote main flow to loop through projects and generate separate files. Updated to v2.0. |
| `CLAUDE.md` | Updated to v3.0 with new architecture documentation |

---

## 3. Important Design Decisions

1. **Within-project dependencies only:** Cross-project dependencies are silently ignored (not warned). Rationale: P6 projects are typically independent; cross-project links are rare and usually data artifacts.

2. **Always include project_code in filename:** Even for single-project XER files, output is `{xer}_{project_code}_activities.json`. This ensures consistent naming and avoids filename collisions.

3. **Removed old flags entirely:** No backward compatibility for `--deduplicate` or `--skip-duplicate-validation`. Clean break since this is a fundamental architecture change.

4. **Per-project cycle detection:** Each project is processed independently with its own CPM calculation. A cycle in one project doesn't affect others.

---

## 4. Known Limitations and Open Questions

- **No cross-project dependency warning:** Currently silently skipped. Consider adding a verbose log for debugging.
- **Empty project names:** Test XER showed projects with empty `proj_name` but valid `project_code`. Output shows `(CTF-3-1)` format which works but looks odd.
- **Visualization tool:** `visualize_critical_path.py` unchanged - still expects single-project JSON. May need updates to handle project-specific files.
- **Tests not updated:** Unit tests may fail if they depend on old `deduplicate_activities()` or `strict` parameter.

---

## 5. Next Steps

- [ ] Run `pytest` and fix any broken tests
- [ ] Update `visualize_critical_path.py` if needed for new file naming
- [ ] Add verbose logging for skipped cross-project dependencies
- [ ] Consider adding `--single-project` flag if users want old behavior
- [ ] Update README.md with new usage examples
- [ ] Git commit: `"Implement project-based output for multi-project XER files"`
- [ ] Clean up old output files in `output/` directory (legacy format)

---

## 6. Planned Feature: Activity Notes from UDFVALUE

**Date:** 2026-01-30

**Goal:** Include `udf_text` from UDFVALUE table as activity notes to explain schedule changes.

**Data mapping:**
- `UDFVALUE.fk_id` → `TASK.task_id` → `Activity`
- `UDFVALUE.udf_text` contains schedule change explanations (e.g., "acceleration schedule pending on EOTR-001 results")

**Implementation plan:**

| File | Change |
|------|--------|
| `src/models/activity.py` | Add `notes: List[str] = field(default_factory=list)` |
| `src/processors/activity_processor.py` | Process UDFVALUE table, build `task_id → [udf_text]` map, attach to activities |
| `src/exporters/json_exporter.py` | Include `notes` array in `to_dict()` output |
| `src/exporters/markdown_exporter.py` | Display notes as bullet points under each activity |

**Output example (JSON):**
```json
{
  "task_code": "A1234",
  "task_name": "Installation Work",
  "notes": ["acceleration schedule pending on EOTR-001 results"],
  ...
}
```

**Source file:** Found in `examples/Cracker_Schedule_Updated.xer` (27 activities have EOTR-001 notes)

**Status:** ✅ Implemented (2026-01-30)

**Test result:** `python xereader.py examples/Cracker_Schedule_Updated.xer --format both --verbose`
- 4011 notes attached to activities
- EOTR-001 notes appear in both JSON and Markdown output

---

## 7. Analysis: Delay Reason Fields in XER Files

**Date:** 2026-01-30

**Question:** Is there a dedicated "delay reason" field in XER files?

**Findings:**

### UDF Types in Cracker_Schedule_Updated.xer

| UDF ID | Label | Purpose |
|--------|-------|---------|
| 129 | user_text2 | Generic text field |
| 137 | **EOT-60%MR** | Extension of Time - 60% Model Review |
| 138 | **Remark** | Generic remarks |
| 329 | user_text01 | Generic text field |
| 829 | **备注** (Notes) | Generic notes (Chinese label) |
| 1531 | **EOT** | Extension of Time |

**Key insight:** UDF type 829 is NOT a dedicated delay category - it's a generic "Notes/Remarks" field. Delay information is stored there by convention, not by schema design.

### Other Delay-Related Data in XER

1. **TASK table** - Dedicated delay event activities:
   - Task codes starting with `0000AE*` are delay events
   - Examples: "Delay Event 01: HQC Beijing Office Lockdown by Covid-19 (3 Weeks)"
   - Already captured as regular activities

2. **TASK table fields** - `suspend_date` / `resume_date`:
   - Track when activities were suspended/resumed
   - Not currently exported

3. **TASKMEMO table** - Task memos:
   - HTML-encoded notes attached to tasks
   - Not currently processed (would need HTML stripping)

4. **PROJWBS table** - WBS categories:
   - Contains "Delay Event 01", "Owner's Delay", etc.
   - WBS hierarchy for organizing delay events

### Current Implementation

- Captures ALL `udf_text` values regardless of UDF type
- No filtering by specific UDF categories
- Delay reasons captured through generic notes field

### Potential Enhancements (Not Implemented)

1. Filter notes by specific UDF types (137, 829, 1531)
2. Add UDF type label to output: `{"EOT": "...", "Remark": "..."}`
3. Extract `suspend_date`/`resume_date` from TASK table
4. Process TASKMEMO table with HTML stripping

**Decision:** Keep current behavior (capture all notes). UDF type filtering can be added later if needed.

---

## 8. Enhancement: UDF Type Labels in Notes

**Date:** 2026-01-30

**Goal:** Add UDF type labels to notes for better categorization and filtering.

**Previous format:**
```json
"notes": ["acceleration schedule pending on EOTR-001 results"]
```

**New format:**
```json
"notes": [
  {"label": "备注", "text": "acceleration schedule pending on EOTR-001 results"},
  {"label": "EOT", "text": "Y"}
]
```

**Implementation:**

| File | Change |
|------|--------|
| `src/models/activity.py` | Changed `notes: List[str]` to `notes: List[Dict[str, str]]` |
| `src/processors/activity_processor.py` | Updated `process_udf_values()` to accept UDFTYPE table, build `udf_type_id → label` map |
| `xereader.py` | Pass UDFTYPE table to `process_udf_values()` |
| `src/exporters/markdown_exporter.py` | Display notes as `**label:** text` format |

**Markdown output:**
```
- **Notes:**
  - **备注:** acceleration schedule pending on EOTR-001 results
  - **EOT:** Y
```

**Status:** ✅ Implemented (2026-01-30)

**Test result:** `python xereader.py input/Cracker_Schedule_Updated.xer --format both --verbose`
- 4135 notes attached to activities
- Labels correctly mapped from UDFTYPE table

---

## 9. Fix: Chinese Character Encoding (GBK)

**Date:** 2026-01-31

**Problem:** Chinese characters in UDF labels (e.g., `备注`) appeared garbled as `±¸×¢` in output files.

**Root cause:** XER files from Chinese P6 installations use GBK encoding for Chinese text, but the parser was falling back to latin-1 which misinterpreted the bytes.

**Analysis:**
```
Bytes in file: \xb1\xb8\xd7\xa2
GBK decode:    备注  ✓
latin-1:       ±¸×¢  ✗
```

**Solution:** Updated `src/parser/xer_parser.py` to try GBK encoding with `errors='replace'` before falling back to latin-1.

**Encoding priority:**
1. UTF-8 (strict) - for modern XER files
2. GBK with `errors='replace'` - for Chinese XER files (preserves Chinese, replaces invalid bytes)
3. latin-1 (fallback) - always succeeds but may garble non-ASCII

**Implementation:**
```python
# First try UTF-8 (strict)
try:
    with open(self.file_path, 'r', encoding='utf-8') as f:
        content = f.readlines()
except UnicodeDecodeError:
    pass

# Then try GBK with replacement for invalid bytes
if content is None:
    with open(self.file_path, 'r', encoding='gbk', errors='replace') as f:
        content = f.readlines()
```

**Status:** ✅ Fixed (2026-01-31)

**Test result:**
- Chinese labels now display correctly: `"label": "备注"`
- Only 1 replacement character in entire file (at byte position 656, in CURRTYPE table)

---

**Test command:** `python xereader.py "input/CTF-3-1 LIII Schedule2023-10-31.xer" --verbose`

**Expected output:** 3 projects processed, 6 JSON files generated (2 per project), 1 cycles.log for CTF-3-1.
