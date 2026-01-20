#!/usr/bin/env python3
"""
Critical Path Visualizer

Generates a visual diagram from critical_path.json showing:
- Task boxes with code and name
- Sequential connections with arrows
- Multiple critical paths (if present)

Usage:
    python visualize_critical_path.py critical_path.json
    python visualize_critical_path.py critical_path.json --output diagram.png
    python visualize_critical_path.py critical_path.json --path-id 1
"""

import argparse
import json
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import textwrap


def load_critical_path_json(file_path: str) -> dict:
    """Load critical path JSON file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def wrap_text(text: str, width: int = 30) -> str:
    """Wrap long text to fit in boxes"""
    return '\n'.join(textwrap.wrap(text, width=width))


def draw_critical_path_diagram(
    data: dict,
    output_path: str,
    path_id: int = None,
    figsize_width: int = 20,
    box_width: float = 3.5,
    box_height: float = 1.2,
    vertical_spacing: float = 1.8,
    horizontal_spacing: float = 4.5
):
    """
    Draw critical path diagram with task boxes and arrows

    Args:
        data: Critical path JSON data
        output_path: Output image file path
        path_id: Specific path ID to visualize (None = all paths)
        figsize_width: Figure width
        box_width: Width of task boxes
        box_height: Height of task boxes
        vertical_spacing: Vertical space between tasks
        horizontal_spacing: Horizontal space between parallel paths
    """
    project = data['project']
    summary = data['summary']
    critical_paths = data['critical_paths']

    # Filter to specific path if requested
    if path_id is not None:
        critical_paths = [p for p in critical_paths if p['path_id'] == path_id]
        if not critical_paths:
            raise ValueError(f"Path ID {path_id} not found")

    # Calculate figure dimensions
    max_activities = max(p['activity_count'] for p in critical_paths)
    num_paths = len(critical_paths)

    figsize_height = max(12, max_activities * vertical_spacing + 3)
    fig_width = max(figsize_width, num_paths * horizontal_spacing + 2)

    fig, ax = plt.subplots(figsize=(fig_width, figsize_height))
    ax.set_xlim(0, fig_width)
    ax.set_ylim(0, figsize_height)
    ax.axis('off')

    # Title
    title = f"{project['project_name'] or project['project_code']}\nCritical Path Diagram"
    if path_id:
        title += f" - Path {path_id}"
    plt.title(title, fontsize=16, fontweight='bold', pad=20)

    # Summary text
    summary_text = (
        f"Duration: {summary['total_duration_days']:.1f} days "
        f"({summary['total_duration_hours']:.0f} hours)\n"
        f"Critical Paths: {summary['critical_path_count']} | "
        f"Total Activities on Critical Paths: {summary['total_activities_on_critical_paths']}"
    )
    ax.text(
        fig_width / 2, figsize_height - 1.5,
        summary_text,
        ha='center', va='top',
        fontsize=10,
        bbox=dict(boxstyle='round,pad=0.5', facecolor='lightblue', alpha=0.3)
    )

    # Color scheme
    colors = {
        'primary': '#4CAF50',      # Green
        'alternate': '#FF9800',    # Orange
        'box_edge': '#333333',     # Dark gray
        'arrow': '#666666',        # Gray
        'text': '#000000'          # Black
    }

    # Draw each critical path
    for path_idx, path in enumerate(critical_paths):
        activities = path['activities']
        is_primary = path['is_primary']

        # Determine box color
        box_color = colors['primary'] if is_primary else colors['alternate']

        # Calculate x position for this path (center multiple paths)
        if num_paths == 1:
            x_base = fig_width / 2
        else:
            x_base = (path_idx + 1) * fig_width / (num_paths + 1)

        # Path header
        path_label = f"Path {path['path_id']}" + (" (Primary)" if is_primary else "")
        path_info = f"{path['activity_count']} activities | {path['duration_days']:.1f} days"

        ax.text(
            x_base, figsize_height - 3,
            f"{path_label}\n{path_info}",
            ha='center', va='top',
            fontsize=9, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor=box_color, alpha=0.3)
        )

        # Draw activities and arrows
        y_start = figsize_height - 4.5

        for i, activity in enumerate(activities):
            y_pos = y_start - (i * vertical_spacing)

            # Draw task box
            box = FancyBboxPatch(
                (x_base - box_width / 2, y_pos - box_height / 2),
                box_width, box_height,
                boxstyle="round,pad=0.1",
                linewidth=2,
                edgecolor=colors['box_edge'],
                facecolor=box_color,
                alpha=0.7
            )
            ax.add_patch(box)

            # Task code (bold)
            ax.text(
                x_base, y_pos + 0.25,
                activity['task_code'],
                ha='center', va='center',
                fontsize=9, fontweight='bold',
                color=colors['text']
            )

            # Task name (wrapped)
            task_name = wrap_text(activity['task_name'], width=35)
            ax.text(
                x_base, y_pos - 0.15,
                task_name,
                ha='center', va='center',
                fontsize=7,
                color=colors['text']
            )

            # Sequence number (small, in corner)
            ax.text(
                x_base - box_width / 2 + 0.15, y_pos + box_height / 2 - 0.15,
                str(activity['sequence']),
                ha='left', va='top',
                fontsize=8,
                color='white',
                fontweight='bold',
                bbox=dict(boxstyle='circle,pad=0.1', facecolor=colors['box_edge'])
            )

            # Draw arrow to next task
            if i < len(activities) - 1:
                arrow = FancyArrowPatch(
                    (x_base, y_pos - box_height / 2 - 0.05),
                    (x_base, y_pos - vertical_spacing + box_height / 2 + 0.05),
                    arrowstyle='->,head_width=0.4,head_length=0.6',
                    linewidth=2,
                    color=colors['arrow'],
                    zorder=1
                )
                ax.add_patch(arrow)

    # Legend
    legend_elements = [
        mpatches.Patch(facecolor=colors['primary'], alpha=0.7, label='Primary Path'),
        mpatches.Patch(facecolor=colors['alternate'], alpha=0.7, label='Alternate Path')
    ]
    ax.legend(
        handles=legend_elements,
        loc='lower right',
        fontsize=9
    )

    # Footer
    ax.text(
        fig_width / 2, 0.3,
        f"Generated by XEReader | Project: {project['project_code']}",
        ha='center', va='bottom',
        fontsize=8,
        style='italic',
        color='gray'
    )

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✓ Diagram saved to: {output_path}")

    return output_path


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Generate critical path diagram from JSON',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python visualize_critical_path.py critical_path.json
  python visualize_critical_path.py critical_path.json --output diagram.png
  python visualize_critical_path.py critical_path.json --path-id 1
  python visualize_critical_path.py critical_path.json --width 30 --height 1.5

Output:
  PNG image file with critical path diagram
        """
    )

    parser.add_argument(
        'json_file',
        help='Path to critical_path.json file'
    )

    parser.add_argument(
        '-o', '--output',
        help='Output image file path (default: based on input filename)'
    )

    parser.add_argument(
        '--path-id',
        type=int,
        help='Visualize only specific path ID (default: all paths)'
    )

    parser.add_argument(
        '--figsize-width',
        type=int,
        default=20,
        help='Figure width (default: 20)'
    )

    parser.add_argument(
        '--box-width',
        type=float,
        default=3.5,
        help='Task box width (default: 3.5)'
    )

    parser.add_argument(
        '--box-height',
        type=float,
        default=1.2,
        help='Task box height (default: 1.2)'
    )

    parser.add_argument(
        '--vertical-spacing',
        type=float,
        default=1.8,
        help='Vertical spacing between tasks (default: 1.8)'
    )

    parser.add_argument(
        '--horizontal-spacing',
        type=float,
        default=4.5,
        help='Horizontal spacing between paths (default: 4.5)'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='Critical Path Visualizer 1.0.0'
    )

    return parser.parse_args()


