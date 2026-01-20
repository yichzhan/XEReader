# CLAUDE.md - XEReader Development Guide

## Project Overview
XEReader is a Python application that parses Oracle Primavera P6 XER files and generates two JSON outputs:
1. **activities.json** - All activities with dates and dependencies
2. **critical_path.json** - Critical path sequence(s)

**Execution Model:** Direct Python script (run with `python xereader.py input.xer`)

---

## Quick Start

### Installation
```bash
# Install dependencies
pip install -r requirements.txt
```

### Run
```bash
# Basic usage
python xereader.py input.xer

# With options
python xereader.py input.xer --output-dir ./output --verbose
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
├── xereader.py              # Main entry point
├── requirements.txt         # Dependencies
├── src/                     # Source code
│   ├── parser/             # XER file parsing
│   ├── models/             # Data models
│   ├── processors/         # Business logic
│   ├── exporters/          # JSON generation
│   └── utils/              # Utilities
├── tests/                   # Test suite
├── examples/                # Sample outputs
└── docs/                    # Design documents
```

---

## Architecture

### Data Flow
```
XER File → Parser → Activity Objects → CPM Calculator → JSON Exporter
                         ↓
                    Dependencies
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

4. **JSON Exporter** (`src/exporters/json_exporter.py`)
   - Generates activities.json
   - Generates critical_path.json
   - Ensures schema compliance

---

## Key Design Decisions

1. **Use `task_code` not `task_id`**
   - `task_code` is persistent across exports
   - `task_id` only used internally during parsing

2. **Two separate JSON files**
   - Separation of concerns
   - Smaller file sizes

3. **Critical path = longest path**
   - Not just zero float activities
   - Proper CPM definition

4. **Direct Python execution**
   - No pip install needed
   - Simple distribution

See [design_decisions.md](design_decisions.md) for full details.

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

### Development
- **pytest** - Testing framework
- **pytest-cov** - Coverage reporting

---

## Related Documentation

- [technical_design.md](technical_design.md) - System architecture
- [design_decisions.md](design_decisions.md) - Design rationale
- [activities_json_schema.md](activities_json_schema.md) - activities.json spec
- [critical_path_json_schema.md](critical_path_json_schema.md) - critical_path.json spec
- [implementation_plan.md](implementation_plan.md) - Development phases

---

## Future Enhancements

Potential features for future versions:
- WBS hierarchy support
- Calendar integration
- Resource assignments
- Visualization/diagrams
- Web interface
- Database output

---

**Version:** 1.0
**Last Updated:** 2026-01-20
