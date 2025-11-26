"""
Basic tests for parsers
"""
import pytest
import os
from pathlib import Path

from parser.unified_parser import UnifiedParser
from parser.csv_parser import CSVParser
from parser.email_parser import EmailParser
from normalization import DataNormalizer


def test_csv_parser():
    """Test CSV parsing"""
    parser = CSVParser()
    csv_file = Path(__file__).parent.parent / 'parser' / 'brokers.csv'
    
    if csv_file.exists():
        profile = parser.parse_file(str(csv_file))
        assert len(profile.brokers) > 0
        assert profile.brokers[0].company_name is not None


def test_email_parser():
    """Test email parsing"""
    parser = EmailParser()
    
    sample_email = """
    Subject: Booking Confirmation - Load #12345
    
    Hello,
    
    This is a booking confirmation for your load.
    
    Broker: ABC Logistics LLC
    MC#: 123456
    Load #: 12345
    
    Origin: Miami, FL
    Destination: Tampa, FL
    
    Pickup Date: 10/28/2024
    Delivery Date: 10/29/2024
    
    Rate: $1,500.00
    Equipment: Dry Van
    
    Thank you!
    """
    
    profile = parser.parse_email_text(sample_email, "Booking Confirmation")
    
    assert len(profile.brokers) > 0
    assert len(profile.loads) > 0
    assert len(profile.lanes) > 0


def test_normalization():
    """Test data normalization"""
    from schema import CarrierProfile, Broker
    
    # Create test profile with duplicates
    profile = CarrierProfile()
    profile.brokers = [
        Broker(mc_id="123456", company_name="ABC Logistics"),
        Broker(mc_id="123456", company_name="ABC Logistics LLC"),  # Duplicate
        Broker(mc_id="789012", company_name="XYZ Transport"),
    ]
    
    normalizer = DataNormalizer()
    normalized = normalizer.normalize_profile(profile)
    
    # Should have 2 unique brokers
    assert len(normalized.brokers) == 2


def test_unified_parser():
    """Test unified parser"""
    parser = UnifiedParser()
    csv_file = Path(__file__).parent.parent / 'parser' / 'brokers.csv'
    
    if csv_file.exists():
        profile = parser.parse_file(str(csv_file))
        assert profile is not None
        assert len(profile.brokers) > 0

