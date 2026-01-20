# XEReader Complete Workflow Guide

This guide shows the complete workflow from XER file to visual diagram.

## Quick Start Workflow

### Step 1: Parse XER File

```bash
python xereader.py Cracker_Schedule_Baseline.xer --verbose
```

**Output:**
- `Cracker_Schedule_Baseline_activities.json` (3.4 MB)
- `Cracker_Schedule_Baseline_critical_path.json` (32 KB)

### Step 2: Generate Visual Diagram

```bash
python visualize_critical_path.py Cracker_Schedule_Baseline_critical_path.json
```

**Output:**
- `Cracker_Schedule_Baseline_critical_path.png` (high-quality diagram)

### Step 3: View and Analyze

- Open the PNG file to view the critical path diagram
- Review the JSON files for detailed data
- Use the activities JSON for analysis and reporting

## Complete Example

```bash
# 1. Parse XER file
python xereader.py project.xer --verbose

# Output example:
# XEReader v1.0 - Primavera P6 XER File Parser
#
# Reading XER file: project.xer
# ✓ Parsed 15 tables
#   Project:  (PROJECT_CODE)
# ✓ Found 3088 activities
# ✓ Built dependency graph (8492 relationships)
# ✓ Calculated critical path (56 activities, 12513.9 days)
# ✓ Generated project_activities.json
# ✓ Generated project_critical_path.json
#
# Output files:
#   - project_activities.json (3.4 MB)
#   - project_critical_path.json (32.0 KB)
#
# Done in 0.3 seconds.

# 2. Generate diagram for all critical paths
python visualize_critical_path.py project_critical_path.json

# Output:
# Loading critical path data from: project_critical_path.json
# Found 2 critical path(s) with 113 total activities
# Generating diagram...
# ✓ Diagram saved to: project_critical_path.png
# Done! Open project_critical_path.png to view the diagram.

# 3. Generate diagram for specific path only
python visualize_critical_path.py project_critical_path.json --path-id 1 --output path1.png
```

## Advanced Usage

### Parse Multiple XER Files

```bash
# Batch process multiple files
for file in *.xer; do
    echo "Processing $file..."
    python xereader.py "$file" --verbose
done

# Generate diagrams for all
for json in *_critical_path.json; do
    echo "Visualizing $json..."
    python visualize_critical_path.py "$json"
done
```

### Customize Diagram Layout

```bash
# For projects with many activities (adjust vertical spacing)
python visualize_critical_path.py project_critical_path.json \
  --vertical-spacing 2.0 \
  --box-height 1.5

# For projects with long task names (adjust box width)
python visualize_critical_path.py project_critical_path.json \
  --box-width 4.5

# For multiple critical paths (adjust horizontal spacing)
python visualize_critical_path.py project_critical_path.json \
  --horizontal-spacing 5.0
```

### Analyze JSON Data with Python

```python
import json

# Load critical path data
with open('project_critical_path.json', 'r') as f:
    cp_data = json.load(f)

# Print summary
summary = cp_data['summary']
print(f"Project Duration: {summary['total_duration_days']:.1f} days")
print(f"Critical Paths: {summary['critical_path_count']}")
print(f"Critical Activities: {summary['total_activities_on_critical_paths']}")

# Get primary critical path
primary_path = [p for p in cp_data['critical_paths'] if p['is_primary']][0]
print(f"\nPrimary Path: {primary_path['activity_count']} activities")

# List activities on primary path
for activity in primary_path['activities']:
    print(f"  {activity['sequence']:2d}. {activity['task_code']} - {activity['task_name']}")
```

## Typical Use Cases

### Use Case 1: Schedule Review

```bash
# Parse schedule
python xereader.py schedule.xer

# Generate diagram
python visualize_critical_path.py schedule_critical_path.json

# Review:
# 1. Open PNG to see critical path visually
# 2. Check activities.json for detailed data
# 3. Identify bottlenecks and long-duration tasks
```

### Use Case 2: Schedule Comparison

```bash
# Parse baseline and current schedule
python xereader.py baseline.xer --output-dir baseline_output
python xereader.py current.xer --output-dir current_output

# Generate diagrams
python visualize_critical_path.py baseline_output/baseline_critical_path.json
python visualize_critical_path.py current_output/current_critical_path.json

# Compare:
# 1. Compare diagrams visually
# 2. Compare JSON files for specific changes
# 3. Identify schedule slippage or improvements
```

### Use Case 3: Reporting

```bash
# Parse XER
python xereader.py project.xer

# Generate diagram with custom output name
python visualize_critical_path.py project_critical_path.json \
  --output "Weekly_Report_Critical_Path_$(date +%Y%m%d).png"

# Include diagram in reports/presentations
```

## Troubleshooting

### Large Diagrams

For projects with 50+ activities on critical path:

```bash
# Increase vertical spacing to prevent overlap
python visualize_critical_path.py project_critical_path.json \
  --vertical-spacing 2.5 \
  --box-height 1.5

# Or visualize only one path at a time
python visualize_critical_path.py project_critical_path.json --path-id 1
```

### Long Task Names

If task names are truncated:

```bash
# Increase box width
python visualize_critical_path.py project_critical_path.json --box-width 5.0
```

### Multiple Critical Paths

For better readability with multiple paths:

```bash
# Option 1: Increase horizontal spacing
python visualize_critical_path.py project_critical_path.json --horizontal-spacing 6.0

# Option 2: Generate separate diagrams for each path
python visualize_critical_path.py project_critical_path.json --path-id 1 -o path1.png
python visualize_critical_path.py project_critical_path.json --path-id 2 -o path2.png
```

## File Naming Convention

XEReader follows a consistent naming convention:

**Input:**
- `{filename}.xer` (Primavera XER file)

**Output:**
- `{filename}_activities.json` (all activities with dependencies)
- `{filename}_critical_path.json` (critical path sequences)
- `{filename}_critical_path.png` (visual diagram, default)

**Example:**
```
Input:  Cracker_Schedule_Baseline.xer

Output: Cracker_Schedule_Baseline_activities.json
        Cracker_Schedule_Baseline_critical_path.json
        Cracker_Schedule_Baseline_critical_path.png
```

## Tips and Best Practices

1. **Always use --verbose** for initial runs to see processing details
2. **Validate first** with `--validate-only` before generating outputs
3. **Check file sizes** - Large activities.json files indicate many activities
4. **Review diagrams** visually before detailed JSON analysis
5. **Keep XER files** as source of truth - JSON files are derived data
6. **Version control** your XER files to track schedule changes over time
7. **Document** which XER export represents baseline vs current schedule

## Integration with Other Tools

### Excel Analysis

```python
import json
import pandas as pd

# Load activities
with open('project_activities.json', 'r') as f:
    data = json.load(f)

# Convert to DataFrame
df = pd.DataFrame(data['activities'])

# Export to Excel
df.to_excel('activities_analysis.xlsx', index=False)
```

### PowerPoint Presentations

1. Generate diagram: `python visualize_critical_path.py project_critical_path.json`
2. Insert PNG into PowerPoint slides
3. Add annotations and commentary

### Project Management Reports

Combine JSON data with diagrams for comprehensive reports showing:
- Critical path visualization
- Activity details and dependencies
- Schedule statistics and metrics
- Delay analysis (comparing actual vs planned dates)

---

**Version:** 1.0
**Last Updated:** 2026-01-20
