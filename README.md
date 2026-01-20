# XEReader - Primavera P6 XER File Parser

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

XEReader is a Python application that parses Oracle Primavera P6 XER files and generates two JSON outputs:
1. **activities.json** - All activities with dates and dependencies
2. **critical_path.json** - Critical path sequence(s) using proper CPM analysis

## Features

- ✅ **Direct Python Execution** - No installation required, just run with Python
- ✅ **Complete XER Parsing** - Reads PROJECT, TASK, and TASKPRED tables
- ✅ **Proper CPM Algorithm** - Forward/backward pass with longest path calculation
- ✅ **Simplified JSON Schema** - Only essential fields for practical use
- ✅ **Persistent Identifiers** - Uses `task_code` (Activity ID), not temporary `task_id`
- ✅ **Bidirectional Dependencies** - Both predecessors and successors
- ✅ **Multiple Critical Paths** - Supports and separately identifies all critical paths
- ✅ **Fast Processing** - Handles 3000+ activities in under 1 second
- ✅ **Comprehensive Validation** - Data integrity checks throughout

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/xereader.git
cd xereader

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```bash
# Parse XER file (outputs to current directory)
python xereader.py project.xer

# Specify output directory
python xereader.py project.xer --output-dir ./output

# Verbose mode
python xereader.py project.xer --verbose

# Validate only (no output files)
python xereader.py project.xer --validate-only
```

## Output Files

### activities.json

Contains all activities with essential information:

```json
{
  "project": {
    "project_code": "PRJ-2026-001",
    "project_name": "Sample Construction Project"
  },
  "activities": [
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
          }
        ]
      }
    }
  ]
}
```

**Fields:**
- `task_code` - Activity ID (persistent identifier)
- `task_name` - Activity description
- `planned_start_date` / `planned_end_date` - Baseline dates
- `actual_start_date` / `actual_end_date` - Actual dates (null if not started/completed)
- `dependencies.predecessors` - Activities that must finish before this one
- `dependencies.successors` - Activities that depend on this one

### critical_path.json

Contains the critical path sequence(s):

```json
{
  "project": {
    "project_code": "PRJ-2026-001",
    "project_name": "Sample Construction Project"
  },
  "summary": {
    "total_duration_hours": 852.0,
    "total_duration_days": 106.5,
    "critical_path_count": 1,
    "total_activities_on_critical_paths": 6
  },
  "critical_paths": [
    {
      "path_id": 1,
      "is_primary": true,
      "duration_hours": 852.0,
      "duration_days": 106.5,
      "activity_count": 6,
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
    }
  ]
}
```

**Fields:**
- `summary` - Overall project statistics
- `critical_paths` - Array of all critical paths (equal duration)
- `path_id` - Unique identifier for each path (1, 2, 3...)
- `is_primary` - True for first path, false for alternates
- `sequence` - Position in critical path (1, 2, 3... per path)

## Command Line Options

```
usage: xereader.py [-h] [-o OUTPUT_DIR] [-v] [-q] [--validate-only] [--version] input_file

positional arguments:
  input_file            Path to input XER file

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                        Output directory (default: current directory)
  -v, --verbose         Enable verbose output
  -q, --quiet           Suppress all output except errors
  --validate-only       Validate XER file without generating output
  --version             show program's version number and exit
```

## Examples

### Parse and View Results

```bash
# Parse XER file
python xereader.py project.xer --verbose

# View activities
cat activities.json | python -m json.tool | less

# View critical path
cat critical_path.json | python -m json.tool | less
```

### Batch Processing

```bash
# Process multiple XER files
for file in *.xer; do
    python xereader.py "$file" --output-dir "output/$(basename $file .xer)"
done
```

### Integration with Other Tools

```python
import json

# Load activities
with open('activities.json', 'r') as f:
    data = json.load(f)

activities = data['activities']
print(f"Total activities: {len(activities)}")

# Find delayed activities
delayed = [a for a in activities
           if a['actual_start_date'] and a['planned_start_date']
           and a['actual_start_date'] > a['planned_start_date']]
print(f"Delayed activities: {len(delayed)}")

# Load critical path
with open('critical_path.json', 'r') as f:
    cp_data = json.load(f)

print(f"Project duration: {cp_data['summary']['total_duration_days']} days")
print(f"Critical activities: {cp_data['summary']['total_activities_on_critical_paths']}")
```

