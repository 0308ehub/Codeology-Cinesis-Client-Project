import csv
import re
from typing import List, Optional

class Broker:
    """
    Represents a broker with all their information.
    """
    def __init__(self):
        self.broker_name: Optional[str] = None          # POC name
        self.company_name: Optional[str] = None         # Company name
        self.mc_id: Optional[str] = None                # MC number
        self.broker_phone_number: Optional[str] = None  # POC's phone
        self.broker_email: Optional[str] = None         # POC's email
        self.company_address: Optional[str] = None      # Office address
        self.date_of_contract: Optional[str] = None     # Contract date
        self.load_id: Optional[str] = None              # Load ID(s)
        self.state: Optional[str] = None                # State abbreviation
        self.source_destination: Optional[str] = None   # Trip details
        self.notes: Optional[str] = None                # Notes about broker
        self.load_board: Optional[str] = None           # Load board info
    
    def __repr__(self):
        return f"Broker(name={self.broker_name}, company={self.company_name}, mc={self.mc_id})"
    
    def to_dict(self):
        """Convert broker to dictionary for easy viewing."""
        return {
            'broker_name': self.broker_name,
            'company_name': self.company_name,
            'mc_id': self.mc_id,
            'broker_phone_number': self.broker_phone_number,
            'broker_email': self.broker_email,
            'company_address': self.company_address,
            'date_of_contract': self.date_of_contract,
            'load_id': self.load_id,
            'state': self.state,
            'source_destination': self.source_destination,
            'notes': self.notes,
            'load_board': self.load_board
        }


class BrokerDataParser:
    """
    Parser for broker CSV data with the following columns:
    Name, Broker, MC#, Phone Number, Email, Address, Date, Load #, State, Trip, Notes, Load Board
    """
    
    def __init__(self):
        self.brokers: List[Broker] = []
    
    def parse_file(self, file_path: str) -> List[Broker]:
        """
        Parse a CSV file containing broker data.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            List of Broker objects
        """
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            return self.parse_content(content)
    
    def parse_content(self, content: str) -> List[Broker]:
        """
        Parse CSV content string into Broker objects.
        
        Args:
            content: Raw CSV content as string
            
        Returns:
            List of Broker objects
        """
        self.brokers = []
        
        # Use csv.reader to properly handle CSV parsing
        lines = content.strip().split('\n')
        reader = csv.reader(lines)
        
        # Read all rows
        rows = list(reader)
        
        if not rows:
            return self.brokers
        
        # First row should be headers
        headers = rows[0]
        
        print(f"Found {len(headers)} columns: {headers}")
        print(f"Processing {len(rows) - 1} data rows...\n")
        
        # Process each data row
        for row_num, row in enumerate(rows[1:], start=2):
            if not row or not any(row):  # Skip empty rows
                continue
            
            broker = self._parse_row(row, headers)
            if broker:
                self.brokers.append(broker)
                print(f"Row {row_num}: Parsed {broker}")
        
        return self.brokers
    
    def _parse_row(self, row: List[str], headers: List[str]) -> Optional[Broker]:
        """
        Parse a single CSV row into a Broker object.
        
        Args:
            row: List of cell values from CSV
            headers: List of column headers
            
        Returns:
            Broker object or None if parsing fails
        """
        broker = Broker()
        
        # Map CSV columns to Broker attributes
        # Expected columns: Name, Broker, MC#, Phone Number, Email, Address, Date, Load #, State, Trip, Notes, Load Board
        
        column_mapping = {
            'Name': 'broker_name',
            'Broker': 'company_name',
            'MC#': 'mc_id',
            'Phone Number': 'broker_phone_number',
            'Email': 'broker_email',
            'Address': 'company_address',
            'Date': 'date_of_contract',
            'Load #': 'load_id',
            'State': 'state',
            'Trip': 'source_destination',
            'Notes': 'notes',
            'Load Board': 'load_board'
        }
        
        # Iterate through each column and extract data
        for i, header in enumerate(headers):
            if i >= len(row):
                break
            
            value = row[i].strip() if row[i] else None
            
            # Handle empty values
            if value in ['N/L', 'N/A', '']:
                value = None
            
            # Find matching attribute name
            attr_name = column_mapping.get(header)
            if attr_name:
                setattr(broker, attr_name, value)
        
        # Additional parsing and cleaning
        self._clean_broker_data(broker)
        
        return broker
    
    def _clean_broker_data(self, broker: Broker):
        """
        Clean and normalize broker data.
        
        Args:
            broker: Broker object to clean
        """
        # Remove ** markers from company names (used for emphasis)
        if broker.company_name:
            broker.company_name = broker.company_name.replace('**', '').strip()
        
        if broker.broker_name:
            broker.broker_name = broker.broker_name.replace('**', '').strip()
        
        # Extract MC number (remove non-numeric characters)
        if broker.mc_id:
            broker.mc_id = re.sub(r'[^\d]', '', broker.mc_id)
        
        # Clean phone numbers (keep digits and common separators)
        if broker.broker_phone_number:
            # Keep the original format but clean up
            broker.broker_phone_number = broker.broker_phone_number.strip()
        
        # Extract state abbreviations (2-letter codes)
        if broker.state:
            # Find 2-letter state codes
            state_match = re.findall(r'\b[A-Z]{2}\b', broker.state)
            if state_match:
                broker.state = state_match[0]
        
        # Parse multiple load IDs if present
        if broker.load_id:
            # Load IDs might be space or comma separated
            load_ids = re.findall(r'L?\d+', broker.load_id)
            broker.load_id = ', '.join(load_ids) if load_ids else broker.load_id
    
    def get_brokers(self) -> List[Broker]:
        """Return list of parsed brokers."""
        return self.brokers
    
    def print_summary(self):
        """Print a summary of parsed brokers."""
        print(f"\n{'='*80}")
        print(f"PARSED {len(self.brokers)} BROKERS")
        print(f"{'='*80}\n")
        
        for i, broker in enumerate(self.brokers, 1):
            print(f"{i}. {broker.broker_name}")
            print(f"   Company Name: {broker.company_name}")
            print(f"   MC#: {broker.mc_id}")
            print(f"   Email: {broker.broker_email}")
            print(f"   Phone: {broker.broker_phone_number}")
            print(f"   Address: {broker.company_address}")
            print(f"   State: {broker.state}")
            print(f"   Trip: {broker.source_destination}")
            print(f"   Load IDs: {broker.load_id}")
            print(f"   Date: {broker.date_of_contract}")
            print(f"   Notes: {broker.notes}")
            print(f"   Load Board: {broker.load_board}")
            print()


# EXAMPLE USAGE
if __name__ == "__main__":
    

    # Create parser
    parser = BrokerDataParser()
    
    # Parse the content
    # brokers = parser.parse_content(sample_csv)
    
    
    # # To use with a file:
    brokers = parser.parse_file('brokers.csv')
    parser.print_summary()