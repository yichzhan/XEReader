# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
XEReader is a Python application that parses Oracle Primavera P6 XER files and generates separate output files per project:
1. **{xer}_{project_code}_activities.json** - All activities with dates and dependencies
2. **{xer}_{project_code}_critical_path.json** - Critical path sequence(s)
3. **{xer}_{project_code}_activities.md** - Human-readable Markdown report of all activities
4. **{xer}_{project_code}_critical_path.md** - Natural language critical path analysis report
5. **PNG diagrams** - Visual representation of critical paths (via visualize_critical_path.py)

**Execution Model:** Direct Python scripts (no installation required)

---

## Quick Start

### Installation
```bash
# Install dependencies
pip install -r requirements.txt
```

### Run Parser
```bash
# Basic usage - generates JSON files (default)
# Multi-project XER files automatically generate separate files per project
python xereader.py input.xer

# Generate Markdown reports instead
python xereader.py input.xer --format markdown

# Generate both JSON and Markdown
python xereader.py input.xer --format both

# With options
python xereader.py input.xer --output-dir ./output --verbose
```

### Generate Visualizations
```bash
# Generate diagram from critical path JSON
python visualize_critical_path.py project_critical_path.json

# Visualize specific path only
python visualize_critical_path.py project_critical_path.json --path-id 1

# Customize layout (10 boxes per row by default)
python visualize_critical_path.py project_critical_path.json --boxes-per-row 15
```

### Run Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test
pytest tests/test_parser.py
```

---

## Project Structure

```
XEReader/
├── xereader.py                    # Main entry point - XER parser
├── visualize_critical_path.py    # Critical path diagram generator
├── requirements.txt               # Dependencies
├── src/                           # Source code
│   ├── parser/                   # XER file parsing
│   ├── models/                   # Data models
│   ├── processors/               # Business logic (CPM algorithm)
│   ├── exporters/                # JSON generation
│   └── utils/                    # Utilities
├── tests/                         # Test suite
└── WORKFLOW.md                    # Complete workflow guide
```

---

## Architecture

### Data Flow
```
XER File → Parser → Activity Objects → Group by Project → CPM Calculator → Exporters
                         ↓                    ↓                              ↓
                    Dependencies        Per-Project         JSON / Markdown / PNG
                  (within-project)      Processing         (separate files per project)
