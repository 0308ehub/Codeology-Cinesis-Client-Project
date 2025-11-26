"""
Database models and integration using SQLAlchemy.
Supports both SQLite (development) and PostgreSQL (production).
"""
from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from typing import Optional
import os
from enum import Enum

from schema import DataSource, EnrichmentSource

Base = declarative_base()


class BrokerModel(Base):
    """Database model for brokers"""
    __tablename__ = 'brokers'
    
    broker_id = Column(String, primary_key=True)
    broker_name = Column(String)
    company_name = Column(String)
    mc_id = Column(String, index=True)
    broker_phone_number = Column(String)
    broker_email = Column(String)
    company_address = Column(Text)  # JSON string
    date_of_contract = Column(DateTime)
    load_board = Column(String)
    notes = Column(Text)
    source = Column(SQLEnum(DataSource))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    loads = relationship("LoadModel", back_populates="broker")


class LaneModel(Base):
    """Database model for lanes"""
    __tablename__ = 'lanes'
    
    lane_id = Column(String, primary_key=True)
    origin_city_state = Column(String, index=True)
    destination_city_state = Column(String, index=True)
    origin_address = Column(Text)  # JSON string
    destination_address = Column(Text)  # JSON string
    distance_miles = Column(Float)
    estimated_duration_hours = Column(Float)
    source = Column(SQLEnum(DataSource))
    created_at = Column(DateTime, default=datetime.now)
    
    loads = relationship("LoadModel", back_populates="lane")
    enriched_data = relationship("EnrichedDataModel", back_populates="lane")


class LoadModel(Base):
    """Database model for loads"""
    __tablename__ = 'loads'
    
    load_id = Column(String, primary_key=True)
    broker_id = Column(String, ForeignKey('brokers.broker_id'))
    lane_id = Column(String, ForeignKey('lanes.lane_id'))
    
    pickup_date = Column(DateTime)
    delivery_date = Column(DateTime)
    equipment_type = Column(String)
    weight = Column(Float)
    pallets = Column(Integer)
    pieces = Column(Integer)
    
    status = Column(String)
    booking_date = Column(DateTime)
    
    notes = Column(Text)
    load_board = Column(String)
    
    source = Column(SQLEnum(DataSource))
    raw_data = Column(Text)  # JSON string
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    broker = relationship("BrokerModel", back_populates="loads")
    lane = relationship("LaneModel", back_populates="loads")
    rate = relationship("RateModel", back_populates="load", uselist=False)


class RateModel(Base):
    """Database model for rates"""
    __tablename__ = 'rates'
    
    rate_id = Column(String, primary_key=True)
    load_id = Column(String, ForeignKey('loads.load_id'), unique=True)
    
    rate_amount = Column(Float)
    rate_per_mile = Column(Float)
    currency = Column(String, default='USD')
    rate_type = Column(String)
    
    source = Column(SQLEnum(DataSource))
    enrichment_source = Column(SQLEnum(EnrichmentSource))
    created_at = Column(DateTime, default=datetime.now)
    
    load = relationship("LoadModel", back_populates="rate")


class EnrichedDataModel(Base):
    """Database model for enriched market data"""
    __tablename__ = 'enriched_data'
    
    enriched_id = Column(String, primary_key=True)
    lane_id = Column(String, ForeignKey('lanes.lane_id'))
    
    origin_city_state = Column(String, index=True)
    destination_city_state = Column(String, index=True)
    
    average_rate = Column(Float)
    average_rate_per_mile = Column(Float)
    market_range_low = Column(Float)
    market_range_high = Column(Float)
    
    average_distance = Column(Float)
    average_transit_time_hours = Column(Float)
    volume_index = Column(Float)
    
    enrichment_source = Column(SQLEnum(EnrichmentSource))
    confidence_score = Column(Float)
    last_updated = Column(DateTime, default=datetime.now)
    
    lane = relationship("LaneModel", back_populates="enriched_data")


