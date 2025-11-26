"""
Freight market enrichment framework.
Fills gaps in carrier data with market benchmarks and estimates.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import random

from schema import (
    Lane, Rate, EnrichedData, EnrichmentSource
)
from database import Database, EnrichedDataModel


class EnrichmentEngine:
    """Engine for enriching carrier data with freight market information"""
    
    def __init__(self, database: Optional[Database] = None):
        self.database = database
        # In production, these would connect to real APIs
        self.dat_available = False
        self.truckstop_available = False
        self.fmcsa_available = False
    
    def enrich_lane(self, lane: Lane) -> EnrichedData:
        """
        Enrich a lane with market data.
        
        Args:
            lane: Lane to enrich
            
        Returns:
            EnrichedData with market benchmarks
        """
        # Check database for existing enriched data
        if self.database:
            existing = self._get_existing_enrichment(lane)
            if existing:
                return existing
        
        # Try to get data from external sources (in order of preference)
        enriched = None
        
        if self.dat_available:
            enriched = self._enrich_from_dat(lane)
        elif self.truckstop_available:
            enriched = self._enrich_from_truckstop(lane)
        elif self.fmcsa_available:
            enriched = self._enrich_from_fmcsa(lane)
        
        # Fallback to estimated data
        if not enriched:
            enriched = self._estimate_enrichment(lane)
        
        # Save to database
        if self.database and enriched:
            self._save_enrichment(enriched, lane)
        
        return enriched
    
    def enrich_rate(self, rate: Rate, lane: Optional[Lane] = None) -> Rate:
        """
        Enrich a rate with missing information.
        
        Args:
            rate: Rate to enrich
            lane: Optional lane for distance calculation
            
        Returns:
            Enriched Rate
        """
        # Calculate rate per mile if we have amount and distance
        if rate.rate_amount and lane and lane.distance_miles:
            if not rate.rate_per_mile:
                rate.rate_per_mile = rate.rate_amount / lane.distance_miles
                rate.enrichment_source = EnrichmentSource.ESTIMATED
        
        # Estimate rate amount if we have rate per mile and distance
        elif rate.rate_per_mile and lane and lane.distance_miles:
            if not rate.rate_amount:
                rate.rate_amount = rate.rate_per_mile * lane.distance_miles
                rate.enrichment_source = EnrichmentSource.ESTIMATED
        
        return rate
    
    def enrich_lanes(self, lanes: List[Lane]) -> List[EnrichedData]:
        """Enrich multiple lanes"""
        enriched_list = []
        for lane in lanes:
            enriched = self.enrich_lane(lane)
            if enriched:
                enriched_list.append(enriched)
        return enriched_list
    
    def _get_existing_enrichment(self, lane: Lane) -> Optional[EnrichedData]:
        """Get existing enriched data from database"""
        if not self.database or not lane.origin_city_state or not lane.destination_city_state:
            return None
        
        session = self.database.get_session()
        try:
            enriched_model = session.query(EnrichedDataModel).filter_by(
                origin_city_state=lane.origin_city_state,
                destination_city_state=lane.destination_city_state
            ).first()
            
            if enriched_model:
                return EnrichedData(
                    lane_id=enriched_model.lane_id,
                    origin_city_state=enriched_model.origin_city_state,
                    destination_city_state=enriched_model.destination_city_state,
                    average_rate=enriched_model.average_rate,
                    average_rate_per_mile=enriched_model.average_rate_per_mile,
                    market_range_low=enriched_model.market_range_low,
                    market_range_high=enriched_model.market_range_high,
                    average_distance=enriched_model.average_distance,
                    average_transit_time_hours=enriched_model.average_transit_time_hours,
                    volume_index=enriched_model.volume_index,
                    enrichment_source=enriched_model.enrichment_source,
                    confidence_score=enriched_model.confidence_score,
                    last_updated=enriched_model.last_updated
                )
        finally:
            session.close()
        
        return None
    
    def _enrich_from_dat(self, lane: Lane) -> Optional[EnrichedData]:
        """Enrich from DAT API (mock implementation)"""
        # In production, this would call DAT API
        # For now, return None to use estimation
        return None
    
    def _enrich_from_truckstop(self, lane: Lane) -> Optional[EnrichedData]:
        """Enrich from Truckstop API (mock implementation)"""
        # In production, this would call Truckstop API
        return None
    
    def _enrich_from_fmcsa(self, lane: Lane) -> Optional[EnrichedData]:
        """Enrich from FMCSA data (mock implementation)"""
        # In production, this would query FMCSA database
        return None
    
    def _estimate_enrichment(self, lane: Lane) -> EnrichedData:
        """
        Estimate enrichment data based on lane characteristics.
        This is a fallback when external sources are unavailable.
        """
        # Calculate distance if not available (rough estimate)
        distance = lane.distance_miles
        if not distance and lane.origin_city_state and lane.destination_city_state:
            # Very rough estimate: assume average 500 miles for inter-state
            # In production, use geocoding API
            distance = 500.0
        
        # Estimate rate per mile based on distance
        # Longer distances typically have lower rates per mile
        if distance:
            if distance < 100:
                base_rate_per_mile = 2.50
            elif distance < 500:
                base_rate_per_mile = 2.00
            else:
                base_rate_per_mile = 1.75
        else:
            base_rate_per_mile = 2.00
        
        # Add some variation
        rate_per_mile = base_rate_per_mile * (0.8 + random.random() * 0.4)
        rate_amount = rate_per_mile * distance if distance else None
        
        # Estimate transit time (rough: 50 mph average)
        transit_hours = distance / 50.0 if distance else None
        
        return EnrichedData(
            lane_id=lane.lane_id,
            origin_city_state=lane.origin_city_state,
            destination_city_state=lane.destination_city_state,
            average_rate=rate_amount,
            average_rate_per_mile=rate_per_mile,
            market_range_low=rate_amount * 0.85 if rate_amount else None,
            market_range_high=rate_amount * 1.15 if rate_amount else None,
            average_distance=distance,
            average_transit_time_hours=transit_hours,
            volume_index=0.5,  # Neutral volume
            enrichment_source=EnrichmentSource.ESTIMATED,
            confidence_score=0.6,  # Medium confidence for estimates
            last_updated=datetime.now()
        )
    
    def _save_enrichment(self, enriched: EnrichedData, lane: Lane):
        """Save enriched data to database"""
        if not self.database:
            return
        
        session = self.database.get_session()
        try:
            enriched_model = EnrichedDataModel(
                enriched_id=f"enriched_{lane.lane_id or hash(f'{lane.origin_city_state}→{lane.destination_city_state}')}",
                lane_id=lane.lane_id,
                origin_city_state=enriched.origin_city_state,
                destination_city_state=enriched.destination_city_state,
                average_rate=enriched.average_rate,
                average_rate_per_mile=enriched.average_rate_per_mile,
                market_range_low=enriched.market_range_low,
                market_range_high=enriched.market_range_high,
                average_distance=enriched.average_distance,
                average_transit_time_hours=enriched.average_transit_time_hours,
                volume_index=enriched.volume_index,
                enrichment_source=enriched.enrichment_source,
                confidence_score=enriched.confidence_score,
                last_updated=enriched.last_updated
            )
            session.merge(enriched_model)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Warning: Could not save enrichment: {e}")
        finally:
            session.close()
    
    def fill_missing_rates(self, loads: List, lanes: List[Lane]) -> List:
        """Fill missing rates using enriched data"""
        # Create lane lookup
        lane_lookup = {}
        for lane in lanes:
            key = f"{lane.origin_city_state}→{lane.destination_city_state}"
            lane_lookup[key] = lane
        
        for load in loads:
            if not load.rate or not load.rate.rate_amount:
                # Try to find lane
                if load.lane:
                    key = f"{load.lane.origin_city_state}→{load.lane.destination_city_state}"
                    lane = lane_lookup.get(key, load.lane)
                    
                    # Enrich lane
                    enriched = self.enrich_lane(lane)
                    
                    if enriched and enriched.average_rate:
                        # Create rate from enriched data
                        if not load.rate:
                            from schema import Rate, DataSource
                            load.rate = Rate(
                                load_id=load.load_id,
                                source=DataSource.ENRICHED,
                                enrichment_source=enriched.enrichment_source
                            )
                        
                        load.rate.rate_amount = enriched.average_rate
                        load.rate.rate_per_mile = enriched.average_rate_per_mile
                        load.rate.rate_type = 'flat'
        
        return loads

