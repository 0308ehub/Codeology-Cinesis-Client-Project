"""
PDF parser for booking confirmations and carrier documents.
Uses pdfplumber for better text extraction.
"""
import re
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

from schema import (
    Broker, Load, Lane, Rate, Address, CarrierProfile,
    DataSource
)
from parser.csv_parser import CSVParser


class PDFParser:
    """Parser for PDF files containing booking confirmations"""
    
    def __init__(self):
        if pdfplumber is None:
            raise ImportError("pdfplumber is required for PDF parsing. Install with: pip install pdfplumber")
    
    def parse_file(self, file_path: str) -> CarrierProfile:
        """
        Parse a PDF file and extract booking information.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            CarrierProfile with parsed data
        """
        brokers = []
        loads = []
        lanes = []
        rates = []
        
        with pdfplumber.open(file_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() or ""
        
        # Extract structured data from text
        extracted_data = self._extract_data_from_text(full_text)
        
        # Create objects from extracted data
        if extracted_data.get('broker'):
            broker = self._create_broker_from_extracted(extracted_data['broker'])
            if broker:
                brokers.append(broker)
        
        if extracted_data.get('lane'):
            lane = self._create_lane_from_extracted(extracted_data['lane'])
            if lane:
                lanes.append(lane)
        
        if extracted_data.get('load'):
            load = self._create_load_from_extracted(
                extracted_data['load'],
                brokers[0] if brokers else None,
                lanes[0] if lanes else None
            )
            if load:
                loads.append(load)
        
        if extracted_data.get('rate'):
            rate = self._create_rate_from_extracted(
                extracted_data['rate'],
                loads[0] if loads else None
            )
            if rate:
                rates.append(rate)
                if loads:
                    loads[0].rate = rate
        
        return CarrierProfile(
            brokers=brokers,
            loads=loads,
            lanes=lanes,
            created_at=datetime.now()
        )
    
    def _extract_data_from_text(self, text: str) -> Dict[str, Any]:
        """Extract structured data from PDF text using regex patterns"""
        extracted = {
            'broker': {},
            'load': {},
            'lane': {},
            'rate': {}
        }
        
        # Extract broker information
        # Company name patterns
        company_patterns = [
            r'(?:Broker|Carrier|Company)[:\s]+([A-Z][A-Za-z\s&,\.]+)',
            r'([A-Z][A-Za-z\s&,\.]+)\s+(?:LLC|Inc|Corp|Ltd)',
        ]
        for pattern in company_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted['broker']['company_name'] = match.group(1).strip()
                break
        
        # MC number
        mc_match = re.search(r'MC[#:\s]*(\d+)', text, re.IGNORECASE)
        if mc_match:
            extracted['broker']['mc_id'] = mc_match.group(1)
        
        # Phone number
        phone_patterns = [
            r'Phone[:\s]+([\d\s\-\(\)]+)',
            r'(\d{3}[-\.\s]?\d{3}[-\.\s]?\d{4})',
        ]
        for pattern in phone_patterns:
            match = re.search(pattern, text)
            if match:
                extracted['broker']['phone'] = match.group(1).strip()
                break
        
        # Email
        email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', text)
        if email_match:
            extracted['broker']['email'] = email_match.group(1)
        
        # Load ID
        load_id_patterns = [
            r'Load[#:\s]+([A-Z0-9\-]+)',
            r'Booking[#:\s]+([A-Z0-9\-]+)',
            r'Pro[#:\s]+([A-Z0-9\-]+)',
        ]
        for pattern in load_id_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted['load']['load_id'] = match.group(1).strip()
                break
        
        # Origin and Destination
        origin_patterns = [
            r'Origin[:\s]+(.+?)(?:\n|Destination|$)',
            r'Pickup[:\s]+(.+?)(?:\n|Delivery|$)',
            r'From[:\s]+(.+?)(?:\n|To|$)',
        ]
        for pattern in origin_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                origin = match.group(1).strip()
                extracted['lane']['origin'] = origin
                break
        
        destination_patterns = [
            r'Destination[:\s]+(.+?)(?:\n|$)',
            r'Delivery[:\s]+(.+?)(?:\n|$)',
            r'To[:\s]+(.+?)(?:\n|$)',
        ]
        for pattern in destination_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                destination = match.group(1).strip()
                extracted['lane']['destination'] = destination
                break
        
        # Rate
        rate_patterns = [
            r'Rate[:\s]+\$?([\d,]+\.?\d*)',
            r'Amount[:\s]+\$?([\d,]+\.?\d*)',
            r'\$([\d,]+\.?\d*)\s*(?:Total|Rate|Amount)',
        ]
        for pattern in rate_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                rate_str = match.group(1).replace(',', '')
                try:
                    extracted['rate']['amount'] = float(rate_str)
                except ValueError:
                    pass
                break
        
        # Dates
        date_patterns = [
            r'Pickup[:\s]+Date[:\s]+(.+?)(?:\n|$)',
            r'Delivery[:\s]+Date[:\s]+(.+?)(?:\n|$)',
            r'Date[:\s]+(.+?)(?:\n|$)',
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1).strip()
                if 'pickup' in pattern.lower() or 'Pickup' in pattern:
                    extracted['load']['pickup_date'] = date_str
                elif 'delivery' in pattern.lower() or 'Delivery' in pattern:
                    extracted['load']['delivery_date'] = date_str
                else:
                    extracted['load']['booking_date'] = date_str
        
        return extracted
    
    def _create_broker_from_extracted(self, data: Dict[str, Any]) -> Optional[Broker]:
        """Create Broker from extracted PDF data"""
        if not data:
            return None
        
        broker = Broker(source=DataSource.PDF, created_at=datetime.now())
        broker.company_name = data.get('company_name')
        broker.mc_id = data.get('mc_id')
        broker.broker_phone_number = data.get('phone')
        broker.broker_email = data.get('email')
        
        return broker if broker.company_name or broker.mc_id else None
    
    def _create_lane_from_extracted(self, data: Dict[str, Any]) -> Optional[Lane]:
        """Create Lane from extracted PDF data"""
        origin = data.get('origin')
        destination = data.get('destination')
        
        if not origin and not destination:
            return None
        
        lane = Lane(source=DataSource.PDF, created_at=datetime.now())
        lane.origin_city_state = origin
        lane.destination_city_state = destination
        
        if origin:
            lane.origin = Address(raw_address=origin)
        if destination:
            lane.destination = Address(raw_address=destination)
        
        return lane
    
    def _create_load_from_extracted(self, data: Dict[str, Any], 
                                   broker: Optional[Broker],
                                   lane: Optional[Lane]) -> Optional[Load]:
        """Create Load from extracted PDF data"""
        load_id = data.get('load_id')
        if not load_id:
            return None
        
        load = Load(
            load_id=load_id,
            broker=broker,
            broker_id=broker.mc_id if broker else None,
            lane=lane,
            source=DataSource.PDF,
            created_at=datetime.now()
        )
        
        # Parse dates
        if data.get('pickup_date'):
            load.pickup_date = self._parse_date(data['pickup_date'])
        if data.get('delivery_date'):
            load.delivery_date = self._parse_date(data['delivery_date'])
        if data.get('booking_date'):
            load.booking_date = self._parse_date(data['booking_date'])
        
        load.status = 'booked'
        
        return load
    
    def _create_rate_from_extracted(self, data: Dict[str, Any],
                                   load: Optional[Load]) -> Optional[Rate]:
        """Create Rate from extracted PDF data"""
        amount = data.get('amount')
        if not amount:
            return None
        
        rate = Rate(
            load_id=load.load_id if load else None,
            rate_amount=float(amount),
            rate_type='flat',
            source=DataSource.PDF,
            created_at=datetime.now()
        )
        
        return rate
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string into datetime object"""
        from parser.utils import parse_date
        return parse_date(date_str)

