"""
Excel parser for carrier data.
Supports .xlsx and .xls files.
"""
import pandas as pd
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from schema import (
    Broker, Load, Lane, Rate, Address, CarrierProfile,
    DataSource
)
from parser.csv_parser import CSVParser


class ExcelParser(CSVParser):
    """Parser for Excel files containing carrier booking data"""
    
    def parse_file(self, file_path: str) -> CarrierProfile:
        """
        Parse an Excel file and return a CarrierProfile.
        
        Args:
            file_path: Path to the Excel file (.xlsx or .xls)
            
        Returns:
            CarrierProfile with parsed data
        """
        try:
            # Read Excel file
            df = pd.read_excel(file_path, engine='openpyxl')
        except Exception as e:
            # Try with xlrd for .xls files
            try:
                df = pd.read_excel(file_path, engine='xlrd')
            except Exception as e2:
                raise ValueError(f"Could not parse Excel file: {e}, {e2}")
        
        # Convert to CSV-like format for processing
        # Get headers
        headers = df.columns.tolist()
        
        # Convert DataFrame to list of rows
        rows = []
        for _, row in df.iterrows():
            rows.append([str(val) if pd.notna(val) else '' for val in row])
        
        # Build CSV content string
        csv_lines = [','.join(headers)]
        for row in rows:
            # Escape commas in values
            escaped_row = []
            for val in row:
                if ',' in val:
                    escaped_row.append(f'"{val}"')
                else:
                    escaped_row.append(val)
            csv_lines.append(','.join(escaped_row))
        
        csv_content = '\n'.join(csv_lines)
        
        # Use parent CSV parser logic
        return self.parse_content(csv_content, source_file=file_path)
    
    def parse_sheets(self, file_path: str) -> Dict[str, CarrierProfile]:
        """
        Parse multiple sheets from an Excel file.
        
        Args:
            file_path: Path to the Excel file
            
        Returns:
            Dictionary mapping sheet names to CarrierProfile objects
        """
        try:
            excel_file = pd.ExcelFile(file_path, engine='openpyxl')
        except Exception:
            try:
                excel_file = pd.ExcelFile(file_path, engine='xlrd')
            except Exception as e:
                raise ValueError(f"Could not parse Excel file: {e}")
        
        profiles = {}
        for sheet_name in excel_file.sheet_names:
            try:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                
                # Convert to CSV format
                headers = df.columns.tolist()
                rows = []
                for _, row in df.iterrows():
                    rows.append([str(val) if pd.notna(val) else '' for val in row])
                
                csv_lines = [','.join(headers)]
                for row in rows:
                    escaped_row = []
                    for val in row:
                        if ',' in val:
                            escaped_row.append(f'"{val}"')
                        else:
                            escaped_row.append(val)
                    csv_lines.append(','.join(escaped_row))
                
                csv_content = '\n'.join(csv_lines)
                profiles[sheet_name] = self.parse_content(csv_content, source_file=f"{file_path}:{sheet_name}")
            except Exception as e:
                print(f"Warning: Could not parse sheet '{sheet_name}': {e}")
                continue
        
        return profiles

