"""
Unified parser interface for all file types.
Automatically detects file type and uses appropriate parser.
"""
from pathlib import Path
from typing import Optional
from datetime import datetime

from schema import CarrierProfile, DataSource
from parser.csv_parser import CSVParser
from parser.excel_parser import ExcelParser
from parser.pdf_parser import PDFParser


class UnifiedParser:
    """Unified interface for parsing carrier data from various file formats"""
    
    def __init__(self):
        self.csv_parser = CSVParser()
        self.excel_parser = ExcelParser()
        self.pdf_parser = PDFParser()
    
    def parse_file(self, file_path: str) -> CarrierProfile:
        """
        Parse a file and return CarrierProfile.
        Automatically detects file type based on extension.
        
        Args:
            file_path: Path to the file (CSV, Excel, or PDF)
            
        Returns:
            CarrierProfile with parsed data
        """
        path = Path(file_path)
        extension = path.suffix.lower()
        
        if extension == '.csv':
            return self.csv_parser.parse_file(file_path)
        elif extension in ['.xlsx', '.xls']:
            return self.excel_parser.parse_file(file_path)
        elif extension == '.pdf':
            return self.pdf_parser.parse_file(file_path)
        else:
            raise ValueError(f"Unsupported file type: {extension}. Supported: .csv, .xlsx, .xls, .pdf")
    
    def parse_multiple_files(self, file_paths: list[str]) -> CarrierProfile:
        """
        Parse multiple files and merge into a single CarrierProfile.
        
        Args:
            file_paths: List of file paths to parse
            
        Returns:
            Merged CarrierProfile
        """
        merged_profile = CarrierProfile(created_at=datetime.now())
        
        for file_path in file_paths:
            try:
                profile = self.parse_file(file_path)
                
                # Merge brokers
                merged_profile.brokers.extend(profile.brokers)
                
                # Merge loads
                merged_profile.loads.extend(profile.loads)
                
                # Merge lanes
                merged_profile.lanes.extend(profile.lanes)
                
            except Exception as e:
                print(f"Warning: Could not parse {file_path}: {e}")
                continue
        
        return merged_profile