class CarrierProfileModel(Base):
    """Database model for carrier profiles"""
    __tablename__ = 'carrier_profiles'
    
    carrier_id = Column(String, primary_key=True)
    carrier_name = Column(String)
    mc_number = Column(String, index=True)
    
    preferred_lanes = Column(Text)  # JSON array
    preferred_equipment = Column(Text)  # JSON array
    preferred_brokers = Column(Text)  # JSON array
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class Database:
    """Database connection and operations"""
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize database connection.
        
        Args:
            database_url: Database URL (defaults to SQLite if not provided)
        """
        if database_url is None:
            # Default to SQLite for development
            database_url = os.getenv('DATABASE_URL', 'sqlite:///carrier_data.db')
        
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def save_carrier_profile(self, profile, carrier_id: str):
        """Save carrier profile to database"""
        session = self.get_session()
        try:
            # Save carrier profile
            carrier_model = CarrierProfileModel(
                carrier_id=carrier_id,
                carrier_name=profile.carrier_name,
                mc_number=profile.mc_number,
                preferred_lanes=str(profile.preferred_lanes),
                preferred_equipment=str(profile.preferred_equipment),
                preferred_brokers=str(profile.preferred_brokers)
            )
            session.merge(carrier_model)
            
            # Save brokers
            seen_broker_ids = set()
            for broker in profile.brokers:
                # Generate unique broker_id
                if broker.broker_id:
                    broker_id = broker.broker_id
                elif broker.mc_id:
                    broker_id = f"broker_{broker.mc_id}"
                elif broker.company_name:
                    # Use hash of company name to ensure uniqueness
                    broker_id = f"broker_{abs(hash(broker.company_name))}"
                else:
                    # Fallback: use hash of all available data
                    broker_data = f"{broker.broker_name}_{broker.broker_email}"
                    broker_id = f"broker_{abs(hash(broker_data))}"
                
                # Ensure uniqueness within this batch
                original_id = broker_id
                counter = 1
                while broker_id in seen_broker_ids:
                    broker_id = f"{original_id}_{counter}"
                    counter += 1
                seen_broker_ids.add(broker_id)
                
                broker_model = BrokerModel(
                    broker_id=broker_id,
                    broker_name=broker.broker_name,
                    company_name=broker.company_name,
                    mc_id=broker.mc_id,
                    broker_phone_number=broker.broker_phone_number,
                    broker_email=broker.broker_email,
                    company_address=str(broker.company_address.to_dict()) if broker.company_address else None,
                    date_of_contract=broker.date_of_contract,
                    load_board=broker.load_board,
                    notes=broker.notes,
                    source=broker.source
                )
                session.merge(broker_model)
            
            # Save lanes
            for lane in profile.lanes:
                lane_model = LaneModel(
                    lane_id=lane.lane_id or f"lane_{hash(f'{lane.origin_city_state}→{lane.destination_city_state}')}",
                    origin_city_state=lane.origin_city_state,
                    destination_city_state=lane.destination_city_state,
                    origin_address=str(lane.origin.to_dict()) if lane.origin else None,
                    destination_address=str(lane.destination.to_dict()) if lane.destination else None,
                    distance_miles=lane.distance_miles,
                    estimated_duration_hours=lane.estimated_duration_hours,
                    source=lane.source
                )
                session.merge(lane_model)
            
            # Save loads
            for load in profile.loads:
                load_model = LoadModel(
                    load_id=load.load_id,
                    broker_id=load.broker_id,
                    lane_id=load.lane.lane_id if load.lane else None,
                    pickup_date=load.pickup_date,
                    delivery_date=load.delivery_date,
                    equipment_type=load.equipment_type,
                    weight=load.weight,
                    pallets=load.pallets,
                    pieces=load.pieces,
                    status=load.status,
                    booking_date=load.booking_date,
                    notes=load.notes,
                    load_board=load.load_board,
                    source=load.source,
                    raw_data=str(load.raw_data) if load.raw_data else None
                )
                session.merge(load_model)
                
                # Save rate
                if load.rate:
                    rate_model = RateModel(
                        rate_id=load.rate.rate_id or f"rate_{load.load_id}",
                        load_id=load.load_id,
                        rate_amount=load.rate.rate_amount,
                        rate_per_mile=load.rate.rate_per_mile,
                        currency=load.rate.currency,
                        rate_type=load.rate.rate_type,
                        source=load.rate.source,
                        enrichment_source=load.rate.enrichment_source
                    )
                    session.merge(rate_model)
            
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_carrier_profile(self, carrier_id: str):
        """Retrieve carrier profile from database"""
        session = self.get_session()
        try:
            # This is a simplified version - full implementation would reconstruct
            # all related objects from the database
            carrier = session.query(CarrierProfileModel).filter_by(carrier_id=carrier_id).first()
            return carrier
        finally:
            session.close()

