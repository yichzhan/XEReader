#!/usr/bin/env python3
"""
XEReader - Primavera P6 XER File Parser

Parses XER files and generates separate output files per project:
- {xer_filename}_{project_code}_activities.json/md: All activities with dates and dependencies
- {xer_filename}_{project_code}_critical_path.json/md: Critical path sequence(s)

Usage:
    python xereader.py input.xer
    python xereader.py input.xer --output-dir ./output
    python xereader.py input.xer --verbose
"""

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.parser.xer_parser import XERParser
from src.processors.activity_processor import ActivityProcessor
from src.processors.critical_path_calculator import CriticalPathCalculator, CycleInfo
from src.exporters.json_exporter import JSONExporter
from src.exporters.markdown_exporter import MarkdownExporter
from src.utils.validators import validate_required_tables, validate_activities, ValidationError


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='XEReader - Parse Primavera P6 XER files to JSON/Markdown',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python xereader.py project.xer
  python xereader.py project.xer --output-dir ./output
  python xereader.py project.xer --format both --verbose

Output (per project in the XER file):
  {xer_filename}_{project_code}_activities.json/md   - All activities with dependencies
  {xer_filename}_{project_code}_critical_path.json/md - Critical path sequence(s)
        """
    )

    parser.add_argument(
        'input_file',
        help='Path to input XER file'
    )

    parser.add_argument(
        '-o', '--output-dir',
        default='.',
        help='Output directory (default: current directory)'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Suppress all output except errors'
    )

    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Validate XER file without generating output'
    )

    parser.add_argument(
        '--format',
        choices=['json', 'markdown', 'both'],
        default='json',
        help='Output format (default: json)'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='XEReader 2.0.0'
    )

    return parser.parse_args()


def log(message: str, verbose: bool = True, quiet: bool = False):
    """Print message if not quiet mode"""
    if not quiet and verbose:
        print(message)


def log_error(message: str):
    """Print error message to stderr"""
    print(f"ERROR: {message}", file=sys.stderr)


def log_warning(message: str):
    """Print warning message to stderr"""
    print(f"WARNING: {message}", file=sys.stderr)


def write_cycles_log(log_path: Path, cycles: List, project_code: str) -> None:
    """
    Write cycles report to log file.

    Args:
        log_path: Path to the log file
        cycles: List of CycleInfo objects
        project_code: Project code for the header
    """
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write(f"CIRCULAR DEPENDENCIES REPORT - {project_code}\n")
        f.write("=" * 60 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total cycles found: {len(cycles)}\n")
        f.write("\n")
        f.write("NOTE: Circular dependencies prevent Critical Path Method (CPM)\n")
        f.write("calculation. The activities file can still be exported,\n")
        f.write("but critical_path file will not be generated.\n")
        f.write("\n")

        # Sort by length (shortest first)
        sorted_cycles = sorted(cycles, key=lambda c: c.length)

        for cycle in sorted_cycles:
            f.write("-" * 60 + "\n")
            f.write(f"## Cycle {cycle.cycle_id} (Length: {cycle.length} activities)\n")
            f.write("-" * 60 + "\n\n")

            f.write("Path:\n")
            for i, (code, name) in enumerate(zip(cycle.task_codes, cycle.task_names)):
                name_display = name[:50] + '...' if len(name) > 50 else name
                f.write(f"  {i+1}. [{code}]\n")
                f.write(f"     {name_display}\n")
                if i < len(cycle.task_codes) - 1:
                    f.write(f"     |\n")
                    f.write(f"     v\n")
                else:
                    f.write(f"     |\n")
                    f.write(f"     +---> (back to [{cycle.task_codes[0]}])\n")
            f.write("\n")


def process_single_project(project_info, activities, output_dir, base_filename, args, output_files):
    """
    Process a single project and generate output files.

    Args:
        project_info: ProjectInfo object
        activities: List of Activity objects for this project
        output_dir: Output directory Path
        base_filename: Base filename from input XER
        args: Command line arguments
        output_files: List to append output file info to

    Returns:
        True if successful, False if validation failed
    """
    project_code = project_info.project_code

    log(f"\n--- Processing project: {project_info.project_name} ({project_code}) ---",
        args.verbose, args.quiet)
    log(f"  Activities: {len(activities)}", args.verbose, args.quiet)

    # Count dependencies
    total_deps = sum(len(a.predecessors) for a in activities)
    log(f"  Dependencies: {total_deps}", args.verbose, args.quiet)

    # Validate activities for this project
    try:
        validate_activities(activities)
    except ValidationError as e:
        log_warning(f"Project {project_code}: {e}")
        return False

    if args.validate_only:
        log(f"  ✓ Validation passed", args.verbose, args.quiet)
        return True

    # Build graph and check for cycles
    cpm_calculator = CriticalPathCalculator(activities)
    cpm_calculator.build_graph_only()

    cycles_detected = []
    critical_paths = []
    project_duration = 0.0

    if cpm_calculator.has_cycles():
        # Detect and report cycles
        cycles_detected = cpm_calculator.detect_cycles()
        log_warning(f"Project {project_code}: Found {len(cycles_detected)} circular dependencies")

        # Write cycles log file
        cycles_log_path = output_dir / f'{base_filename}_{project_code}_cycles.log'
        write_cycles_log(cycles_log_path, cycles_detected, project_code)
        log(f"  ✓ Generated {cycles_log_path.name}", args.verbose, args.quiet)
    else:
        # Calculate critical path (no cycles)
        critical_paths, project_duration = cpm_calculator.calculate()

        if critical_paths:
            total_critical_activities = len(critical_paths[0]) if critical_paths else 0
            log(
                f"  ✓ Critical path: {total_critical_activities} activities, "
                f"{project_duration / 8:.1f} days",
                args.verbose,
                args.quiet
            )
        else:
            log(f"  ⚠ No critical path found", args.verbose, args.quiet)

    # Export JSON files
    if args.format in ['json', 'both']:
        activities_json_path = output_dir / f'{base_filename}_{project_code}_activities.json'

        json_exporter = JSONExporter(project_info, activities)
        json_exporter.export_activities(str(activities_json_path))
        log(f"  ✓ Generated {activities_json_path.name}", args.verbose, args.quiet)
        output_files.append((activities_json_path, JSONExporter.get_file_size(str(activities_json_path))))

        # Only export critical path if no cycles
        if not cycles_detected:
            critical_path_json_path = output_dir / f'{base_filename}_{project_code}_critical_path.json'
            json_exporter.export_critical_path(
                str(critical_path_json_path),
                critical_paths,
                project_duration
            )
            log(f"  ✓ Generated {critical_path_json_path.name}", args.verbose, args.quiet)
            output_files.append((critical_path_json_path, JSONExporter.get_file_size(str(critical_path_json_path))))

    # Export Markdown files
    if args.format in ['markdown', 'both']:
        activities_md_path = output_dir / f'{base_filename}_{project_code}_activities.md'

        md_exporter = MarkdownExporter(project_info, activities)
        md_exporter.export_activities(str(activities_md_path))
        log(f"  ✓ Generated {activities_md_path.name}", args.verbose, args.quiet)
        output_files.append((activities_md_path, JSONExporter.get_file_size(str(activities_md_path))))

        # Only export critical path if no cycles
        if not cycles_detected:
            critical_path_md_path = output_dir / f'{base_filename}_{project_code}_critical_path.md'
            md_exporter.export_critical_path(
                str(critical_path_md_path),
                critical_paths,
                project_duration
            )
            log(f"  ✓ Generated {critical_path_md_path.name}", args.verbose, args.quiet)
            output_files.append((critical_path_md_path, JSONExporter.get_file_size(str(critical_path_md_path))))

    return True


def main():
    """Main entry point"""
    args = parse_arguments()
    start_time = time.time()

    try:
        # Print header
        if not args.quiet:
            print("XEReader v2.0 - Primavera P6 XER File Parser")
            print()

        # Validate input file
        input_path = Path(args.input_file)
        if not input_path.exists():
            log_error(f"Input file not found: {args.input_file}")
            return 1

        log(f"Reading XER file: {args.input_file}", args.verbose, args.quiet)

        # Parse XER file
        parser = XERParser(str(input_path))
        tables = parser.parse()

        log(f"✓ Parsed {len(tables)} tables", args.verbose, args.quiet)

        # Validate required tables
        required_tables = ['PROJECT', 'TASK', 'TASKPRED']
        validate_required_tables(parser, required_tables)

        # Process all projects
        activity_processor = ActivityProcessor()
        projects = activity_processor.process_all_projects(parser.get_table('PROJECT'))

        log(f"✓ Found {len(projects)} project(s)", args.verbose, args.quiet)
        for proj in projects:
            log(f"  - {proj.project_name} ({proj.project_code})", args.verbose, args.quiet)

        # Process all activities
        all_activities = activity_processor.process_activities(parser.get_table('TASK'))
        log(f"✓ Found {len(all_activities)} total activities", args.verbose, args.quiet)

        # Process UDF values (notes) if available
        if parser.has_table('UDFVALUE'):
            notes_count = activity_processor.process_udf_values(parser.get_table('UDFVALUE'))
            if notes_count > 0:
                log(f"✓ Attached {notes_count} notes to activities", args.verbose, args.quiet)

        # Process dependencies (only within-project)
        activity_processor.process_dependencies(parser.get_table('TASKPRED'))

        # Count total dependencies
        total_deps = sum(len(a.predecessors) for a in all_activities)
        log(f"✓ Built dependency graph ({total_deps} within-project relationships)", args.verbose, args.quiet)

        if args.validate_only:
            # Validate all activities
            for proj in projects:
                proj_activities = activity_processor.get_activities_for_project(proj.project_id)
                try:
                    validate_activities(proj_activities)
                    log(f"✓ Project {proj.project_code}: Validation passed", args.verbose, args.quiet)
                except ValidationError as e:
                    log_warning(f"Project {proj.project_code}: {e}")
            return 0

        # Prepare output directory
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        base_filename = input_path.stem

        output_files = []

        # Process each project
        for proj in projects:
            proj_activities = activity_processor.get_activities_for_project(proj.project_id)

            if not proj_activities:
                log_warning(f"Project {proj.project_code}: No activities found, skipping")
                continue

            process_single_project(
                proj, proj_activities, output_dir, base_filename, args, output_files
            )

        # Print output summary
        if not args.quiet and output_files:
            print()
            print("Output files:")
            for file_path, file_size in output_files:
                print(f"  - {file_path} ({file_size})")
            print()

        elapsed = time.time() - start_time
        log(f"Done in {elapsed:.1f} seconds.", args.verbose, args.quiet)

        return 0

    except ValidationError as e:
        log_error(f"Validation failed: {e}")
        return 1

    except FileNotFoundError as e:
        log_error(str(e))
        return 1

    except KeyError as e:
        log_error(f"Missing required table or field: {e}")
        return 1

    except Exception as e:
        log_error(f"Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
