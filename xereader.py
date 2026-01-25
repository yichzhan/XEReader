#!/usr/bin/env python3
"""
XEReader - Primavera P6 XER File Parser

Parses XER files and generates two JSON outputs:
- activities.json: All activities with dates and dependencies
- critical_path.json: Critical path sequence(s)

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
        description='XEReader - Parse Primavera P6 XER files to JSON',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python xereader.py project.xer
  python xereader.py project.xer --output-dir ./output
  python xereader.py project.xer --verbose

Output:
  activities.json      - All activities with dependencies
  critical_path.json   - Critical path sequence(s)
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
        '--skip-duplicate-validation',
        action='store_true',
        help='Skip validation for duplicate task codes (for multi-project XER files)'
    )

    parser.add_argument(
        '--deduplicate',
        action='store_true',
        help='Remove duplicate task codes (keeps first, logs discarded to _duplicates.log)'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='XEReader 1.0.0'
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


def write_duplicates_log(log_path: Path, discarded: Dict, activities: List) -> None:
    """
    Write duplicates report to log file.

    Args:
        log_path: Path to the log file
        discarded: Dict mapping task_code to list of DuplicateInfo
        activities: List of kept activities (to get info about kept task)
    """
    from src.processors.activity_processor import DuplicateInfo

    # Build lookup for kept activities
    kept_lookup = {a.task_code: a for a in activities}

    def format_date(dt):
        return dt.strftime('%Y-%m-%d %H:%M') if dt else 'None'

    with open(log_path, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("DUPLICATE TASK CODES REPORT\n")
        f.write("=" * 60 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total duplicate task codes: {len(discarded)}\n")
        total_discarded = sum(len(dups) for dups in discarded.values())
        f.write(f"Total discarded tasks: {total_discarded}\n")
        f.write("\n")

        for task_code, dup_list in sorted(discarded.items()):
            kept = kept_lookup.get(task_code)
            all_identical = all(d.is_identical for d in dup_list)

            status = "IDENTICAL" if all_identical else "DIFFERENT"
            f.write("-" * 60 + "\n")
            f.write(f"## {task_code} ({len(dup_list) + 1} occurrences - {status})\n")
            f.write("-" * 60 + "\n")

            # Show kept task
            if kept:
                f.write(f"\nKEPT: task_id={kept.task_id}\n")
                f.write(f"  task_name:          {kept.task_name}\n")
                f.write(f"  planned_start_date: {format_date(kept.planned_start_date)}\n")
                f.write(f"  planned_end_date:   {format_date(kept.planned_end_date)}\n")
                f.write(f"  actual_start_date:  {format_date(kept.actual_start_date)}\n")
                f.write(f"  actual_end_date:    {format_date(kept.actual_end_date)}\n")

            # Show discarded tasks
            for dup in dup_list:
                f.write(f"\nDISCARDED: task_id={dup.task_id}\n")
                if dup.is_identical:
                    f.write("  (All fields identical to kept task)\n")
                else:
                    # Show all fields, marking differences
                    name_mark = " [DIFFERS]" if 'task_name' in dup.differences else ""
                    f.write(f"  task_name:          {dup.task_name}{name_mark}\n")

                    start_mark = " [DIFFERS]" if 'planned_start_date' in dup.differences else ""
                    f.write(f"  planned_start_date: {format_date(dup.planned_start_date)}{start_mark}\n")

                    end_mark = " [DIFFERS]" if 'planned_end_date' in dup.differences else ""
                    f.write(f"  planned_end_date:   {format_date(dup.planned_end_date)}{end_mark}\n")

                    act_start_mark = " [DIFFERS]" if 'actual_start_date' in dup.differences else ""
                    f.write(f"  actual_start_date:  {format_date(dup.actual_start_date)}{act_start_mark}\n")

                    act_end_mark = " [DIFFERS]" if 'actual_end_date' in dup.differences else ""
                    f.write(f"  actual_end_date:    {format_date(dup.actual_end_date)}{act_end_mark}\n")

            f.write("\n")


def write_cycles_log(log_path: Path, cycles: List) -> None:
    """
    Write cycles report to log file.

    Args:
        log_path: Path to the log file
        cycles: List of CycleInfo objects
    """
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("CIRCULAR DEPENDENCIES REPORT\n")
        f.write("=" * 60 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total cycles found: {len(cycles)}\n")
        f.write("\n")
        f.write("NOTE: Circular dependencies prevent Critical Path Method (CPM)\n")
        f.write("calculation. The activities.json file can still be exported,\n")
        f.write("but critical_path.json will not be generated.\n")
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


def main():
    """Main entry point"""
    args = parse_arguments()
    start_time = time.time()

    try:
        # Print header
        if not args.quiet:
            print("XEReader v1.0 - Primavera P6 XER File Parser")
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

        # Process project information
        activity_processor = ActivityProcessor()
        project_info = activity_processor.process_project(parser.get_table('PROJECT'))

        log(f"  Project: {project_info.project_name} ({project_info.project_code})", args.verbose, args.quiet)

        # Process activities
        activities = activity_processor.process_activities(parser.get_table('TASK'))
        log(f"✓ Found {len(activities)} activities", args.verbose, args.quiet)

        # Deduplicate if requested
        discarded_duplicates = {}
        if args.deduplicate:
            original_count = len(activities)
            activities, discarded_duplicates = activity_processor.deduplicate_activities()
            if discarded_duplicates:
                removed_count = original_count - len(activities)
                log_warning(f"Removed {removed_count} duplicate tasks ({len(discarded_duplicates)} unique codes)")
                log(f"✓ Deduplicated to {len(activities)} activities", args.verbose, args.quiet)

                # Write duplicates log immediately (before other processing that might fail)
                output_dir = Path(args.output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
                base_filename = input_path.stem
                duplicates_log_path = output_dir / f'{base_filename}_duplicates.log'
                write_duplicates_log(duplicates_log_path, discarded_duplicates, activities)
                log(f"✓ Generated {duplicates_log_path.name}", args.verbose, args.quiet)

        # Process dependencies
        activity_processor.process_dependencies(parser.get_table('TASKPRED'))

        # Count total dependencies
        total_deps = sum(len(a.predecessors) for a in activities)
        log(f"✓ Built dependency graph ({total_deps} relationships)", args.verbose, args.quiet)

        # Validate activities
        warnings = validate_activities(activities, strict=not args.skip_duplicate_validation)
        for warning in warnings:
            log_warning(warning)

        if args.validate_only:
            log("✓ Validation passed", args.verbose, args.quiet)
            return 0

        # Prepare output directory
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        base_filename = input_path.stem

        # Build graph and check for cycles
        cpm_calculator = CriticalPathCalculator(activities)
        cpm_calculator.build_graph_only()

        cycles_detected = []
        critical_paths = []
        project_duration = 0.0

        if cpm_calculator.has_cycles():
            # Detect and report cycles
            cycles_detected = cpm_calculator.detect_cycles()
            log_warning(f"Found {len(cycles_detected)} circular dependencies - skipping critical path calculation")

            # Write cycles log file
            cycles_log_path = output_dir / f'{base_filename}_cycles.log'
            write_cycles_log(cycles_log_path, cycles_detected)
            log(f"✓ Generated {cycles_log_path.name}", args.verbose, args.quiet)
        else:
            # Calculate critical path (no cycles)
            critical_paths, project_duration = cpm_calculator.calculate()

            if critical_paths:
                total_critical_activities = len(critical_paths[0]) if critical_paths else 0
                log(
                    f"✓ Calculated critical path ({total_critical_activities} activities, "
                    f"{project_duration / 8:.1f} days)",
                    args.verbose,
                    args.quiet
                )
            else:
                log("⚠ Warning: No critical path found", args.verbose, args.quiet)

        output_files = []

        # Export JSON files
        if args.format in ['json', 'both']:
            activities_json_path = output_dir / f'{base_filename}_activities.json'

            json_exporter = JSONExporter(project_info, activities)
            json_exporter.export_activities(str(activities_json_path))
            log(f"✓ Generated {activities_json_path.name}", args.verbose, args.quiet)
            output_files.append((activities_json_path, JSONExporter.get_file_size(str(activities_json_path))))

            # Only export critical path if no cycles
            if not cycles_detected:
                critical_path_json_path = output_dir / f'{base_filename}_critical_path.json'
                json_exporter.export_critical_path(
                    str(critical_path_json_path),
                    critical_paths,
                    project_duration
                )
                log(f"✓ Generated {critical_path_json_path.name}", args.verbose, args.quiet)
                output_files.append((critical_path_json_path, JSONExporter.get_file_size(str(critical_path_json_path))))

        # Export Markdown files
        if args.format in ['markdown', 'both']:
            activities_md_path = output_dir / f'{base_filename}_activities.md'

            md_exporter = MarkdownExporter(project_info, activities)
            md_exporter.export_activities(str(activities_md_path))
            log(f"✓ Generated {activities_md_path.name}", args.verbose, args.quiet)
            output_files.append((activities_md_path, JSONExporter.get_file_size(str(activities_md_path))))

            # Only export critical path if no cycles
            if not cycles_detected:
                critical_path_md_path = output_dir / f'{base_filename}_critical_path.md'
                md_exporter.export_critical_path(
                    str(critical_path_md_path),
                    critical_paths,
                    project_duration
                )
                log(f"✓ Generated {critical_path_md_path.name}", args.verbose, args.quiet)
                output_files.append((critical_path_md_path, JSONExporter.get_file_size(str(critical_path_md_path))))

        # Print output summary
        if not args.quiet:
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
