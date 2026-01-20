# XEReader Implementation Plan

## Overview
Implementation plan for the XEReader Python application that parses Primavera P6 XER files and generates two JSON outputs: activities.json and critical_path.json.

**Execution Model:** Direct Python script (not pip-installable package)

---

## Project Structure

```
XEReader/
├── README.md                    # User documentation
├── CLAUDE.md                    # Developer documentation
├── requirements.txt             # Python dependencies
├── xereader.py                  # Main entry point script
├── src/
│   ├── __init__.py
│   ├── parser/
│   │   ├── __init__.py
│   │   ├── xer_parser.py       # XER file parsing
│   │   └── table_extractor.py  # Extract specific tables
│   ├── models/
│   │   ├── __init__.py
│   │   ├── activity.py         # Activity data class
│   │   ├── dependency.py       # Dependency data class
│   │   └── project.py          # Project info data class
│   ├── processors/
│   │   ├── __init__.py
│   │   ├── activity_processor.py      # Build activity objects
│   │   └── critical_path_calculator.py # CPM calculations
│   ├── exporters/
│   │   ├── __init__.py
│   │   └── json_exporter.py    # JSON file generation
│   └── utils/
│       ├── __init__.py
│       ├── date_utils.py       # Date parsing/formatting
│       └── validators.py       # Data validation
├── tests/
│   ├── __init__.py
│   ├── test_parser.py
│   ├── test_critical_path.py
│   ├── test_json_export.py
│   └── fixtures/
│       └── sample.xer          # Test XER file
├── examples/
│   ├── sample_activities.json
│   └── sample_critical_path.json
└── docs/
    ├── technical_design.md
    ├── design_decisions.md
    ├── activities_json_schema.md
    └── critical_path_json_schema.md
```

---

## Usage

### Installation
```bash
# Clone or download repository
cd XEReader

# Install dependencies
pip install -r requirements.txt
```

### Execution
```bash
# Basic usage
python xereader.py input.xer

# Specify output directory
python xereader.py input.xer --output-dir ./output

# Verbose mode
python xereader.py input.xer --verbose

# Help
python xereader.py --help
```

### Output
```
XEReader/
├── input.xer                    # Input file
├── activities.json              # Generated output 1
└── critical_path.json           # Generated output 2
```

---

## Implementation Phases

### Phase 1: Core Parsing (Foundation)
**Goal:** Parse XER file and extract required tables

**Tasks:**
1. Create XER file reader
   - Read file line by line
   - Identify table sections (%T, %F, %R markers)
   - Handle encoding issues (UTF-8, latin-1, etc.)

2. Create table extractor
   - Extract PROJECT table
   - Extract TASK table
   - Extract TASKPRED table
   - Build dictionary structures for each row

3. Create basic data models
   - `Activity` dataclass with all fields
   - `Dependency` dataclass
   - `ProjectInfo` dataclass

4. Unit tests for parser
   - Test table extraction
   - Test field parsing
   - Test error handling

**Deliverables:**
- `src/parser/xer_parser.py`
- `src/parser/table_extractor.py`
- `src/models/` (all data classes)
- Unit tests

---

### Phase 2: Activity Processing
**Goal:** Convert parsed data into Activity objects with dependencies

**Tasks:**
1. Implement activity processor
   - Map TASK table rows to Activity objects
   - Build `task_id` → `task_code` lookup map
   - Parse and validate dates
   - Handle null/missing values

2. Implement dependency builder
   - Parse TASKPRED table
   - Build predecessors list for each activity
   - Build successors list for each activity
   - Convert `task_id` references to `task_code`

3. Create date utilities
   - Parse XER date formats
   - Convert to Python datetime
   - Format to ISO 8601
   - Handle timezone issues

4. Implement validators
   - Validate required fields
   - Check data integrity (references exist)
   - Validate date ranges
   - Check dependency types

**Deliverables:**
- `src/processors/activity_processor.py`
- `src/utils/date_utils.py`
- `src/utils/validators.py`
- Integration tests

---

### Phase 3: Critical Path Calculation
**Goal:** Implement CPM algorithm to identify critical path(s)