def main():
    """Main entry point"""
    args = parse_arguments()

    try:
        # Validate input file
        input_path = Path(args.json_file)
        if not input_path.exists():
            print(f"ERROR: Input file not found: {args.json_file}", file=sys.stderr)
            return 1

        if not input_path.suffix == '.json':
            print(f"ERROR: Input file must be a JSON file", file=sys.stderr)
            return 1

        # Determine output path
        if args.output:
            output_path = args.output
        else:
            # Default: replace .json with .png
            output_path = input_path.with_suffix('.png')

        print(f"Loading critical path data from: {input_path}")

        # Load JSON data
        data = load_critical_path_json(str(input_path))

        # Validate data structure
        if 'critical_paths' not in data or not data['critical_paths']:
            print("ERROR: No critical paths found in JSON file", file=sys.stderr)
            return 1

        num_paths = len(data['critical_paths'])
        total_activities = sum(p['activity_count'] for p in data['critical_paths'])

        print(f"Found {num_paths} critical path(s) with {total_activities} total activities")

        if args.path_id:
            print(f"Visualizing path {args.path_id} only")

        # Generate diagram
        print("Generating diagram...")
        draw_critical_path_diagram(
            data,
            str(output_path),
            path_id=args.path_id,
            figsize_width=args.figsize_width,
            box_width=args.box_width,
            box_height=args.box_height,
            vertical_spacing=args.vertical_spacing,
            horizontal_spacing=args.horizontal_spacing
        )

        print(f"Done! Open {output_path} to view the diagram.")

        return 0

    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON file: {e}", file=sys.stderr)
        return 1

    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    except Exception as e:
        print(f"ERROR: Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
