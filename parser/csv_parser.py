"""
Enhanced CSV parser for carrier data.
Extends the original broker parser to handle loads, rates, and addresses.
"""
import csv
import re
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from schema import (
    Broker, Load, Lane, Rate, Address, CarrierProfile,
    DataSource
)


class CSVParser:
    """Parser for CSV files containing carrier booking data"""
    
    def __init__(self):
        self.brokers: List[Broker] = []
        self.loads: List[Load] = []
        self.lanes: List[Lane] = []
        self.rates: List[Rate] = []
    
    def parse_file(self, file_path: str) -> CarrierProfile:
        """
        Parse a CSV file and return a CarrierProfile.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            CarrierProfile with parsed data
        """
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            return self.parse_content(content, source_file=file_path)
    
    def parse_content(self, content: str, source_file: Optional[str] = None) -> CarrierProfile:
        """
        Parse CSV content string into structured data.
        
        Args:
            content: Raw CSV content as string
            source_file: Optional source file path for metadata
            
        Returns:
            CarrierProfile with parsed data
        """
        self.brokers = []
        self.loads = []
        self.lanes = []
        self.rates = []
        
        lines = content.strip().split('\n')
        reader = csv.reader(lines)
        rows = list(reader)
        
        if not rows:
            return CarrierProfile()
        
        headers = [h.strip() for h in rows[0]]
        print(f"Found {len(headers)} columns: {headers}")
        print(f"Processing {len(rows) - 1} data rows...\n")
        
        # Process each data row
        for row_num, row in enumerate(rows[1:], start=2):
            if not row or not any(row):
                continue
            
            self._parse_row(row, headers, row_num)
        
        # Build carrier profile
        profile = CarrierProfile(
            brokers=self.brokers,
            loads=self.loads,
            lanes=self.lanes,
            created_at=datetime.now()
        )
        
        return profile
    
    def _parse_row(self, row: List[str], headers: List[str], row_num: int):
        """Parse a single CSV row into structured objects"""
        # Map headers to values
        row_data = {}
        for i, header in enumerate(headers):
            if i < len(row):
                row_data[header] = row[i].strip() if row[i] else None
        
        # Create broker
        broker = self._create_broker(row_data, row_num)
        if broker:
            self.brokers.append(broker)
        
        # Create lane
        lane = self._create_lane(row_data, row_num)
        if lane:
            self.lanes.append(lane)
        
        # Create load
        load = self._create_load(row_data, broker, lane, row_num)
        if load:
            self.loads.append(load)
        
        # Create rate
        rate = self._create_rate(row_data, load, row_num)
        if rate:
            self.rates.append(rate)
            if load:
                load.rate = rate
    
    def _create_broker(self, row_data: Dict[str, Any], row_num: int) -> Optional[Broker]:
        """Create a Broker object from row data"""
        broker = Broker(source=DataSource.CSV, created_at=datetime.now())
        
        # Map CSV columns to broker fields
        column_mapping = {
            'Name': 'broker_name',
            'Broker': 'company_name',
            'MC#': 'mc_id',
            'Phone Number': 'broker_phone_number',
            'Email': 'broker_email',
            'Address': 'company_address',
            'Date': 'date_of_contract',
            'Load #': 'load_id',
            # 'State' is not part of Broker schema - state info is in address
            'Trip': 'source_destination',
            'Notes': 'notes',
            'Load Board': 'load_board'
        }
        
        for csv_col, attr_name in column_mapping.items():
            value = row_data.get(csv_col)
            if value and value not in ['N/L', 'N/A', '']:
                if attr_name == 'company_address':
                    # Parse address
                    broker.company_address = self._parse_address(value)
                elif attr_name == 'date_of_contract':
                    broker.date_of_contract = self._parse_date(value)
                elif attr_name == 'mc_id':
                    # Clean MC number
                    broker.mc_id = re.sub(r'[^\d]', '', value)
                else:
                    setattr(broker, attr_name, value)
        
        # Clean broker data
        self._clean_broker_data(broker)
        
        return broker if broker.company_name or broker.broker_name else None
    
    def _create_lane(self, row_data: Dict[str, Any], row_num: int) -> Optional[Lane]:
        """Create a Lane object from row data"""
        trip = row_data.get('Trip') or row_data.get('source_destination')
        if not trip:
            return None
        
        lane = Lane(source=DataSource.CSV, created_at=datetime.now())
        lane.origin_city_state, lane.destination_city_state = self._parse_trip(trip)
        
        # Try to extract addresses if available
        if lane.origin_city_state:
            lane.origin = Address(raw_address=lane.origin_city_state)
        if lane.destination_city_state:
            lane.destination = Address(raw_address=lane.destination_city_state)
        
        return lane
    
    def _create_load(self, row_data: Dict[str, Any], broker: Optional[Broker], 
                    lane: Optional[Lane], row_num: int) -> Optional[Load]:
        """Create a Load object from row data"""
        load_id = row_data.get('Load #') or row_data.get('Load #')
        if not load_id:
            return None
        
        load = Load(
            load_id=load_id,
            broker=broker,
            broker_id=broker.mc_id if broker else None,
            lane=lane,
            source=DataSource.CSV,
            created_at=datetime.now()
        )
        
        # Parse dates
        date_str = row_data.get('Date')
        if date_str:
            load.booking_date = self._parse_date(date_str)
            load.pickup_date = load.booking_date  # Default to booking date
        
        load.notes = row_data.get('Notes')
        load.load_board = row_data.get('Load Board')
        load.status = 'booked'  # Default status
        
        return load
    
    def _create_rate(self, row_data: Dict[str, Any], load: Optional[Load], 
                    row_num: int) -> Optional[Rate]:
        """Create a Rate object from row data"""
        # Try to extract rate from notes or other fields
        notes = row_data.get('Notes') or ''
        
        # Look for rate patterns in notes (only if notes is not empty)
        rate_amount = None
        if notes:
            from parser.utils import extract_rate_from_text
            rate_amount = extract_rate_from_text(notes)
        
        # Only create rate if we found an amount or have a load
        if not rate_amount and not load:
            return None
        
        rate = Rate(
            load_id=load.load_id if load else None,
            source=DataSource.CSV,
            created_at=datetime.now()
        )
        
        if rate_amount:
            rate.rate_amount = rate_amount
            rate.rate_type = 'flat'
        
        return rate
    
    def _parse_address(self, address_str: str) -> Address:
        """Parse address string into Address object"""
        if not address_str:
            return Address()
        
        address = Address(raw_address=address_str)
        
        # Try to extract state (2-letter code)
        state_match = re.search(r'\b([A-Z]{2})\b', address_str)
        if state_match:
            address.state = state_match.group(1)
        
        # Try to extract ZIP code
        zip_match = re.search(r'\b(\d{5}(?:-\d{4})?)\b', address_str)
        if zip_match:
            address.zip_code = zip_match.group(1)
        
        # Simple city extraction (text before state)
        if address.state:
            parts = address_str.split(address.state)
            if parts:
                city_part = parts[0].strip().rstrip(',').strip()
                # Take last part as city (usually city name)
                city_parts = city_part.split(',')
                if city_parts:
                    address.city = city_parts[-1].strip()
        
        return address
    
    def _parse_trip(self, trip_str: str) -> tuple:
        """Parse trip string into origin and destination"""
        from parser.utils import parse_trip
        return parse_trip(trip_str)
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string into datetime object"""
        from parser.utils import parse_date
        return parse_date(date_str)
    
    def _clean_broker_data(self, broker: Broker):
        """Clean and normalize broker data"""
        if broker.company_name:
            broker.company_name = broker.company_name.replace('**', '').strip()
        
        if broker.broker_name:
            broker.broker_name = broker.broker_name.replace('**', '').strip()
        
        if broker.mc_id:
            broker.mc_id = re.sub(r'[^\d]', '', broker.mc_id)
        
        if broker.broker_phone_number:
            broker.broker_phone_number = broker.broker_phone_number.strip()

