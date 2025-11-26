"""
Email parser for booking confirmations.
Extracts structured data from email text using regex and NLP.
"""
import re
from typing import Optional, Dict, Any
from datetime import datetime

from schema import (
    Broker, Load, Lane, Rate, Address, CarrierProfile,
    DataSource
)
from parser.csv_parser import CSVParser


class EmailParser(CSVParser):
    """Parser for email booking confirmations"""
    
    def parse_email_text(self, email_text: str, subject: Optional[str] = None) -> CarrierProfile:
        """
        Parse email text to extract booking information.
        
        Args:
            email_text: Email body text
            subject: Optional email subject
            
        Returns:
            CarrierProfile with parsed data
        """
        brokers = []
        loads = []
        lanes = []
        rates = []
        
        # Combine subject and body
        full_text = f"{subject or ''}\n{email_text}"
        
        # Extract structured data
        extracted = self._extract_from_email(full_text)
        
        # Create broker
        if extracted.get('broker'):
            broker = self._create_broker_from_email(extracted['broker'])
            if broker:
                brokers.append(broker)
        
        # Create lane
        if extracted.get('lane'):
            lane = self._create_lane_from_email(extracted['lane'])
            if lane:
                lanes.append(lane)
        
        # Create load
        if extracted.get('load'):
            load = self._create_load_from_email(
                extracted['load'],
                brokers[0] if brokers else None,
                lanes[0] if lanes else None
            )
            if load:
                loads.append(load)
        
        # Create rate
        if extracted.get('rate'):
            rate = self._create_rate_from_email(
                extracted['rate'],
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
    
    def _extract_from_email(self, text: str) -> Dict[str, Any]:
        """Extract structured data from email text"""
        extracted = {
            'broker': {},
            'load': {},
            'lane': {},
            'rate': {}
        }
        
        # Extract broker company name
        company_patterns = [
            r'(?:from|broker|carrier)[:\s]+([A-Z][A-Za-z\s&,\.]+(?:LLC|Inc|Corp|Ltd)?)',
            r'([A-Z][A-Za-z\s&,\.]+(?:LLC|Inc|Corp|Ltd))',
        ]
        for pattern in company_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted['broker']['company_name'] = match.group(1).strip()
                break
        
        # Extract MC number
        mc_patterns = [
            r'MC[#:\s]*(\d+)',
            r'MC\s*Number[:\s]*(\d+)',
            r'Motor\s*Carrier[#:\s]*(\d+)',
        ]
        for pattern in mc_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted['broker']['mc_id'] = match.group(1)
                break
        
        # Extract load ID
        load_id_patterns = [
            r'Load[#:\s]+([A-Z0-9\-]+)',
            r'Booking[#:\s]+([A-Z0-9\-]+)',
            r'Pro[#:\s]+([A-Z0-9\-]+)',
            r'Reference[#:\s]+([A-Z0-9\-]+)',
            r'Order[#:\s]+([A-Z0-9\-]+)',
        ]
        for pattern in load_id_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted['load']['load_id'] = match.group(1).strip()
                break
        
        # Extract origin
        origin_patterns = [
            r'Origin[:\s]+(.+?)(?:\n|Destination|Delivery|To|$)',
            r'Pickup[:\s]+(.+?)(?:\n|Delivery|To|$)',
            r'From[:\s]+(.+?)(?:\n|To|Destination|$)',
            r'Pickup\s*Location[:\s]+(.+?)(?:\n|$)',
        ]
        for pattern in origin_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                origin = match.group(1).strip()
                # Clean up common suffixes
                origin = re.sub(r'\s*(City|State|Zip).*$', '', origin, flags=re.IGNORECASE)
                extracted['lane']['origin'] = origin
                break
        
        # Extract destination
        destination_patterns = [
            r'Destination[:\s]+(.+?)(?:\n|$)',
            r'Delivery[:\s]+(.+?)(?:\n|$)',
            r'To[:\s]+(.+?)(?:\n|Origin|From|$)',
            r'Delivery\s*Location[:\s]+(.+?)(?:\n|$)',
        ]
        for pattern in destination_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                destination = match.group(1).strip()
                destination = re.sub(r'\s*(City|State|Zip).*$', '', destination, flags=re.IGNORECASE)
                extracted['lane']['destination'] = destination
                break
        
        # Extract rate
        rate_patterns = [
            r'Rate[:\s]+\$?([\d,]+\.?\d*)',
            r'Amount[:\s]+\$?([\d,]+\.?\d*)',
            r'Total[:\s]+\$?([\d,]+\.?\d*)',
            r'\$([\d,]+\.?\d*)\s*(?:Total|Rate|Amount|Payment)',
            r'Payment[:\s]+\$?([\d,]+\.?\d*)',
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
        
        # Extract dates
        date_patterns = [
            r'Pickup\s*Date[:\s]+(.+?)(?:\n|$)',
            r'Delivery\s*Date[:\s]+(.+?)(?:\n|$)',
            r'Booking\s*Date[:\s]+(.+?)(?:\n|$)',
            r'Date[:\s]+(.+?)(?:\n|$)',
        ]
        for pattern in date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                date_str = match.group(1).strip()
                if 'pickup' in match.group(0).lower():
                    extracted['load']['pickup_date'] = date_str
                elif 'delivery' in match.group(0).lower():
                    extracted['load']['delivery_date'] = date_str
                elif 'booking' in match.group(0).lower():
                    extracted['load']['booking_date'] = date_str
                else:
                    if 'pickup_date' not in extracted['load']:
                        extracted['load']['pickup_date'] = date_str
        
        # Extract equipment type
        equipment_patterns = [
            r'Equipment[:\s]+(.+?)(?:\n|$)',
            r'Trailer\s*Type[:\s]+(.+?)(?:\n|$)',
            r'Type[:\s]+(.+?)(?:\n|$)',
        ]
        for pattern in equipment_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                equipment = match.group(1).strip()
                # Normalize common equipment types
                equipment = equipment.lower()
                if 'dry' in equipment or 'van' in equipment:
                    extracted['load']['equipment_type'] = 'Dry Van'
                elif 'reefer' in equipment or 'refrigerated' in equipment:
                    extracted['load']['equipment_type'] = 'Refrigerated'
                elif 'flatbed' in equipment or 'flat' in equipment:
                    extracted['load']['equipment_type'] = 'Flatbed'
                else:
                    extracted['load']['equipment_type'] = equipment.title()
                break
        
        return extracted
    
    def _create_broker_from_email(self, data: Dict[str, Any]) -> Optional[Broker]:
        """Create Broker from email data"""
        if not data:
            return None
        
        broker = Broker(source=DataSource.EMAIL, created_at=datetime.now())
        broker.company_name = data.get('company_name')
        broker.mc_id = data.get('mc_id')
        
        return broker if broker.company_name or broker.mc_id else None
    
    def _create_lane_from_email(self, data: Dict[str, Any]) -> Optional[Lane]:
        """Create Lane from email data"""
        origin = data.get('origin')
        destination = data.get('destination')
        
        if not origin and not destination:
            return None
        
        lane = Lane(source=DataSource.EMAIL, created_at=datetime.now())
        lane.origin_city_state = origin
        lane.destination_city_state = destination
        
        if origin:
            lane.origin = Address(raw_address=origin)
        if destination:
            lane.destination = Address(raw_address=destination)
        
        return lane
    
    def _create_load_from_email(self, data: Dict[str, Any],
                               broker: Optional[Broker],
                               lane: Optional[Lane]) -> Optional[Load]:
        """Create Load from email data"""
        load_id = data.get('load_id')
        if not load_id:
            return None
        
        load = Load(
            load_id=load_id,
            broker=broker,
            broker_id=broker.mc_id if broker else None,
            lane=lane,
            source=DataSource.EMAIL,
            created_at=datetime.now()
        )
        
        # Parse dates
        if data.get('pickup_date'):
            load.pickup_date = self._parse_date(data['pickup_date'])
        if data.get('delivery_date'):
            load.delivery_date = self._parse_date(data['delivery_date'])
        if data.get('booking_date'):
            load.booking_date = self._parse_date(data['booking_date'])
        
        load.equipment_type = data.get('equipment_type')
        load.status = 'booked'
        
        return load
    
    def _create_rate_from_email(self, data: Dict[str, Any],
                                load: Optional[Load]) -> Optional[Rate]:
        """Create Rate from email data"""
        amount = data.get('amount')
        if not amount:
            return None
        
        rate = Rate(
            load_id=load.load_id if load else None,
            rate_amount=float(amount),
            rate_type='flat',
            source=DataSource.EMAIL,
            created_at=datetime.now()
        )
        
        return rate
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string into datetime object"""
        from parser.utils import parse_date
        return parse_date(date_str)