```

### Key Components

1. **XER Parser** (`src/parser/`)
   - Reads XER file (tab-delimited format)
   - Extracts PROJECT, TASK, TASKPRED tables
   - Returns raw data dictionaries

2. **Activity Processor** (`src/processors/activity_processor.py`)
   - Converts TASK rows to Activity objects
   - Stores `proj_id` for each activity
   - Builds task_id → task_code lookup map
   - `process_all_projects()` - Returns all ProjectInfo objects
   - `group_by_project()` - Groups activities by project ID
   - `get_activities_for_project(proj_id)` - Returns activities for specific project
   - Resolves dependencies (only within-project links)

3. **Critical Path Calculator** (`src/processors/critical_path_calculator.py`)
   - Builds network graph (NetworkX)
   - `detect_cycles()` / `has_cycles()` - Cycle detection before CPM
   - Performs CPM forward/backward pass
   - Calculates total float
   - Identifies longest path(s)

4. **Exporters** (`src/exporters/`)
   - **JSON Exporter** - Generates activities.json and critical_path.json with schema compliance
   - **Markdown Exporter** - Generates human-readable reports with natural language formatting
     - Handles both dict and object inputs (ProjectInfo, Activity dataclasses)
     - Formats dependencies with relationship types (FS, SS, FF, SF) and lag
     - Uses compact single-line format for critical path activities
     - Date format: `YYYY-MM-DD HH:MM`

5. **Visualization Tool** (`visualize_critical_path.py`)
   - Reads critical_path.json
   - Generates PNG diagrams with matplotlib
   - Horizontal layout with 10 boxes per row (configurable)
   - Three-segment wrapping arrows for row transitions
   - Separate diagrams for multiple critical paths

---

## Key Design Decisions

1. **Use `task_code` not `task_id`**
   - `task_code` is persistent across exports (Activity ID)
   - `task_id` only used internally during parsing

2. **Separate output files per project**
   - XER files can contain multiple projects
   - Each project gets its own output files
   - `proj_short_name` (project_code) is unique in P6 database
   - Dependencies only link activities within the same project

3. **Critical path = longest path**
   - Not just zero float activities
   - Proper CPM definition using NetworkX

4. **Output file naming convention**
   - `{xer_filename}_{project_code}_activities.json/md`
   - `{xer_filename}_{project_code}_critical_path.json/md`
   - `{xer_filename}_{project_code}_critical_path_path{N}.png`
   - `{xer_filename}_{project_code}_cycles.log` - circular dependencies (when detected)

5. **Multiple output formats**
   - JSON for programmatic use (default)
   - Markdown for human readability with natural language style
   - PNG for visual representation
   - Selectable via `--format {json,markdown,both}` flag

6. **Horizontal diagram layout**
   - Left-to-right flow (not vertical)
   - Grid-based positioning with automatic wrapping
   - Wrapping arrows route through space between rows
   - Default 10 boxes per row (configurable)

7. **Within-project dependencies only**
   - Cross-project dependencies are ignored
   - Each project has independent dependency graph
   - Prevents cycles caused by cross-project links

8. **Circular dependency handling**
   - Cycles in dependency graph prevent CPM calculation
   - Automatic cycle detection before CPM (per project)
   - Generates `{xer}_{project}_cycles.log` with cycle details
   - Activities export still works; critical path is skipped

---

## Common Tasks

### Parse a New XER Table
1. Add table name to `table_extractor.py`
2. Create data model in `src/models/`
3. Update processor to handle new table
4. Add tests

### Add a New CLI Option
1. Update argument parser in `xereader.py`
2. Implement functionality
3. Update README.md
4. Add tests

### Modify JSON Output Schema
1. Update schema documentation
2. Update exporter code
3. Update tests and examples
4. Document in design_decisions.md

### Add a New Export Format
1. Create exporter class in `src/exporters/`
2. Handle both dict and object inputs (use `hasattr()` checks)
3. Update `xereader.py` to integrate new exporter
4. Update `--format` CLI argument choices
5. Add output file pattern to `.gitignore`
6. Update documentation

### Modify Visualization Layout
1. Update `draw_critical_path_diagram()` in visualize_critical_path.py
2. Key parameters: `boxes_per_row`, `box_width`, `box_height`, `horizontal_spacing`, `vertical_spacing`
3. Arrow logic: same-row arrows vs wrapping arrows (three-segment path)
4. Test with real data to ensure readability

---

## Debugging Tips

### XER Parsing Issues
- Check file encoding (UTF-8 vs latin-1)
- Verify table markers (%T, %F, %R)
- Check for tab characters (not spaces)

### Critical Path Issues
- Verify graph connectivity
- Check for circular dependencies (per project)
- Ensure float calculations are correct
- Validate forward/backward pass

### JSON Output Issues
- Validate against schema
- Check for null values
- Verify date formatting (ISO 8601)
- Ensure all task_code references exist

---

## Dependencies

### Required
- **networkx** - Graph algorithms for CPM
- **python-dateutil** - Date parsing
- **matplotlib** - Diagram generation (PNG output)

### Development
- **pytest** - Testing framework
- **pytest-cov** - Coverage reporting

---

## Related Documentation

- [README.md](README.md) - User guide and API reference
- [WORKFLOW.md](WORKFLOW.md) - Complete workflow from XER to diagram
- [design_decisions.md](design_decisions.md) - Design rationale
- [activities_json_schema.md](activities_json_schema.md) - activities.json spec
- [critical_path_json_schema.md](critical_path_json_schema.md) - critical_path.json spec
- [markdown_export_design.md](markdown_export_design.md) - Markdown export specifications

---

**Version:** 3.0
**Last Updated:** 2026-01-26