**Tasks:**
1. Build network graph
   - Use NetworkX directed graph
   - Add all activities as nodes
   - Add dependencies as edges with lag

2. Implement forward pass
   - Calculate Early Start (ES) for each activity
   - Calculate Early Finish (EF) for each activity
   - Handle different dependency types (FS, SS, FF, SF)
   - Handle lag values

3. Implement backward pass
   - Calculate Late Finish (LF) for each activity
   - Calculate Late Start (LS) for each activity
   - Handle different dependency types
   - Handle lag values

4. Calculate total float
   - Total Float = LS - ES (or LF - EF)
   - Identify critical activities (float ≤ 0)

5. Find critical path(s)
   - Build critical activities subgraph
   - Find all paths from start to finish
   - Calculate duration for each path
   - Select longest path(s)

6. Sequence and validate
   - Topologically sort critical path activities
   - Assign sequence numbers
   - Validate path continuity
   - Handle multiple critical paths

**Deliverables:**
- `src/processors/critical_path_calculator.py`
- Unit tests for CPM algorithm
- Test cases for multiple critical paths

---

### Phase 4: JSON Export
**Goal:** Generate output JSON files

**Tasks:**
1. Implement activities.json exporter
   - Convert Activity objects to JSON structure
   - Include project information
   - Include all activities with dependencies
   - Use only `task_code` (not `task_id`)
   - Format dates to ISO 8601

2. Implement critical_path.json exporter
   - Extract critical path activities
   - Assign path_id and is_primary flags
   - Assign sequence numbers for each path
   - Calculate summary statistics
   - Format output structure

3. JSON validation
   - Validate schema compliance
   - Check required fields present
   - Verify data integrity
   - Pretty-print formatting

**Deliverables:**
- `src/exporters/json_exporter.py`
- Example output files
- Schema validation tests

---

### Phase 5: CLI and Polish
**Goal:** Create command-line interface and finalize application

**Tasks:**
1. Implement CLI (xereader.py)
   - Argument parsing (argparse)
   - Input file validation
   - Output directory handling
   - Verbose/quiet modes
   - Error messaging
   - Progress reporting

2. Error handling
   - Handle missing files
   - Handle malformed XER files
   - Handle missing required tables
   - Handle invalid data
   - User-friendly error messages

3. Documentation
   - README.md with usage instructions
   - CLAUDE.md for developers
   - Example outputs
   - Troubleshooting guide

4. Testing
   - End-to-end tests
   - Test with real XER files
   - Performance testing
   - Edge case testing

**Deliverables:**
- `xereader.py` (main script)
- Complete documentation
- Test suite
- Example files

---

## Dependencies (requirements.txt)

```
# Core dependencies
networkx>=3.0
python-dateutil>=2.8.0

# Optional (for testing)
pytest>=7.0.0
pytest-cov>=4.0.0
```

**No packaging dependencies needed** (no setup.py, no build tools)

---

## Command-Line Interface Design

### Basic Usage
```bash
python xereader.py <input_file.xer>
```

### Arguments
```
positional arguments:
  input_file            Path to input XER file

optional arguments:
  -h, --help            Show help message and exit
  -o, --output-dir DIR  Output directory (default: current directory)
  -v, --verbose         Enable verbose output
  -q, --quiet           Suppress all output except errors
  --validate-only       Validate XER file without generating output
  --version             Show version number
```

### Output Messages
```
XEReader v1.0 - Primavera P6 XER File Parser

Reading XER file: project.xer
✓ Parsed 3 tables (PROJECT, TASK, TASKPRED)
✓ Found 150 activities
✓ Built dependency graph (245 relationships)
✓ Calculated critical path (25 activities, 180 days)
✓ Generated activities.json
✓ Generated critical_path.json

Output files:
  - activities.json (125 KB)
  - critical_path.json (12 KB)

Done in 2.3 seconds.
```

---

## Data Flow Summary

