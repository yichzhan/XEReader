"""XER file parser"""
from typing import Dict, List, Optional
import os


class XERParser:
    """Parser for Primavera P6 XER files (tab-delimited format)"""

    def __init__(self, file_path: str):
        """
        Initialize parser with XER file path

        Args:
            file_path: Path to XER file
        """
        self.file_path = file_path
        self.tables: Dict[str, List[Dict]] = {}

    def parse(self) -> Dict[str, List[Dict]]:
        """
        Parse XER file and extract all tables

        Returns:
            Dictionary mapping table names to list of row dictionaries

        Raises:
            FileNotFoundError: If XER file doesn't exist
            ValueError: If file format is invalid
        """
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"XER file not found: {self.file_path}")

        # Try different encodings (XER files can be UTF-8 or latin-1)
        encodings = ['utf-8', 'latin-1', 'cp1252']
        content = None

        for encoding in encodings:
            try:
                with open(self.file_path, 'r', encoding=encoding) as f:
                    content = f.readlines()
                break
            except UnicodeDecodeError:
                continue

        if content is None:
            raise ValueError(f"Could not read file with supported encodings: {encodings}")

        self._parse_tables(content)
        return self.tables

    def _parse_tables(self, lines: List[str]) -> None:
        """
        Parse XER file content into tables

        XER format:
        %T <table_name>      - Table marker
        %F <field1> <field2> - Field names (tab-separated)
        %R <value1> <value2> - Row data (tab-separated)
        """
        current_table = None
        current_fields = []

        for line in lines:
            line = line.rstrip('\n\r')

            if not line or line.startswith('%E'):  # Empty or end marker
                continue

            if line.startswith('%T\t'):
                # Table marker
                current_table = line.split('\t')[1]
                current_fields = []
                self.tables[current_table] = []

            elif line.startswith('%F\t'):
                # Field definition
                current_fields = line.split('\t')[1:]

            elif line.startswith('%R\t'):
                # Row data
                if current_table and current_fields:
                    values = line.split('\t')[1:]
                    row = self._create_row(current_fields, values)
                    self.tables[current_table].append(row)

    def _create_row(self, fields: List[str], values: List[str]) -> Dict:
        """
        Create a dictionary from field names and values

        Args:
            fields: List of field names
            values: List of values

        Returns:
            Dictionary mapping field names to values
        """
        row = {}
        for i, field in enumerate(fields):
            value = values[i] if i < len(values) else ''
            row[field] = value if value else None
        return row

    def get_table(self, table_name: str) -> List[Dict]:
        """
        Get a specific table by name

        Args:
            table_name: Name of the table

        Returns:
            List of row dictionaries for the table

        Raises:
            KeyError: If table doesn't exist
        """
        if table_name not in self.tables:
            raise KeyError(f"Table '{table_name}' not found in XER file")
        return self.tables[table_name]

    def has_table(self, table_name: str) -> bool:
        """Check if a table exists in the parsed data"""
        return table_name in self.tables

    def get_table_names(self) -> List[str]:
        """Get list of all table names"""
        return list(self.tables.keys())
