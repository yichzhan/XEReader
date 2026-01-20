"""Integration tests for full workflow"""
import pytest
import json
from pathlib import Path
from src.parser.xer_parser import XERParser
from src.processors.activity_processor import ActivityProcessor
from src.processors.critical_path_calculator import CriticalPathCalculator
from src.exporters.json_exporter import JSONExporter
from src.utils.validators import validate_required_tables, validate_activities


def test_full_workflow(tmp_path):
    """Test complete workflow from XER to JSON"""
    # Parse XER
    fixture_path = Path(__file__).parent / 'fixtures' / 'sample.xer'
    parser = XERParser(str(fixture_path))
    tables = parser.parse()

    # Validate tables
    required_tables = ['PROJECT', 'TASK', 'TASKPRED']
    validate_required_tables(parser, required_tables)

    # Process project
    activity_processor = ActivityProcessor()
    project_info = activity_processor.process_project(parser.get_table('PROJECT'))
    assert project_info.project_code == 'PRJ-2026-001'

    # Process activities
    activities = activity_processor.process_activities(parser.get_table('TASK'))
    assert len(activities) == 6

    # Process dependencies
    activity_processor.process_dependencies(parser.get_table('TASKPRED'))

    # Validate
    validate_activities(activities)

    # Calculate critical path
    cpm_calculator = CriticalPathCalculator(activities)
    critical_paths, project_duration = cpm_calculator.calculate()

    assert len(critical_paths) > 0
    assert project_duration > 0

    # Export JSON
    activities_path = tmp_path / 'activities.json'
    critical_path_path = tmp_path / 'critical_path.json'

    exporter = JSONExporter(project_info, activities)
    exporter.export_activities(str(activities_path))
    exporter.export_critical_path(str(critical_path_path), critical_paths, project_duration)

    # Verify files exist
    assert activities_path.exists()
    assert critical_path_path.exists()

    # Validate JSON structure
    with open(activities_path, 'r') as f:
        activities_data = json.load(f)
        assert 'project' in activities_data
        assert 'activities' in activities_data
        assert len(activities_data['activities']) == 6

    with open(critical_path_path, 'r') as f:
        critical_path_data = json.load(f)
        assert 'project' in critical_path_data
        assert 'summary' in critical_path_data
        assert 'critical_paths' in critical_path_data
        assert critical_path_data['summary']['critical_path_count'] > 0


def test_activities_json_schema(tmp_path):
    """Test activities.json matches expected schema"""
    fixture_path = Path(__file__).parent / 'fixtures' / 'sample.xer'
    parser = XERParser(str(fixture_path))
    parser.parse()

    activity_processor = ActivityProcessor()
    project_info = activity_processor.process_project(parser.get_table('PROJECT'))
    activities = activity_processor.process_activities(parser.get_table('TASK'))
    activity_processor.process_dependencies(parser.get_table('TASKPRED'))

    activities_path = tmp_path / 'activities.json'
    exporter = JSONExporter(project_info, activities)
    exporter.export_activities(str(activities_path))

    with open(activities_path, 'r') as f:
        data = json.load(f)

    # Check project section
    assert 'project_code' in data['project']
    assert 'project_name' in data['project']

    # Check activities section
    assert isinstance(data['activities'], list)

    for activity in data['activities']:
        # Required fields
        assert 'task_code' in activity
        assert 'task_name' in activity
        assert 'planned_start_date' in activity
        assert 'planned_end_date' in activity
        assert 'actual_start_date' in activity
        assert 'actual_end_date' in activity

        # Dependencies
        assert 'dependencies' in activity
        assert 'predecessors' in activity['dependencies']
        assert 'successors' in activity['dependencies']

        # Check dependency structure
        for dep in activity['dependencies']['predecessors']:
            assert 'task_code' in dep
            assert 'dependency_type' in dep
            assert 'lag_hours' in dep

        for dep in activity['dependencies']['successors']:
            assert 'task_code' in dep
            assert 'dependency_type' in dep
            assert 'lag_hours' in dep


def test_critical_path_json_schema(tmp_path):
    """Test critical_path.json matches expected schema"""
    fixture_path = Path(__file__).parent / 'fixtures' / 'sample.xer'
    parser = XERParser(str(fixture_path))
    parser.parse()

    activity_processor = ActivityProcessor()
    project_info = activity_processor.process_project(parser.get_table('PROJECT'))
    activities = activity_processor.process_activities(parser.get_table('TASK'))
    activity_processor.process_dependencies(parser.get_table('TASKPRED'))

    cpm_calculator = CriticalPathCalculator(activities)
    critical_paths, project_duration = cpm_calculator.calculate()

    critical_path_path = tmp_path / 'critical_path.json'
    exporter = JSONExporter(project_info, activities)
    exporter.export_critical_path(str(critical_path_path), critical_paths, project_duration)

    with open(critical_path_path, 'r') as f:
        data = json.load(f)

    # Check project section
    assert 'project_code' in data['project']
    assert 'project_name' in data['project']

    # Check summary section
    assert 'total_duration_hours' in data['summary']
    assert 'total_duration_days' in data['summary']
    assert 'critical_path_count' in data['summary']
    assert 'total_activities_on_critical_paths' in data['summary']

    # Check critical paths
    assert isinstance(data['critical_paths'], list)
    assert len(data['critical_paths']) > 0

    for path in data['critical_paths']:
        # Path metadata
        assert 'path_id' in path
        assert 'is_primary' in path
        assert 'duration_hours' in path
        assert 'duration_days' in path
        assert 'activity_count' in path

        # Activities in path
        assert 'activities' in path
        assert isinstance(path['activities'], list)

        for activity in path['activities']:
            assert 'sequence' in activity
            assert 'task_code' in activity
            assert 'task_name' in activity
            assert 'planned_start_date' in activity
            assert 'planned_end_date' in activity

    # Verify primary path
    primary_paths = [p for p in data['critical_paths'] if p['is_primary']]
    assert len(primary_paths) == 1