```
1. Read XER File
   ↓
2. Extract Tables (PROJECT, TASK, TASKPRED)
   ↓
3. Build Activity Objects
   - Map task_id → task_code
   - Parse dates
   - Store task_id temporarily
   ↓
4. Build Dependencies
   - Parse TASKPRED
   - Find predecessors (where task_id = current)
   - Find successors (where pred_task_id = current)
   - Convert task_id → task_code
   ↓
5. Build Network Graph
   - Add all activities as nodes
   - Add dependencies as edges
   ↓
6. CPM Calculation
   - Forward pass (ES, EF)
   - Backward pass (LS, LF)
   - Calculate total float
   ↓
7. Find Critical Path(s)
   - Filter critical activities (float ≤ 0)
   - Find all paths through critical activities
   - Select longest path(s)
   ↓
8. Generate JSON Outputs
   - activities.json (all activities)
   - critical_path.json (critical path sequence)
```

---

## Testing Strategy

### Unit Tests
- XER parser (table extraction)
- Date utilities (parsing, formatting)
- Activity processor (object creation)
- Dependency builder (predecessor/successor)
- CPM calculator (forward/backward pass)
- JSON exporter (schema compliance)

### Integration Tests
- Full XER file parsing
- Activity relationship building
- Critical path calculation accuracy
- JSON output validation

### Test Data
1. **Minimal XER** (5-10 activities)
   - Simple linear sequence
   - Single critical path
   - All dependency types

2. **Medium XER** (50-100 activities)
   - Multiple branches
   - Multiple critical paths
   - Mixed dependency types

3. **Edge Cases**
   - Empty dependencies (start/end activities)
   - Negative float (delayed schedule)
   - Multiple disconnected phases
   - Circular dependencies (should error)

---

## Error Handling

### File Errors
- File not found
- Permission denied
- Invalid file format (not XER)
- Encoding issues

### Data Errors
- Missing required tables
- Missing required fields
- Invalid date formats
- Invalid dependency references
- Circular dependencies

### Processing Errors
- Unable to calculate critical path
- No critical activities found
- Graph traversal failures

### Output Errors
- Unable to write output files
- Permission denied on output directory
- Disk space issues

---

## Performance Considerations

### Expected Performance
- **Small projects** (<100 activities): < 1 second
- **Medium projects** (100-1000 activities): 1-5 seconds
- **Large projects** (1000-10000 activities): 5-30 seconds
- **Very large projects** (>10000 activities): 30-120 seconds

### Optimization Strategies
- Stream XER file reading (don't load entire file)
- Efficient graph algorithms from NetworkX
- Use dictionaries for O(1) lookups
- Minimize memory allocations
- Cache task_id → task_code mapping

---

## Version 1.0 Scope

### In Scope
✅ Parse PROJECT, TASK, TASKPRED tables
✅ Generate activities.json
✅ Generate critical_path.json
✅ Support all 4 dependency types (FS, SS, FF, SF)
✅ Handle lag/lead times
✅ Multiple critical paths support
✅ ISO 8601 date formatting
✅ CLI with basic options
✅ Error handling and validation
✅ Unit and integration tests

### Out of Scope (Future Versions)
❌ WBS hierarchy parsing
❌ Calendar integration
❌ Resource assignments
❌ Activity codes
❌ Constraints parsing
❌ Multiple baselines
❌ Visualization/diagrams
❌ GUI interface
❌ Database output
❌ Real-time P6 connection

---

## Success Criteria

### Functional Requirements
- ✅ Correctly parse valid XER files
- ✅ Generate valid JSON outputs matching schemas
- ✅ Calculate critical path using proper CPM algorithm
- ✅ Handle multiple critical paths
- ✅ Support all dependency types and lags
- ✅ Provide clear error messages

### Non-Functional Requirements
- ✅ Run directly from command line (no installation)
- ✅ Complete parsing in reasonable time (<30s for 1000 activities)
- ✅ Clear, readable code with comments
- ✅ Comprehensive test coverage (>80%)
- ✅ Complete documentation

---

**Document Version:** 1.0
**Last Updated:** 2026-01-20
**Related Documents:**
- technical_design.md
- design_decisions.md
- activities_json_schema.md
- critical_path_json_schema.md
