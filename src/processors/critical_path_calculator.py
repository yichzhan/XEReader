"""Critical Path Method (CPM) calculator"""
from dataclasses import dataclass
from typing import List, Dict, Tuple, Set, Optional
from datetime import datetime, timedelta
import networkx as nx
from ..models.activity import Activity


@dataclass
class CycleInfo:
    """Information about a cycle in the dependency graph"""
    cycle_id: int
    task_codes: List[str]  # Task codes in the cycle
    task_names: List[str]  # Task names in the cycle
    length: int


class CriticalPathCalculator:
    """
    Calculates critical path using CPM algorithm:
    1. Build network graph
    2. Forward pass (Early Start/Finish)
    3. Backward pass (Late Start/Finish)
    4. Calculate total float
    5. Identify critical activities (float <= 0)
    6. Find longest path(s) through critical activities
    """

    def __init__(self, activities: List[Activity]):
        """
        Initialize calculator with activities

        Args:
            activities: List of Activity objects with dependencies
        """
        self.activities = activities
        self.graph = nx.DiGraph()
        self.task_code_to_activity: Dict[str, Activity] = {
            a.task_code: a for a in activities
        }

    def detect_cycles(self) -> List[CycleInfo]:
        """
        Detect cycles in the dependency graph.

        Must be called after _build_graph().

        Returns:
            List of CycleInfo objects describing each cycle found
        """
        cycles = []
        try:
            raw_cycles = list(nx.simple_cycles(self.graph))
            for i, cycle in enumerate(raw_cycles):
                task_names = []
                for code in cycle:
                    activity = self.task_code_to_activity.get(code)
                    if activity:
                        task_names.append(activity.task_name or '(no name)')
                    else:
                        task_names.append('(unknown)')

                cycles.append(CycleInfo(
                    cycle_id=i + 1,
                    task_codes=cycle,
                    task_names=task_names,
                    length=len(cycle)
                ))
        except Exception:
            pass

        return cycles

    def has_cycles(self) -> bool:
        """
        Check if the graph has any cycles.

        Must be called after _build_graph().

        Returns:
            True if cycles exist, False otherwise
        """
        try:
            nx.find_cycle(self.graph)
            return True
        except nx.NetworkXNoCycle:
            return False

    def calculate(self) -> Tuple[List[List[Activity]], float]:
        """
        Calculate critical path(s)

        Returns:
            Tuple of (list of critical paths, project duration in hours)
            Each critical path is a list of Activity objects in sequence

        Raises:
            ValueError: If the graph contains cycles
        """
        # Build network graph
        self._build_graph()

        # Check for cycles before proceeding
        if self.has_cycles():
            raise ValueError("Graph contains cycles - cannot calculate critical path")

        # Perform CPM calculations
        self._forward_pass()
        self._backward_pass()
        self._calculate_total_float()

        # Find critical activities
        critical_activities = self._identify_critical_activities()

        if not critical_activities:
            return [], 0.0

        # Find longest path(s) through critical activities
        critical_paths = self._find_critical_paths(critical_activities)

        # Get project duration
        project_duration = self._calculate_project_duration()

        return critical_paths, project_duration

    def build_graph_only(self) -> None:
        """Build the graph without calculating critical path (for cycle detection)"""
        self._build_graph()

    def _build_graph(self) -> None:
        """Build directed graph from activities and dependencies"""
        # Add all activities as nodes
        for activity in self.activities:
            self.graph.add_node(
                activity.task_code,
                activity=activity,
                duration=activity.duration_hours
            )

        # Add edges for dependencies
        for activity in self.activities:
            for successor in activity.successors:
                # Edge from activity to successor
                self.graph.add_edge(
                    activity.task_code,
                    successor.task_code,
                    lag=successor.lag_hours,
                    dep_type=successor.dependency_type
                )

    def _forward_pass(self) -> None:
        """
        Forward pass: Calculate Early Start (ES) and Early Finish (EF)
        ES = max(EF of all predecessors + lag)
        EF = ES + duration
        """
        # Find start nodes (no predecessors)
        start_nodes = [node for node in self.graph.nodes()
                       if self.graph.in_degree(node) == 0]

        # Topological sort for processing order
        try:
            sorted_nodes = list(nx.topological_sort(self.graph))
        except nx.NetworkXError:
            # Graph has cycles - this shouldn't happen with valid project data
            sorted_nodes = list(self.graph.nodes())

        # Initialize project start date (use earliest planned start)
        project_start = min(
            (a.planned_start_date for a in self.activities if a.planned_start_date),
            default=datetime.now()
        )

        for node in sorted_nodes:
            activity = self.graph.nodes[node]['activity']

            if node in start_nodes:
                # Start node: ES = project start
                activity.early_start = project_start
            else:
                # ES = max(EF of predecessors + lag)
                max_early_start = project_start
                for pred in self.graph.predecessors(node):
                    pred_activity = self.graph.nodes[pred]['activity']
                    if pred_activity.early_finish:
                        edge_data = self.graph[pred][node]
                        lag = edge_data.get('lag', 0)
                        pred_finish_with_lag = pred_activity.early_finish + timedelta(hours=lag)
                        if pred_finish_with_lag > max_early_start:
                            max_early_start = pred_finish_with_lag

                activity.early_start = max_early_start

            # EF = ES + duration
            activity.early_finish = activity.early_start + timedelta(hours=activity.duration_hours)

    def _backward_pass(self) -> None:
        """
        Backward pass: Calculate Late Start (LS) and Late Finish (LF)
        LF = min(LS of all successors - lag)
        LS = LF - duration
        """
        # Find end nodes (no successors)
        end_nodes = [node for node in self.graph.nodes()
                     if self.graph.out_degree(node) == 0]

        # Reverse topological sort
        try:
            sorted_nodes = list(reversed(list(nx.topological_sort(self.graph))))
        except nx.NetworkXError:
            sorted_nodes = list(reversed(list(self.graph.nodes())))

        # Project end date = max early finish
        project_end = max(
            (a.early_finish for a in self.activities if a.early_finish),
            default=datetime.now()
        )

        for node in sorted_nodes:
            activity = self.graph.nodes[node]['activity']

            if node in end_nodes:
                # End node: LF = project end
                activity.late_finish = project_end
            else:
                # LF = min(LS of successors - lag)
                min_late_finish = project_end
                for succ in self.graph.successors(node):
                    succ_activity = self.graph.nodes[succ]['activity']
                    if succ_activity.late_start:
                        edge_data = self.graph[node][succ]
                        lag = edge_data.get('lag', 0)
                        succ_start_minus_lag = succ_activity.late_start - timedelta(hours=lag)
                        if succ_start_minus_lag < min_late_finish:
                            min_late_finish = succ_start_minus_lag

                activity.late_finish = min_late_finish

            # LS = LF - duration
            activity.late_start = activity.late_finish - timedelta(hours=activity.duration_hours)

    def _calculate_total_float(self) -> None:
        """
        Calculate total float for each activity
        Total Float = LS - ES (in hours)
        """
        for activity in self.activities:
            if activity.late_start and activity.early_start:
                delta = activity.late_start - activity.early_start
                activity.total_float_hours = delta.total_seconds() / 3600
            else:
                activity.total_float_hours = 0.0

    def _identify_critical_activities(self) -> List[Activity]:
        """
        Identify critical activities (total float <= 0)

        Returns:
            List of critical Activity objects
        """
        critical = []
        for activity in self.activities:
            if activity.total_float_hours is not None and activity.total_float_hours <= 0.01:
                # Use small threshold for floating point comparison
                critical.append(activity)

        return critical

    def _find_critical_paths(self, critical_activities: List[Activity]) -> List[List[Activity]]:
        """
        Find all paths through critical activities and select longest path(s)

        Args:
            critical_activities: List of critical activities

        Returns:
            List of critical paths (each path is a list of Activity objects)
        """
        # Build subgraph with only critical activities
        critical_codes = {a.task_code for a in critical_activities}
        critical_graph = self.graph.subgraph(critical_codes)

        # Find start and end nodes in critical subgraph
        start_nodes = [node for node in critical_graph.nodes()
                       if critical_graph.in_degree(node) == 0]
        end_nodes = [node for node in critical_graph.nodes()
                     if critical_graph.out_degree(node) == 0]

        if not start_nodes or not end_nodes:
            # If no clear start/end in critical activities, return all critical activities
            return [critical_activities]

        # Find all paths from start to end
        all_paths = []
        for start in start_nodes:
            for end in end_nodes:
                try:
                    paths = nx.all_simple_paths(critical_graph, start, end)
                    all_paths.extend(list(paths))
                except nx.NetworkXNoPath:
                    continue

        if not all_paths:
            return [critical_activities]

        # Calculate duration for each path
        path_durations = []
        for path in all_paths:
            duration = sum(
                self.task_code_to_activity[code].duration_hours
                for code in path
            )
            path_durations.append(duration)

        # Find longest path(s)
        if path_durations:
            max_duration = max(path_durations)
            critical_paths = []

            for path, duration in zip(all_paths, path_durations):
                if abs(duration - max_duration) < 0.01:  # Floating point comparison
                    # Convert task codes to Activity objects
                    activity_path = [
                        self.task_code_to_activity[code] for code in path
                    ]
                    critical_paths.append(activity_path)

            return critical_paths

        return [critical_activities]

    def _calculate_project_duration(self) -> float:
        """
        Calculate total project duration in hours

        Returns:
            Project duration in hours
        """
        if not self.activities:
            return 0.0

        # Duration = max(early_finish) - min(early_start)
        early_starts = [a.early_start for a in self.activities if a.early_start]
        early_finishes = [a.early_finish for a in self.activities if a.early_finish]

        if not early_starts or not early_finishes:
            return 0.0

        project_start = min(early_starts)
        project_end = max(early_finishes)

        delta = project_end - project_start
        return delta.total_seconds() / 3600
