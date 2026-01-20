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
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.parser.xer_parser import XERParser
from src.processors.activity_processor import ActivityProcessor
from src.processors.critical_path_calculator import CriticalPathCalculator
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

        # Process dependencies
        activity_processor.process_dependencies(parser.get_table('TASKPRED'))

        # Count total dependencies
        total_deps = sum(len(a.predecessors) for a in activities)
        log(f"✓ Built dependency graph ({total_deps} relationships)", args.verbose, args.quiet)

        # Validate activities
        validate_activities(activities)

        if args.validate_only:
            log("✓ Validation passed", args.verbose, args.quiet)
            return 0

        # Calculate critical path
        cpm_calculator = CriticalPathCalculator(activities)
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

        # Export files based on format
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Use original XER filename (without .xer extension) for output files
        base_filename = input_path.stem  # Gets filename without extension

        output_files = []

        # Export JSON files
        if args.format in ['json', 'both']:
            activities_json_path = output_dir / f'{base_filename}_activities.json'
            critical_path_json_path = output_dir / f'{base_filename}_critical_path.json'

            json_exporter = JSONExporter(project_info, activities)
            json_exporter.export_activities(str(activities_json_path))
            log(f"✓ Generated {activities_json_path.name}", args.verbose, args.quiet)

            json_exporter.export_critical_path(
                str(critical_path_json_path),
                critical_paths,
                project_duration
            )
            log(f"✓ Generated {critical_path_json_path.name}", args.verbose, args.quiet)

            output_files.append((activities_json_path, JSONExporter.get_file_size(str(activities_json_path))))
            output_files.append((critical_path_json_path, JSONExporter.get_file_size(str(critical_path_json_path))))

        # Export Markdown files
        if args.format in ['markdown', 'both']:
            activities_md_path = output_dir / f'{base_filename}_activities.md'
            critical_path_md_path = output_dir / f'{base_filename}_critical_path.md'

            md_exporter = MarkdownExporter(project_info, activities)
            md_exporter.export_activities(str(activities_md_path))
            log(f"✓ Generated {activities_md_path.name}", args.verbose, args.quiet)

            md_exporter.export_critical_path(
                str(critical_path_md_path),
                critical_paths,
                project_duration
            )
            log(f"✓ Generated {critical_path_md_path.name}", args.verbose, args.quiet)

            output_files.append((activities_md_path, JSONExporter.get_file_size(str(activities_md_path))))
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
