"""
Schema definitions for carrier data processing system.
Defines data models for brokers, loads, lanes, rates, and addresses.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum


class DataSource(Enum):
    """Source of the data"""
    CSV = "csv"
    EXCEL = "excel"
    PDF = "pdf"
    EMAIL = "email"
    MANUAL = "manual"
    ENRICHED = "enriched"  # Data from freight market enrichment


class EnrichmentSource(Enum):
    """Source of enriched data"""
    DAT = "dat"
    TRUCKSTOP = "truckstop"
    FMCSA = "fmcsa"
    DOE_INDEX = "doe_index"
    INTERNAL = "internal"
    ESTIMATED = "estimated"


@dataclass
class Address:
    """Normalized address information"""
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: str = "USA"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    raw_address: Optional[str] = None  # Original unparsed address
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'street': self.street,
            'city': self.city,
            'state': self.state,
            'zip_code': self.zip_code,
            'country': self.country,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'raw_address': self.raw_address
        }


@dataclass
class Broker:
    """Broker information"""
    broker_id: Optional[str] = None
    broker_name: Optional[str] = None  # POC name
    company_name: Optional[str] = None
    mc_id: Optional[str] = None
    broker_phone_number: Optional[str] = None
    broker_email: Optional[str] = None
    company_address: Optional[Address] = None
    date_of_contract: Optional[datetime] = None
    load_board: Optional[str] = None
    notes: Optional[str] = None
    source: DataSource = DataSource.MANUAL
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'broker_id': self.broker_id,
            'broker_name': self.broker_name,
            'company_name': self.company_name,
            'mc_id': self.mc_id,
            'broker_phone_number': self.broker_phone_number,
            'broker_email': self.broker_email,
            'company_address': self.company_address.to_dict() if self.company_address else None,
            'date_of_contract': self.date_of_contract.isoformat() if self.date_of_contract else None,
            'load_board': self.load_board,
            'notes': self.notes,
            'source': self.source.value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class Lane:
    """Shipping lane definition"""
    lane_id: Optional[str] = None
    origin: Optional[Address] = None
    destination: Optional[Address] = None
    origin_city_state: Optional[str] = None  # e.g., "Miami, FL"
    destination_city_state: Optional[str] = None  # e.g., "Tampa, FL"
    distance_miles: Optional[float] = None
    estimated_duration_hours: Optional[float] = None
    source: DataSource = DataSource.MANUAL
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'lane_id': self.lane_id,
            'origin': self.origin.to_dict() if self.origin else None,
            'destination': self.destination.to_dict() if self.destination else None,
            'origin_city_state': self.origin_city_state,
            'destination_city_state': self.destination_city_state,
            'distance_miles': self.distance_miles,
            'estimated_duration_hours': self.estimated_duration_hours,
            'source': self.source.value,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class Rate:
    """Rate information for a load"""
    rate_id: Optional[str] = None
    load_id: Optional[str] = None
    rate_amount: Optional[float] = None
    rate_per_mile: Optional[float] = None
    currency: str = "USD"
    rate_type: Optional[str] = None  # "flat", "per_mile", "per_hour"
    source: DataSource = DataSource.MANUAL
    enrichment_source: Optional[EnrichmentSource] = None
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'rate_id': self.rate_id,
            'load_id': self.load_id,
            'rate_amount': self.rate_amount,
            'rate_per_mile': self.rate_per_mile,
            'currency': self.currency,
            'rate_type': self.rate_type,
            'source': self.source.value,
            'enrichment_source': self.enrichment_source.value if self.enrichment_source else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class Load:
    """Load/booking information"""
    load_id: Optional[str] = None
    broker_id: Optional[str] = None
    broker: Optional[Broker] = None
    lane: Optional[Lane] = None
    rate: Optional[Rate] = None
    
    # Load details
    pickup_date: Optional[datetime] = None
    delivery_date: Optional[datetime] = None
    equipment_type: Optional[str] = None  # "Dry Van", "Refrigerated", "Flatbed", etc.
    weight: Optional[float] = None  # in pounds
    pallets: Optional[int] = None
    pieces: Optional[int] = None
    
    # Status
    status: Optional[str] = None  # "booked", "completed", "cancelled"
    booking_date: Optional[datetime] = None
    
    # Additional info
    notes: Optional[str] = None
    load_board: Optional[str] = None
    
    # Metadata
    source: DataSource = DataSource.MANUAL
    raw_data: Optional[Dict[str, Any]] = None  # Original parsed data
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'load_id': self.load_id,
            'broker_id': self.broker_id,
            'broker': self.broker.to_dict() if self.broker else None,
            'lane': self.lane.to_dict() if self.lane else None,
            'rate': self.rate.to_dict() if self.rate else None,
            'pickup_date': self.pickup_date.isoformat() if self.pickup_date else None,
            'delivery_date': self.delivery_date.isoformat() if self.delivery_date else None,
            'equipment_type': self.equipment_type,
            'weight': self.weight,
            'pallets': self.pallets,
            'pieces': self.pieces,
            'status': self.status,
            'booking_date': self.booking_date.isoformat() if self.booking_date else None,
            'notes': self.notes,
            'load_board': self.load_board,
            'source': self.source.value,
            'raw_data': self.raw_data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class CarrierProfile:
    """Complete carrier profile with all historical data"""
    carrier_id: Optional[str] = None
    carrier_name: Optional[str] = None
    mc_number: Optional[str] = None
    
    # Historical data
    brokers: List[Broker] = field(default_factory=list)
    loads: List[Load] = field(default_factory=list)
    lanes: List[Lane] = field(default_factory=list)
    
    # Preferences (for matching)
    preferred_lanes: List[str] = field(default_factory=list)  # City-state pairs
    preferred_equipment: List[str] = field(default_factory=list)
    preferred_brokers: List[str] = field(default_factory=list)  # MC IDs
    
    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'carrier_id': self.carrier_id,
            'carrier_name': self.carrier_name,
            'mc_number': self.mc_number,
            'brokers': [b.to_dict() for b in self.brokers],
            'loads': [l.to_dict() for l in self.loads],
            'lanes': [l.to_dict() for l in self.lanes],
            'preferred_lanes': self.preferred_lanes,
            'preferred_equipment': self.preferred_equipment,
            'preferred_brokers': self.preferred_brokers,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class EnrichedData:
    """Enriched data from freight market sources"""
    lane_id: Optional[str] = None
    origin_city_state: Optional[str] = None
    destination_city_state: Optional[str] = None
    
    # Market benchmarks
    average_rate: Optional[float] = None
    average_rate_per_mile: Optional[float] = None
    market_range_low: Optional[float] = None
    market_range_high: Optional[float] = None
    
    # Additional metrics
    average_distance: Optional[float] = None
    average_transit_time_hours: Optional[float] = None
    volume_index: Optional[float] = None  # Market volume indicator
    
    # Source information
    enrichment_source: EnrichmentSource = EnrichmentSource.ESTIMATED
    confidence_score: Optional[float] = None  # 0-1 confidence in the data
    last_updated: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'lane_id': self.lane_id,
            'origin_city_state': self.origin_city_state,
            'destination_city_state': self.destination_city_state,
            'average_rate': self.average_rate,
            'average_rate_per_mile': self.average_rate_per_mile,
            'market_range_low': self.market_range_low,
            'market_range_high': self.market_range_high,
            'average_distance': self.average_distance,
            'average_transit_time_hours': self.average_transit_time_hours,
            'volume_index': self.volume_index,
            'enrichment_source': self.enrichment_source.value,
            'confidence_score': self.confidence_score,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }

