#!/usr/bin/env python3
"""
Critical Path Visualizer

Generates a visual diagram from critical_path.json showing:
- Task boxes with code and name (horizontal layout)
- Sequential connections with arrows
- Multiple critical paths (if present)
- Maximum 20 boxes per line with automatic wrapping

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


def wrap_text(text: str, width: int = 20) -> str:
    """Wrap long text to fit in boxes"""
    return '\n'.join(textwrap.wrap(text, width=width))


def draw_critical_path_diagram(
    data: dict,
    output_path: str,
    path_id: int = None,
    boxes_per_row: int = 20,
    box_width: float = 2.8,
    box_height: float = 1.0,
    horizontal_spacing: float = 3.2,
    vertical_spacing: float = 1.6
):
    """
    Draw critical path diagram with horizontal layout

    Args:
        data: Critical path JSON data
        output_path: Output image file path
        path_id: Specific path ID to visualize (None = all paths)
        boxes_per_row: Maximum number of boxes per row (default: 20)
        box_width: Width of task boxes (default: 2.8)
        box_height: Height of task boxes (default: 1.0)
        horizontal_spacing: Horizontal space between boxes (default: 3.2)
        vertical_spacing: Vertical space between rows (default: 1.6)
    """
    project = data['project']
    summary = data['summary']
    critical_paths = data['critical_paths']

    # Filter to specific path if requested
    if path_id is not None:
        critical_paths = [p for p in critical_paths if p['path_id'] == path_id]
        if not critical_paths:
            raise ValueError(f"Path ID {path_id} not found")

    # Color scheme
    colors = {
        'primary': '#4CAF50',      # Green
        'alternate': '#FF9800',    # Orange
        'box_edge': '#333333',     # Dark gray
        'arrow': '#666666',        # Gray
        'text': '#000000'          # Black
    }

    # Process each path
    for path_idx, path in enumerate(critical_paths):
        activities = path['activities']
        is_primary = path['is_primary']
        box_color = colors['primary'] if is_primary else colors['alternate']

        # Calculate layout dimensions
        num_activities = len(activities)
        num_rows = (num_activities + boxes_per_row - 1) // boxes_per_row  # Ceiling division

        # Figure dimensions
        fig_width = max(30, boxes_per_row * horizontal_spacing + 2)
        fig_height = max(8, num_rows * vertical_spacing + 5)

        fig, ax = plt.subplots(figsize=(fig_width, fig_height))
        ax.set_xlim(0, fig_width)
        ax.set_ylim(0, fig_height)
        ax.axis('off')

        # Title
        title = f"{project['project_name'] or project['project_code']}\nCritical Path Diagram"
        if path_id:
            title += f" - Path {path_id}"
        elif not is_primary:
            title += f" - Path {path['path_id']}"
        plt.title(title, fontsize=14, fontweight='bold', pad=15)

        # Summary text
        summary_text = (
            f"Path {path['path_id']}" + (" (Primary)" if is_primary else "") +
            f" | Duration: {path['duration_days']:.1f} days ({path['duration_hours']:.0f} hours) | "
            f"Activities: {path['activity_count']}"
        )
        ax.text(
            fig_width / 2, fig_height - 1.5,
            summary_text,
            ha='center', va='top',
            fontsize=10,
            bbox=dict(boxstyle='round,pad=0.5', facecolor=box_color, alpha=0.3)
        )

        # Starting position (top-left corner)
        margin_left = 1.5
        margin_top = fig_height - 3.0
        y_current = margin_top

        # Draw activities
        for i, activity in enumerate(activities):
            # Calculate position (row and column)
            row = i // boxes_per_row
            col = i % boxes_per_row

            # Calculate coordinates
            x_pos = margin_left + col * horizontal_spacing
            y_pos = margin_top - row * vertical_spacing

            # Draw task box
            box = FancyBboxPatch(
                (x_pos - box_width / 2, y_pos - box_height / 2),
                box_width, box_height,
                boxstyle="round,pad=0.08",
                linewidth=1.5,
                edgecolor=colors['box_edge'],
                facecolor=box_color,
                alpha=0.8
            )
            ax.add_patch(box)

            # Sequence number (small, in top-left corner)
            ax.text(
                x_pos - box_width / 2 + 0.12, y_pos + box_height / 2 - 0.12,
                str(activity['sequence']),
                ha='left', va='top',
                fontsize=7,
                color='white',
                fontweight='bold',
                bbox=dict(boxstyle='circle,pad=0.05', facecolor=colors['box_edge'])
            )

            # Task code (bold, top)
            ax.text(
                x_pos, y_pos + 0.2,
                activity['task_code'],
                ha='center', va='center',
                fontsize=7,
                fontweight='bold',
                color=colors['text']
            )

            # Task name (wrapped, bottom)
            task_name = wrap_text(activity['task_name'], width=25)
            ax.text(
                x_pos, y_pos - 0.15,
                task_name,
                ha='center', va='center',
                fontsize=5.5,
                color=colors['text']
            )

            # Draw arrow to next task
            if i < len(activities) - 1:
                next_row = (i + 1) // boxes_per_row
                next_col = (i + 1) % boxes_per_row

                next_x = margin_left + next_col * horizontal_spacing
                next_y = margin_top - next_row * vertical_spacing

                # Check if we're wrapping to next row
                if row == next_row:
                    # Same row - horizontal arrow
                    arrow = FancyArrowPatch(
                        (x_pos + box_width / 2 + 0.05, y_pos),
                        (next_x - box_width / 2 - 0.05, next_y),
                        arrowstyle='->,head_width=0.3,head_length=0.4',
                        linewidth=1.5,
                        color=colors['arrow'],
                        zorder=1
                    )
                    ax.add_patch(arrow)
                else:
                    # Wrapping to next row - route through the space between rows
                    # Start from bottom of current box, end at top of next box
                    start_x = x_pos
                    start_y = y_pos - box_height / 2 - 0.05  # Bottom of current box
                    end_x = next_x
                    end_y = next_y + box_height / 2 + 0.05  # Top of next box

                    # Calculate midpoint in the vertical space between rows
                    mid_y = (start_y + end_y) / 2

                    # Three-segment path through the space between rows
                    # Segment 1: go down from current box to middle space
                    arrow1 = FancyArrowPatch(
                        (start_x, start_y),
                        (start_x, mid_y),
                        arrowstyle='-',
                        linewidth=1.5,
                        color=colors['arrow'],
                        zorder=1
                    )
                    ax.add_patch(arrow1)

                    # Segment 2: go horizontally through the middle space
                    arrow2 = FancyArrowPatch(
                        (start_x, mid_y),
                        (end_x, mid_y),
                        arrowstyle='-',
                        linewidth=1.5,
                        color=colors['arrow'],
                        zorder=1
                    )
                    ax.add_patch(arrow2)

                    # Segment 3: go up to next box (with arrow head)
                    arrow3 = FancyArrowPatch(
                        (end_x, mid_y),
                        (end_x, end_y),
                        arrowstyle='->,head_width=0.3,head_length=0.4',
                        linewidth=1.5,
                        color=colors['arrow'],
                        zorder=1
                    )
                    ax.add_patch(arrow3)

        # Footer
        ax.text(
            fig_width / 2, 0.3,
            f"Generated by XEReader | {boxes_per_row} activities per row",
            ha='center', va='bottom',
            fontsize=7,
            style='italic',
            color='gray'
        )

        plt.tight_layout()

        # Generate output filename for this path
        if len(critical_paths) > 1 and path_id is None:
            # Multiple paths, save separately
            output_file = Path(output_path)
            path_output = output_file.parent / f"{output_file.stem}_path{path['path_id']}{output_file.suffix}"
            plt.savefig(path_output, dpi=300, bbox_inches='tight', facecolor='white')
            print(f"✓ Diagram saved to: {path_output}")
        else:
            # Single path or specific path requested
            plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
            print(f"✓ Diagram saved to: {output_path}")

        plt.close()

    return output_path


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Generate critical path diagram from JSON (horizontal layout)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python visualize_critical_path.py critical_path.json
  python visualize_critical_path.py critical_path.json --output diagram.png
  python visualize_critical_path.py critical_path.json --path-id 1
  python visualize_critical_path.py critical_path.json --boxes-per-row 15

Layout:
  - Horizontal flow (left to right)
  - Maximum 20 boxes per row by default
  - Automatic wrapping to new rows with connector arrows

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
        '--boxes-per-row',
        type=int,
        default=20,
        help='Maximum number of task boxes per row (default: 20)'
    )

    parser.add_argument(
        '--box-width',
        type=float,
        default=2.8,
        help='Task box width (default: 2.8)'
    )

    parser.add_argument(
        '--box-height',
        type=float,
        default=1.0,
        help='Task box height (default: 1.0)'
    )

    parser.add_argument(
        '--horizontal-spacing',
        type=float,
        default=3.2,
        help='Horizontal spacing between boxes (default: 3.2)'
    )

    parser.add_argument(
        '--vertical-spacing',
        type=float,
        default=1.6,
        help='Vertical spacing between rows (default: 1.6)'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='Critical Path Visualizer 2.0.0'
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
        print(f"Layout: {args.boxes_per_row} boxes per row, horizontal flow with wrapping")

        if args.path_id:
            print(f"Visualizing path {args.path_id} only")

        # Generate diagram
        print("Generating diagram...")
        draw_critical_path_diagram(
            data,
            str(output_path),
            path_id=args.path_id,
            boxes_per_row=args.boxes_per_row,
            box_width=args.box_width,
            box_height=args.box_height,
            horizontal_spacing=args.horizontal_spacing,
            vertical_spacing=args.vertical_spacing
        )

        if num_paths > 1 and args.path_id is None:
            print(f"\nNote: Multiple paths detected. Each path saved as a separate file.")

        print(f"\nDone!")

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