## Project Structure

```
XEReader/
├── xereader.py              # Main entry point
├── requirements.txt         # Dependencies
├── README.md               # This file
├── CLAUDE.md               # Development guide
├── src/                    # Source code
│   ├── parser/            # XER file parsing
│   │   ├── xer_parser.py
│   │   └── table_extractor.py
│   ├── models/            # Data models
│   │   ├── activity.py
│   │   ├── dependency.py
│   │   └── project.py
│   ├── processors/        # Business logic
│   │   ├── activity_processor.py
│   │   └── critical_path_calculator.py
│   ├── exporters/         # JSON generation
│   │   └── json_exporter.py
│   └── utils/             # Utilities
│       ├── date_utils.py
│       └── validators.py
├── tests/                  # Test suite
│   ├── test_parser.py
│   ├── test_integration.py
│   └── fixtures/
│       └── sample.xer
└── docs/                   # Design documents
    ├── technical_design.md
    ├── design_decisions.md
    ├── activities_json_schema.md
    └── critical_path_json_schema.md
```

## Critical Path Method (CPM)

XEReader implements proper CPM algorithm:

1. **Build Network Graph** - All activities and dependencies
2. **Forward Pass** - Calculate Early Start/Finish dates
3. **Backward Pass** - Calculate Late Start/Finish dates
4. **Calculate Total Float** - LS - ES for each activity
5. **Identify Critical Activities** - Float ≤ 0
6. **Find Longest Path(s)** - The true critical path

**Important:** The critical path is the **longest sequence** of dependent activities, not just all activities with zero float.

## Performance

- **Small projects (<100 activities):** < 0.1 seconds
- **Medium projects (100-1000 activities):** < 0.5 seconds
- **Large projects (1000-5000 activities):** < 1 second
- **Very large projects (5000+ activities):** 1-3 seconds

Tested with real-world P6 projects containing 3000+ activities.

## Dependencies

### Required
- **Python 3.10+**
- **networkx** - Graph algorithms for CPM
- **python-dateutil** - Date parsing

### Development
- **pytest** - Testing framework
- **pytest-cov** - Coverage reporting

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test
pytest tests/test_parser.py -v

# Run integration tests
pytest tests/test_integration.py -v
```

## Design Decisions

Key design choices documented in [design_decisions.md](design_decisions.md):

1. **Use `task_code` not `task_id`** - Persistent across exports
2. **Two separate JSON files** - Separation of concerns
3. **Simplified schema** - Only essential fields
4. **Both planned and actual dates** - For delay detection
5. **Bidirectional dependencies** - Both predecessors and successors
6. **Critical path = longest path** - Proper CPM definition
7. **Direct Python execution** - No pip install required

## Troubleshooting

### Missing Required Tables

```
ERROR: Validation failed: Required table 'TASK' not found in XER file
```

**Solution:** Ensure your XER file contains PROJECT, TASK, and TASKPRED tables. Export from P6 with "All Data" option.

### Invalid Date Format

```
ERROR: Unexpected error: time data '...' does not match format
```

**Solution:** XER files should use standard P6 date format. Check file encoding (UTF-8 recommended).

### Circular Dependencies

If the CPM calculation detects circular dependencies, it will process what it can but may not identify a proper critical path.

**Solution:** Fix circular dependencies in Primavera P6 before exporting.

## Future Enhancements

Potential features for future versions:

- WBS hierarchy support
- Calendar integration (working vs non-working days)
- Resource assignments
- Multiple baseline comparison
- Visualization/diagrams
- Web interface
- Database output

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Oracle Primavera P6 documentation
- NetworkX library for graph algorithms
- The scheduling and project management community

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Refer to design documents in `docs/` folder
- See [CLAUDE.md](CLAUDE.md) for development guide

---

**Version:** 1.0.0
**Last Updated:** 2026-01-20
**Author:** XEReader Development Team
