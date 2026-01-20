"""Tests for XER parser"""
import pytest
from pathlib import Path
from src.parser.xer_parser import XERParser


def test_parse_sample_xer():
    """Test parsing sample XER file"""
    fixture_path = Path(__file__).parent / 'fixtures' / 'sample.xer'
    parser = XERParser(str(fixture_path))
    tables = parser.parse()

    # Check tables exist
    assert 'PROJECT' in tables
    assert 'TASK' in tables
    assert 'TASKPRED' in tables

    # Check PROJECT table
    project_table = parser.get_table('PROJECT')
    assert len(project_table) == 1
    assert project_table[0]['proj_short_name'] == 'PRJ-2026-001'
    assert project_table[0]['proj_name'] == 'Sample Construction Project'

    # Check TASK table
    task_table = parser.get_table('TASK')
    assert len(task_table) == 6
    assert task_table[0]['task_code'] == 'A1000'

    # Check TASKPRED table
    taskpred_table = parser.get_table('TASKPRED')
    assert len(taskpred_table) == 5


def test_missing_file():
    """Test error handling for missing file"""
    parser = XERParser('nonexistent.xer')
    with pytest.raises(FileNotFoundError):
        parser.parse()


def test_get_table_names():
    """Test getting table names"""
    fixture_path = Path(__file__).parent / 'fixtures' / 'sample.xer'
    parser = XERParser(str(fixture_path))
    parser.parse()

    table_names = parser.get_table_names()
    assert 'PROJECT' in table_names
    assert 'TASK' in table_names
    assert 'TASKPRED' in table_names
