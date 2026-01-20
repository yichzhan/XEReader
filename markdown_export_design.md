# Markdown Export Design Document

## Overview
Add Markdown export capability to XEReader to generate human-readable reports from XER data.

## Design Decisions

### 1. Architecture
- **Approach:** Create separate `MarkdownExporter` class in `src/exporters/markdown_exporter.py`
- **Rationale:** Clean separation of concerns, keeps export formats independent

### 2. CLI Integration
- **Flag:** `--format {json,markdown,both}`
- **Default:** `json` (backward compatibility)
- **Examples:**
  ```bash
  python xereader.py project.xer --format json      # JSON only (default)
  python xereader.py project.xer --format markdown  # Markdown only
  python xereader.py project.xer --format both      # Both formats
  ```

### 3. Output Files
Following existing naming convention:
- `{filename}_activities.md` - All activities report
- `{filename}_critical_path.md` - Critical path report

### 4. Markdown Style
**Natural language format** - Prose-like with minimal tables, focusing on readability.

## File Structures

### activities.md - Natural Language Format

```markdown
# Project Activities Report

**{project_name}** ({project_code})

This report contains {count} activities for the project.

Report generated on {timestamp}.

---

## Activity List

### 1. A1000 - Notice to Proceed

**Planned Schedule:**
- Start: January 15, 2026 at 8:00 AM
- End: January 15, 2026 at 8:00 AM
- Duration: 0 days

**Actual Progress:**
- Started: January 15, 2026 at 8:00 AM
- Completed: January 15, 2026 at 8:00 AM
- Status: Completed

**Dependencies:**
- Predecessors: None
- Successors: A1010 (Finish-to-Start, no lag)

---

### 2. A1010 - Site Mobilization

**Planned Schedule:**
- Start: February 1, 2026 at 8:00 AM
- End: February 5, 2026 at 5:00 PM
- Duration: 4 days

**Actual Progress:**
- Not yet started

**Dependencies:**
- Predecessors: A1000 (Finish-to-Start, no lag)
- Successors: A1020 (Finish-to-Start, no lag)

---

## Summary Statistics

- Total activities: {count}
- Completed activities: {completed_count}
- In progress: {in_progress_count}
- Not started: {not_started_count}
```

**Proposed dependency format (for user confirmation):**
- Option A (minimal): Just list task codes
  ```
  Predecessors: A1000, A1005
  Successors: A1020
  ```

- Option B (with relationship type): Include dependency type
  ```
  Predecessors: A1000 (Finish-to-Start), A1005 (Start-to-Start, lag: 2 days)
  Successors: A1020 (Finish-to-Start)
  ```

**User to confirm:** Which dependency format do you prefer?

---

### critical_path.md - Natural Language Format

```markdown
# Critical Path Analysis Report

**{project_name}** ({project_code})

Analysis performed on {timestamp}.

---

## Project Summary

The project has a total duration of **106.5 days** (852.0 hours) from start to finish.

The analysis identified **2 critical paths** containing a total of **57 activities**. These critical paths represent the longest sequence of dependent activities that determine the minimum project duration.

---

## Critical Path #1 (Primary Path)

This is the primary critical path with a duration of **106.5 days** (852.0 hours) spanning **56 activities**.

### Path Sequence

**1. A1000 - Notice to Proceed**
- Planned: January 15, 2026 (8:00 AM to 8:00 AM)
- Duration: 0 days

**2. A1010 - Site Mobilization**
- Planned: February 1, 2026 at 8:00 AM to February 5, 2026 at 5:00 PM
- Duration: 4 days

**3. A1020 - Foundation Excavation**
- Planned: February 8, 2026 at 8:00 AM to February 15, 2026 at 5:00 PM
- Duration: 7 days

... (continues for all activities in sequence)

---

## Critical Path #2 (Alternate Path)

This is an alternate critical path with the same duration of **106.5 days** (852.0 hours) spanning **57 activities**.

### Path Sequence

**1. A1000 - Notice to Proceed**
- Planned: January 15, 2026 (8:00 AM to 8:00 AM)
- Duration: 0 days

... (continues for all activities in sequence)

---

## Analysis Notes

Critical paths represent sequences of activities where any delay will directly impact the project completion date. Project managers should monitor these activities closely and allocate resources to prevent delays.
```

**Proposed activity format (for user confirmation):**
- Option A (compact): Single line with dates
  ```
  **1. A1000 - Notice to Proceed** - January 15, 2026 (0 days)
  ```

- Option B (detailed): Multiple lines as shown above
  ```
  **1. A1000 - Notice to Proceed**
  - Planned: January 15, 2026 (8:00 AM to 8:00 AM)
  - Duration: 0 days
  ```

**User to confirm:** Which activity format do you prefer?

---

## Implementation Plan

### 1. Create MarkdownExporter class
**File:** `src/exporters/markdown_exporter.py`

**Class structure:**
```python
class MarkdownExporter:
    def __init__(self, project_info, activities):
        """Initialize with project info and activities list"""

    def export_activities(self, output_path):
        """Generate activities.md with natural language format"""

    def export_critical_path(self, output_path, critical_paths, project_duration):
        """Generate critical_path.md with natural language format"""

    # Helper methods
    def _format_date(self, date_str):
        """Convert ISO date to readable format: 'January 15, 2026 at 8:00 AM'"""

    def _format_duration(self, start_date, end_date):
        """Calculate and format duration between dates"""

    def _get_activity_status(self, activity):
        """Determine status: Completed, In Progress, Not Started"""

    def _format_dependencies(self, deps):
        """Format predecessor/successor lists"""
```

### 2. Update xereader.py
**Changes:**
- Add `--format` argument with choices: `json`, `markdown`, `both`
- Import MarkdownExporter
- Conditional export based on format flag
- Update output summary to show markdown files

### 3. Update .gitignore
```
*_activities.md
*_critical_path.md
```

### 4. Update documentation
- README.md - Add Markdown export section
- WORKFLOW.md - Add Markdown examples
- CLAUDE.md - Add MarkdownExporter to architecture

### 5. Testing
- Test with sample XER files
- Verify formatting and readability
- Test all three format options (json, markdown, both)

---

## Confirmed Design Specifications

1. **Dependencies format**: Include relationship types and lag
   - Format: `A1000 (Finish-to-Start)`, `A1005 (Start-to-Start, lag: 2 days)`

2. **Activity format in critical_path.md**: Compact single line
   - Format: `**1. A1000 - Notice to Proceed** - 2026-01-15 08:00 to 2026-01-15 08:00 (0 days)`

3. **Date format**: Shorter format
   - Format: `2026-01-15 08:00`

4. **No additional sections requested**

---

**Version:** 1.0 (Final)
**Last Updated:** 2026-01-21
**Status:** Ready for implementation
