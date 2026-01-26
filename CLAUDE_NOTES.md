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

**Test command:** `python xereader.py "input/CTF-3-1 LIII Schedule2023-10-31.xer" --verbose`

**Expected output:** 3 projects processed, 6 JSON files generated (2 per project), 1 cycles.log for CTF-3-1.
