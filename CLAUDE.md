# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
XEReader is a Python application that parses Oracle Primavera P6 XER files and generates multiple output formats:
1. **activities.json** - All activities with dates and dependencies
2. **critical_path.json** - Critical path sequence(s)
3. **activities.md** - Human-readable Markdown report of all activities
4. **critical_path.md** - Natural language critical path analysis report
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

# Customize layout (20 boxes per row by default)
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
XER File → Parser → Activity Objects → CPM Calculator → Exporters → Outputs
                         ↓                                   ↓
                    Dependencies                    JSON / Markdown / PNG
                                                   (selectable via --format)
```

### Key Components

1. **XER Parser** (`src/parser/`)
   - Reads XER file (tab-delimited format)
   - Extracts PROJECT, TASK, TASKPRED tables
   - Returns raw data dictionaries

2. **Activity Processor** (`src/processors/activity_processor.py`)
   - Converts TASK rows to Activity objects
   - Builds task_id → task_code lookup map
   - Resolves dependencies (predecessors + successors)
   - Converts task_id references to task_code

3. **Critical Path Calculator** (`src/processors/critical_path_calculator.py`)
   - Builds network graph (NetworkX)
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
   - Horizontal layout with 20 boxes per row (configurable)
   - Three-segment wrapping arrows for row transitions
   - Separate diagrams for multiple critical paths

---

## Key Design Decisions

1. **Use `task_code` not `task_id`**
   - `task_code` is persistent across exports (Activity ID)
   - `task_id` only used internally during parsing

2. **Two separate JSON files**
   - Separation of concerns
   - Smaller file sizes

3. **Critical path = longest path**
   - Not just zero float activities
   - Proper CPM definition using NetworkX

4. **Output file naming convention**
   - `{filename}_activities.json` / `{filename}_activities.md` - uses input XER filename without .xer extension
   - `{filename}_critical_path.json` / `{filename}_critical_path.md`
   - `{filename}_critical_path_path{N}.png` - separate file per critical path

5. **Multiple output formats**
   - JSON for programmatic use (default)
   - Markdown for human readability with natural language style
   - PNG for visual representation
   - Selectable via `--format {json,markdown,both}` flag

6. **Horizontal diagram layout**
   - Left-to-right flow (not vertical)
   - Grid-based positioning with automatic wrapping
   - Wrapping arrows route through space between rows
   - Default 20 boxes per row (configurable)

---

## Development Workflow

### Adding a New Feature
1. Update relevant design documents
2. Write tests first (TDD)
3. Implement feature
4. Update documentation
5. Run full test suite

### Code Style
- Python 3.10+
- Use type hints
- Follow PEP 8
- Use dataclasses for models
- Document complex logic

### Testing
- Unit tests for all modules
- Integration tests for full flow
- Test fixtures in `tests/fixtures/`
- Aim for >80% coverage

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
- Check for circular dependencies
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

**Version:** 2.1
**Last Updated:** 2026-01-21
